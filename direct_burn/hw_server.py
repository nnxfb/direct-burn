# direct_burn/hw_server.py — hw_server 生命周期管理

import time
import socket

from .config import HW_SERVER_BAT, REMOTE_TEMP, VIVADO_BAT
from .ssh import SshSession


class HwServerSession:
    """hw_server 上下文管理器 — __exit__ 保证进程回收.

    Usage:
        with HwServerSession(ssh, ip, port, jtag) as hw:
            run_vivado_burn(...)
        # hw_server auto-killed here, even on exception
    """

    def __init__(self, ssh: SshSession, ip: str, port: int, jtag: str, timeout=30):
        self._ssh = ssh
        self._ip = ip
        self._port = port
        self._jtag = jtag
        self._timeout = timeout

    def __enter__(self):
        print(f'hw_server: {self._ip}:{self._port}, jtag={self._jtag}')

        out, _, _ = self._ssh.exec(
            f'powershell -ExecutionPolicy Bypass -File "{REMOTE_TEMP}/start_hw_server.ps1" '
            f'-Port "{self._port}" -Jtag "{self._jtag}" -TempDir "{REMOTE_TEMP}" -HwServerBat "{HW_SERVER_BAT}"'
        )
        print(out)

        bat_path = f'{REMOTE_TEMP}/{self._jtag}_run_hw.bat'
        print(f'[+] cmd.exe /c {bat_path}')
        self._ssh.exec_bg(f'cmd.exe /c {bat_path}')

        # 3. Wait for port
        if not self._wait_for_hw_server():
            self._kill()
            raise RuntimeError(f'hw_server 启动超时: {self._ip}:{self._port}')
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
        print(f'\n[+] 停止 hw_server: port={self._port}')
        out, _, _ = self._ssh.exec(f'powershell -ExecutionPolicy Bypass -File "{REMOTE_TEMP}/kill_port_admin.ps1" -Port {self._port}')
        if out.strip():
            print(f'{out.strip()}')

    def _wait_for_hw_server(self):
        """轮询等待 hw_server 端口就绪."""
        print(f'\n[+] 等待 hw_server {self._ip}:{self._port} (timeout={self._timeout}s)')
        start = time.time()
        while time.time() - start < self._timeout:
            try:
                with socket.create_connection((self._ip, self._port), timeout=2):
                    elapsed = int(time.time() - start)
                    print(f'[+] hw_server 已就绪 ({elapsed}s)')
                    return True
            except (socket.timeout, ConnectionRefusedError, OSError):
                elapsed = int(time.time() - start)
                print(f'[+] 等待中... ({elapsed}s)')
                time.sleep(2)
        print(f'[!] 超时 ({self._timeout}s)')
        return False


def run_vivado_burn(ssh: SshSession, ip: str, port: int, local_bitfile: str, jtag: str):
    """上传 bit 文件 + 上传 TCL 模板 + 远程执行 Vivado. 返回 True/False."""

    vivado_path = VIVADO_BAT

    print(f'\n[+] 上传 bit 文件并执行 Vivado 烧录...')

    ssh.exec(f'powershell -Command "New-Item -ItemType Directory -Path \'{REMOTE_TEMP}\' -Force | Out-Null"')

    remote_bit = f'{REMOTE_TEMP}/{jtag}_fpga.bit'
    remote_tcl = f'{REMOTE_TEMP}/auto_program.tcl'

    # 1. SFTP 上传 bit 文件
    print(f'[+] 上传 {local_bitfile:<20} -> {remote_bit}')
    ssh.upload(local_bitfile, remote_bit)

    # 2. 执行 Vivado
    cmd = (f'"{vivado_path}" -mode batch -source "{remote_tcl}" -tclargs "{ip}" "{port}" "{remote_bit}"')
    print(f'[+] {cmd}')
    _, err, exit_code = ssh.exec(cmd, timeout=120)

    if err.strip():
        print(f'[!] Vivado stderr:')
        print(f'[!] {err.strip()}')
    print(f'[+] 退出码: {exit_code}')

    return exit_code == 0
