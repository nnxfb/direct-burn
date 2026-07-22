# direct_burn/ssh.py — SSH 会话封装 + PS1 脚本部署

import os

import paramiko

from .config import REMOTE_TEMP, _TEMPLATE_DIR, get_ssh_default_config


class SshSession:
    """SSH 会话封装 — 支持上下文管理器."""

    def __init__(self, host, port=None, username=None, password=None):
        _port, _user, _pass = get_ssh_default_config()
        self.host = host
        self.port = port or _port
        self.username = username or _user
        self.password = password or _pass
        self._ssh = None

    def connect(self):
        self._ssh = paramiko.SSHClient()
        self._ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._ssh.connect(
            hostname=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            timeout=15,
            look_for_keys=False,
            allow_agent=False,
        )
        print(f'[+] SSH 已连接: {self.username}@{self.host}:{self.port}')

    def exec(self, cmd, timeout=30):
        """执行命令, 返回 (stdout, stderr, exit_code)."""
        print('cmd >', cmd)
        stdin, stdout, stderr = self._ssh.exec_command(cmd, timeout=timeout)
        out = stdout.read().decode(errors='replace')
        err = stderr.read().decode(errors='replace')
        exit_code = stdout.channel.recv_exit_status()
        return out, err, exit_code

    def sftp_put(self, local_path, remote_path):
        sftp = self._ssh.open_sftp()
        sftp.put(local_path, remote_path)
        sftp.close()

    def close(self):
        if self._ssh:
            self._ssh.close()
        print(f'[+] SSH 连接已断开: {self.username}@{self.host}:{self.port}')

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.close()


def deploy_ps1_scripts(ssh: SshSession):
    """上传 template/*.ps1 到远程 REMOTE_TEMP."""
    # 确保远程目录存在
    ssh.exec(
        f'powershell -Command "New-Item -ItemType Directory '
        f"-Path '{REMOTE_TEMP}' -Force | Out-Null\""
    )

    for fname in os.listdir(_TEMPLATE_DIR):
        if not fname.endswith('.ps1'):
            continue

        local_path = f'{_TEMPLATE_DIR}/{fname}'
        remote_path = f'{REMOTE_TEMP}/{fname}'

        print(f'[+] 部署 {local_path} → {remote_path}')
        ssh.sftp_put(local_path, remote_path)
