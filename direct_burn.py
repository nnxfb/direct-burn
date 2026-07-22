#!/usr/bin/env python3
"""
direct_burn.py — 免登录·免记次·直接远程 FPGA 烧录工具

用法:
    python direct_burn.py --bit path/to/fpga.bit                       # 自动分配板卡+串口监控
    python direct_burn.py --jtag C306A4BBABCD --bit test.bit            # 指定 JTAG+串口监控
    python direct_burn.py --fpga-name FPGA_3121 --bit test.bit          # 指定名称+串口监控
    python direct_burn.py --list                                        # 查看可用设备
    python direct_burn.py --bit test.bit --monitor-duration 60          # 自定义监控时长
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from direct_burn.config import VIVADO_BAT, get_db_default_config, get_ssh_default_config
from direct_burn.db import (
    list_all_fpga, list_available_fpga, query_fpga_by_jtag, query_fpga_by_name,
    FpgaLock,
)
from direct_burn.ssh import SshSession, deploy_ps1_scripts
from direct_burn.hw_server import HwServerSession
from direct_burn.vivado import run_vivado_burn
from direct_burn.monitor import remote_serial_monitor_direct


def print_fpga_list(rows):
    """格式化打印 FPGA 设备列表."""
    if not rows:
        print('[!] 没有可用设备')
        return

    header = (f'{"FPGA Name":<16} {"IP":<16} {"Port":<8} '
              f'{"JTAG":<20} {"COM":<8} {"VCOM":<8} {"Status":<12}')
    print(f'\n{header}')
    print('-' * len(header))
    for r in rows:
        print(
            f'{r["fpga_name"]:<16} '
            f'{r["IP"]:<16} '
            f'{r["total_port"]:<8} '
            f'{r["jtag_filter"]:<20} '
            f'{r["com_name"]:<8} '
            f'{r["vcom_name"]:<8} '
            f'{r["status"]:<12}'
        )
    print(f'\n共 {len(rows)} 台设备')


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='direct_burn.py — 免登录直接远程 FPGA 烧录工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python direct_burn.py --bit my_fpga.bit                   # 自动分配板卡
  python direct_burn.py --jtag C306A4BBABCD --bit test.bit    # 指定 JTAG
  python direct_burn.py --fpga-name FPGA_3121 --bit test.bit  # 指定名称
  python direct_burn.py --list                                # 查看可用设备
        """,
    )
    parser.add_argument('--jtag', help='按 JTAG 编号指定设备 (不指定则自动分配)')
    parser.add_argument('--fpga-name', help='按 fpga_name 指定设备 (不指定则自动分配)')
    parser.add_argument('--list', action='store_true', help='列出所有可用 FPGA 设备')

    parser.add_argument('--bit', help='要烧录的 .bit 文件路径')

    parser.add_argument('--db-host', help='MySQL 服务器 IP')
    parser.add_argument('--db-port', type=int, help='MySQL 端口')
    parser.add_argument('--db-user', help='MySQL 用户名')
    parser.add_argument('--db-pass', help='MySQL 密码')
    
    parser.add_argument('--ssh-port', type=int, help='SSH 端口')
    parser.add_argument('--ssh-user', help='SSH 用户名')
    parser.add_argument('--ssh-pass', help='SSH 密码')

    parser.add_argument('--vivado-path', default=None, help=f'Vivado 路径 (默认: {VIVADO_BAT})')
    parser.add_argument('--timeout', type=int, default=120, help='Vivado 执行超时秒数')

    # 串口监控 (默认开启)
    parser.add_argument('--monitor-duration', type=int, default=30, help='烧录后远程串口监控时长秒数 (默认: 30)')

    args = parser.parse_args()

    # ---- 解析 DB / SSH 配置 (参数 > config 默认值) ----
    _dh, _dp, _du, _dpass = get_db_default_config()
    db_host = args.db_host or _dh
    db_port = args.db_port or _dp
    db_user = args.db_user or _du
    db_pass = args.db_pass if args.db_pass is not None else _dpass

    _sp, _su, _spass = get_ssh_default_config()
    ssh_port = args.ssh_port or _sp
    ssh_user = args.ssh_user or _su
    ssh_pass = args.ssh_pass or _spass

    # ---- List 模式 ----
    if args.list:
        print(f'[*] 查询全部 FPGA 设备 (DB: {db_host})...')
        rows = list_all_fpga(db_host, db_port, db_user, db_pass)
        print_fpga_list(rows)
        return

    # ---- 参数检查 ----
    if not args.bit:
        parser.error('请指定 --bit (要烧录的 .bit 文件)')
    if not os.path.exists(args.bit):
        print(f'[!] Bit 文件不存在: {args.bit}')
        sys.exit(1)

    # ---- 查询 FPGA 信息 ----
    print(f'[*] 查询 FPGA 设备信息 (DB: {db_host})...')

    if args.fpga_name:
        fpga_info = query_fpga_by_name(db_host, args.fpga_name, db_pass)
    elif args.jtag:
        fpga_info = query_fpga_by_jtag(db_host, args.jtag, db_pass)
    else:
        rows = list_available_fpga(db_host, db_pass)
        if not rows:
            print('[!] 没有可用设备')
            sys.exit(1)
        fpga_info = rows[0]
        print(f'[*] 自动分配: {fpga_info["fpga_name"]} (JTAG={fpga_info["jtag_filter"]})')

    if not fpga_info:
        print(f'[!] 未找到设备: {args.fpga_name or args.jtag}')
        sys.exit(1)

    print(f'\n{"="*60}')
    print(f'  设备信息')
    print(f'{"="*60}')
    for key in ['fpga_name', 'IP', 'total_port', 'jtag_filter', 'com_name', 'vcom_name', 'result']:
        print(f'  {key:<16}: {fpga_info.get(key, "N/A")}')
    print(f'{"="*60}')

    server_ip = fpga_info['IP']
    vivado_port = fpga_info['total_port']
    jtag_filter = fpga_info['jtag_filter']
    com_name = fpga_info['com_name']
    fpga_name = fpga_info['fpga_name']
    success = False

    try:
        with FpgaLock(fpga_name, db_host, db_pass) as lock:
            print(f'\n{"="*60}')
            print(f'  开始烧录: {jtag_filter}')
            print(f'  Bit 文件: {args.bit}')
            print(f'  目标主机: {server_ip}')
            print(f'{"="*60}')

            with SshSession(server_ip, port=ssh_port, username=ssh_user, password=ssh_pass) as ssh:
                print(f'\n[Step 1/4] 部署远程脚本...')
                deploy_ps1_scripts(ssh)

                print(f'\n[Step 2/4] 启动 hw_server + Vivado 烧录...')
                with HwServerSession(ssh, server_ip, vivado_port, jtag_filter):
                    success = run_vivado_burn(ssh, server_ip, vivado_port, args.bit, jtag_filter, vivado_path=args.vivado_path)
               
                if success:
                    print(f'\n[Step 3/4] 远程串口直读 ({com_name}, {args.monitor_duration}s)...')
                    remote_serial_monitor_direct(ssh, com_name, duration=args.monitor_duration)

    except RuntimeError as e:
        print(f'[!] {e}')
        sys.exit(1)
    except Exception as e:
        import traceback
        print(f'[!] 烧录过程异常: {e}')
        traceback.print_exc()
        success = False

    if success:
        print(f'[+] 板卡 {jtag_filter} 烧录完成!')
    else:
        print(f'[!] 板卡 {jtag_filter} 烧录失败!')
        sys.exit(1)


if __name__ == '__main__':
    main()
