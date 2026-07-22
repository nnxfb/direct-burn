# direct_burn/db.py — 数据库操作 (只读查询 + fpga_boards 互斥写)

import threading
import pymysql

from .config import get_db_default_config


def get_db_connection(host=None, port=None, user=None, password=None):
    _host, _port, _user, _password = get_db_default_config()
    return pymysql.connect(
        host=host or _host,
        port=port or _port,
        user=user or _user,
        password=password if password is not None else _password,
        database='port_manager',
        charset='utf8mb4',
        autocommit=True,
    )


def list_all_fpga(db_host, db_port=None, db_user=None, db_password=None):
    """列出全部 FPGA 设备."""
    conn = get_db_connection(host=db_host, port=db_port, user=db_user, password=db_password)
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT fpga_name, total_port, jtag_filter, vcom_name, com_name, IP, result, status, last_heartbeat
                FROM fpga_boards
                ORDER BY CAST(SUBSTRING(fpga_name, 5) AS UNSIGNED)
            """)
            rows = cursor.fetchall()
        return rows
    finally:
        conn.close()


def list_available_fpga(db_host, db_password=None):
    """列出空闲 FPGA 设备."""
    conn = get_db_connection(host=db_host, password=db_password)
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT fpga_name, total_port, jtag_filter, vcom_name, com_name, IP, result, status, last_heartbeat
                FROM fpga_boards
                WHERE status = 'available'
                ORDER BY CAST(SUBSTRING(fpga_name, 5) AS UNSIGNED)
            """)
            rows = cursor.fetchall()
        return rows
    finally:
        conn.close()


def query_fpga_by_name(db_host, fpga_name, db_password=None):
    """按名称查询 FPGA."""
    conn = get_db_connection(host=db_host, password=db_password)
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute('SELECT * FROM fpga_boards WHERE fpga_name = %s', (fpga_name,))
            row = cursor.fetchone()
        return row
    finally:
        conn.close()


def query_fpga_by_jtag(db_host, jtag_filter, db_password=None):
    """按 JTAG 查询 FPGA."""
    conn = get_db_connection(host=db_host, password=db_password)
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute('SELECT * FROM fpga_boards WHERE jtag_filter = %s', (jtag_filter,))
            row = cursor.fetchone()
        return row
    finally:
        conn.close()


class FpgaLock:
    """FPGA 板卡互斥锁 — 支持上下文管理器.

    Usage:
        with FpgaLock('FPGA11', db_host, db_pass) as lock:
            # 烧录逻辑...
    """

    def __init__(self, fpga_name, db_host, db_password=None, heartbeat_interval=45):
        self.fpga_name = fpga_name
        self.db_host = db_host
        self.db_password = db_password
        self.heartbeat_interval = heartbeat_interval
        self._heartbeat_stop = None

    def acquire_fpga(self):
        conn = get_db_connection(host=self.db_host, password=self.db_password)
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE fpga_boards SET status = 'in_use' WHERE fpga_name = %s",
                    (self.fpga_name,),
                )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def release_fpga(self):
        conn = get_db_connection(host=self.db_host, password=self.db_password)
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE fpga_boards SET status = 'available' WHERE fpga_name = %s",
                    (self.fpga_name,),
                )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def __enter__(self):
        if not self.acquire_fpga():
            raise RuntimeError(f'无法标记 {self.fpga_name} 为 in_use, 可能已被占用')
        print(f'[+] {self.fpga_name} 已占用 (status=in_use)')
        self._heartbeat_stop = self._start_heartbeat()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._heartbeat_stop:
            self._heartbeat_stop.set()
        if self.release_fpga():
            print(f'[+] {self.fpga_name} 已释放 (status=available)')
        else:
            print(f'[!] {self.fpga_name} 释放失败, 将在 3 分钟后被心跳超时自动回收')
        return False

    def _update_heartbeat(self):
        conn = get_db_connection(host=self.db_host, password=self.db_password)
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE fpga_boards SET last_heartbeat = NOW() WHERE fpga_name = %s",
                    (self.fpga_name,),
                )
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

    def _start_heartbeat(self):
        stop_event = threading.Event()

        def worker():
            print(f'[+] {self.fpga_name} 心跳线程已启动 ({self.heartbeat_interval}s 间隔)')
            while not stop_event.is_set():
                self._update_heartbeat()
                stop_event.wait(self.heartbeat_interval)
            print(f'[+] {self.fpga_name} 心跳线程已停止')

        t = threading.Thread(target=worker, daemon=True)
        t.start()
        return stop_event
