# direct_burn/ssh.py — SSH 会话封装 + PS1 脚本部署

import os

import paramiko

from .config import REMOTE_TEMP, SCRIPT_DIR, get_ssh_default_config


class SshSession:
    """SSH 会话封装"""

    def __init__(self, host):
        _user, _pass = get_ssh_default_config()
        self.host = host
        self.username = _user
        self.password = _pass
        self._ssh = None

    def connect(self):
        self._ssh = paramiko.SSHClient()
        self._ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._ssh.connect(
            hostname=self.host,
            port=22,
            username=self.username,
            password=self.password,
            timeout=15,
            look_for_keys=False,
            allow_agent=False,
        )
        print(f'[+] SSH 已连接: {self.username}@{self.host}:{22}')

    def exec(self, cmd: str, timeout=30):
        """执行命令, 返回 (stdout, stderr, exit_code)"""
        # print('cmd >', cmd)
        stdin, stdout, stderr = self._ssh.exec_command(cmd, timeout=timeout)
        out = stdout.read().decode(errors='replace')
        err = stderr.read().decode(errors='replace')
        exit_code = stdout.channel.recv_exit_status()
        return out, err, exit_code
    
    def exec_bg(self, cmd: str):
        self._ssh.exec_command(cmd)

    def upload(self, local_path: str, remote_path: str):
        sftp = self._ssh.open_sftp()
        sftp.put(local_path, remote_path)
        sftp.close()

    def close(self):
        if self._ssh:
            self._ssh.close()
        print(f'[+] SSH 已断开: {self.username}@{self.host}:{22}')

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.close()


def deploy_scripts(ssh: SshSession):
    """上传 template/*.ps1 到远程 REMOTE_TEMP."""
    
    ssh.exec(f'powershell -Command "New-Item -ItemType Directory -Path \'{REMOTE_TEMP}\' -Force | Out-Null"')

    for fname in os.listdir(SCRIPT_DIR):

        local_path = f'{SCRIPT_DIR}/{fname}'
        remote_path = f'{REMOTE_TEMP}/{fname}'

        print(f'[+] 上传 {fname:<20} -> {remote_path}')
        ssh.upload(local_path, remote_path)
