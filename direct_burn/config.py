# direct_burn/config.py — 凭据 & 路径配置
# 所有敏感值从 secret.py 导入 (gitignored, 不提交)
import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    from .secret import *
except ImportError:
    _dir = os.path.dirname(__file__)
    print(f'''
[!] 配置文件缺失 — secret.py 不存在

  cp {_dir}\\secret.example.py
     {_dir}\\secret.py

  然后编辑 secret.py 填入实际凭据。
  secret.py 已在 .gitignore 中，不会提交到仓库。
''')
    sys.exit(1)


def get_ssh_default_config():
    """获取 SSH 凭据 (host 由 FPGA 的 IP 决定)."""
    return SSH_PORT, SSH_USER, SSH_PASSWORD


def get_db_default_config():
    """获取 DB 凭据."""
    return DB_HOST, DB_PORT, DB_USER, DB_PASSWORD


# 以下变量由 secret.py 提供:
#   SSH_PORT, SSH_USER, SSH_PASSWORD
#   DB_HOST, DB_PORT, DB_USER, DB_PASSWORD
#   VIVADO_BAT, HW_SERVER_BAT, REMOTE_TEMP


# ── 派生变量 ─────────────────────────────────────────────────────────
REMOTE_TEMP_WIN = REMOTE_TEMP.replace('/', '\\')

_TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts')
