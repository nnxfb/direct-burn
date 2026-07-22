# direct_burn/hw_server.py — hw_server 生命周期管理

import time
import socket

from .config import HW_SERVER_BAT, REMOTE_TEMP, REMOTE_TEMP_WIN
from .ssh import SshSession


class HwServerSession:
    """hw_server 上下文管理器 — __exit__ 保证进程回收.

    Usage:
        with HwServerSession(ssh, ip, port, jtag) as hw:
            run_vivado_burn(...)
        # hw_server auto-killed here, even on exception
    """

    def __init__(self, ssh: SshSession, ip, port, jtag, timeout=30):
        self._ssh = ssh
        self._ip = ip
        self._port = port
        self._jtag = jtag
        self._timeout = timeout

    def __enter__(self):
        print(f'\n[+] 启动 hw_server: port={self._port}, jtag={self._jtag}')

        # 1. PS1 does: kill old process on port + generate .bat file
        self._ssh.exec(
            f'powershell -ExecutionPolicy Bypass '
            f'-File "{REMOTE_TEMP}/start_hw_server.ps1" '
            f'-Port "{self._port}" -Jtag "{self._jtag}" '
            f'-TempDir "{REMOTE_TEMP}" -HwServerBat "{HW_SERVER_BAT}"'
        )
        time.sleep(1)

        log_path = f'{REMOTE_TEMP}/{self._jtag}_hw_server_exec_log.txt'
        out, _, _ = self._ssh.exec(
            f'powershell -Command "if (Test-Path \'{log_path}\') '
            f'{{ Get-Content \'{log_path}\' -Tail 5 }} else {{ Write-Host \'NO LOG\' }}"'
        )
        if out.strip() and 'NO LOG' not in out:
            for line in out.strip().splitlines():
                print(f'  [日志] {line.strip()}')

        # 2. Fire-and-forget: cmd.exe /c .bat  (channel stays open → hw_server survives)
        bat_path = f'{REMOTE_TEMP_WIN}\\{self._jtag}_run_hw.bat'
        print(f'  🔥 fire-and-forget: cmd.exe /c {bat_path}')
        self._ssh._ssh.exec_command(f'cmd.exe /c {bat_path}')

        # 3. Wait for port
        if not wait_for_hw_server(self._ip, self._port, self._timeout):
            self._kill()
            raise RuntimeError(
                f'hw_server 启动超时: {self._ip}:{self._port}'
            )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self._kill()
            print('[+] hw_server 已清理')
        except Exception as e:
            print(f'[!] 清理 hw_server 失败: {e}')
        return False

    def _kill(self):
        """Kill hw_server by port."""
        print(f'\n[*] 停止 hw_server: port={self._port}')
        out, _, _ = self._ssh.exec(
            f'powershell -ExecutionPolicy Bypass '
            f'-File "{REMOTE_TEMP}\\kill_port_admin.ps1" -Port {self._port}'
        )
        if out.strip():
            print(f'  {out.strip()}')


def wait_for_hw_server(ip, port, timeout=30):
    """轮询等待 hw_server 端口就绪."""
    print(f'\n[*] 等待 hw_server 就绪: {ip}:{port} (timeout={timeout}s)')
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((ip, port), timeout=2):
                elapsed = int(time.time() - start)
                print(f'[+] hw_server 已就绪 ({elapsed}s)')
                return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            elapsed = int(time.time() - start)
            print(f'  ⏳ 等待中... ({elapsed}s)')
            time.sleep(2)
    print(f'[!] 超时 ({timeout}s)')
    return False
