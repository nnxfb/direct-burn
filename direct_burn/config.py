# direct_burn/config.py — 凭据 & 路径配置
import os
from .secret import *

def get_ssh_default_config():
    return SSH_USER, SSH_PASSWORD


def get_db_default_config():
    return DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME


SCRIPT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts')
