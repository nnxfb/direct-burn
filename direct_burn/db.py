# direct_burn/db.py — 数据库操作 (只读查询 + fpga_boards 互斥写)

import threading
import pymysql

from .config import get_db_default_config


def get_db_connection():
    _host, _port, _user, _password, _name = get_db_default_config()
    return pymysql.connect(
        host=_host,
        port=_port,
        user=_user,
        password=_password,
        database=_name,
        charset='utf8mb4',
        autocommit=True,
    )


def list_all_fpga():
    """列出全部 FPGA 设备."""
    conn = get_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT fpga_name, total_port, jtag_filter, vcom_name, com_name, IP, result, status, last_heartbeat
                FROM fpga_boards
                ORDER BY CAST(SUBSTRING(fpga_name, 5) AS UNSIGNED)
            """)
            rows = cursor.fetchall()
        print(rows[0])
        return rows
    finally:
        conn.close()


def list_available_fpga():
    """列出空闲 FPGA 设备."""
    conn = get_db_connection()
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


def query_fpga_by_name(fpga_name):
    """按名称查询 FPGA"""
    conn = get_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute('SELECT * FROM fpga_boards WHERE fpga_name = %s', (fpga_name,))
            row = cursor.fetchone()
        return row
    finally:
        conn.close()


def query_fpga_by_jtag(jtag_filter):
    """按 JTAG 查询 FPGA"""
    conn = get_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute('SELECT * FROM fpga_boards WHERE jtag_filter = %s', (jtag_filter,))
            row = cursor.fetchone()
        return row
    finally:
        conn.close()


class FpgaLock:
    """FPGA 板卡互斥锁

    Usage:
        with FpgaLock('FPGA11') as lock:
            # 烧录逻辑...
    """

    def __init__(self, fpga_name, heartbeat_interval=45):
        self.fpga_name = fpga_name
        self.heartbeat_interval = heartbeat_interval
        self._heartbeat_stop = None

    def acquire_fpga(self):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE fpga_boards SET status = 'in_use' WHERE fpga_name = %s", (self.fpga_name,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def release_fpga(self):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE fpga_boards SET status = 'available' WHERE fpga_name = %s", (self.fpga_name,))
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
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE fpga_boards SET last_heartbeat = NOW() WHERE fpga_name = %s", (self.fpga_name,))
            conn.commit()
        except Exception as e:
            print('[!] 心跳更新失败', e)
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
