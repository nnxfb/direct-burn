#!/usr/bin/env python3
"""
direct_burn.py — FPGA 远程烧录工具

用法:
    python direct_burn.py --bit path/to/fpga.bit                        # 自动分配板卡 + 串口监控
    python direct_burn.py --jtag C306A4BBABCD --bit test.bit            # 指定板卡JTAG + 串口监控
    python direct_burn.py --fpga-name FPGA20 --bit test.bit             # 指定板卡名称 + 串口监控
    python direct_burn.py --list                                        # 查看设备状态
    python direct_burn.py --bit test.bit --monitor-duration 60          # 自定义监控时长
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from direct_burn.config import get_db_default_config, get_ssh_default_config
from direct_burn.db import (
    list_all_fpga, list_available_fpga, query_fpga_by_jtag, query_fpga_by_name,
    FpgaLock,
)
from direct_burn.ssh import SshSession, deploy_scripts
from direct_burn.hw_server import HwServerSession, run_vivado_burn
from direct_burn.monitor import remote_serial_monitor

def format_fpga_info(entry) -> str:
    info = (
        f'{entry["fpga_name"]:<8}{entry["IP"]:<16}{entry["total_port"]:<6}{entry["jtag_filter"]:<14}{entry["com_name"]:<8}'
        f'{entry["vcom_name"]:<6}{entry["status"]:<12}{entry["last_heartbeat"].strftime("%Y-%m-%d %H:%M:%S"):<20}'
    )
    return info

def print_fpga_list(rows):
    """格式化打印 FPGA 设备列表."""
    if not rows:
        print('[!] 没有可用设备')
        return

    header = f'{"FPGA":<8}{"IP":<16}{"Port":<6}{"JTAG":<14}{"COM":<8}{"VCOM":<6}{"Status":<12}{"Last":<20}'
    print(f'{header}')
    print('-' * len(header))
    for r in rows:
        print((format_fpga_info(r)))
    print(f'\n共 {len(rows)} 台设备')


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='远程 FPGA 烧录工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python direct_burn.py --bit my_fpga.bit                     # 自动分配板卡
  python direct_burn.py --jtag C306A4BBABCD --bit test.bit    # 指定板卡JTAG
  python direct_burn.py --fpga-name FPGA_3121 --bit test.bit  # 指定板卡名称
  python direct_burn.py --list                                # 查看所有设备
        """,
    )
    parser.add_argument('--jtag', help='按 JTAG 编号指定设备 (不指定则自动分配)')
    parser.add_argument('--fpga-name', help='按 fpga_name 指定设备 (不指定则自动分配)')
    parser.add_argument('--list', action='store_true', help='列出所有可用 FPGA 设备')

    parser.add_argument('--bit', help='要烧录的 .bit 文件路径')

    parser.add_argument('--monitor-duration', type=int, default=30, help='烧录后远程串口监控时长秒数 (默认: 30)')

    args = parser.parse_args()

    _dh, _dp, _du, _dpass, _dn = get_db_default_config()
    db_host = _dh
    db_port = _dp
    db_user = _du
    db_pass = _dpass
    db_name = _dn

    _su, _spass = get_ssh_default_config()
    ssh_user = _su
    ssh_pass = _spass

    # ---- List 模式 ----
    if args.list:
        print(f'[+] 查询全部 FPGA 设备 (DB: {db_host})...')
        rows = list_all_fpga()
        print_fpga_list(rows)
        return

    # ---- 参数检查 ----
    if not args.bit:
        parser.error('请指定 --bit (要烧录的 .bit 文件)')
    if not os.path.exists(args.bit):
        print(f'[!] Bit 文件不存在: {args.bit}')
        sys.exit(1)

    # ---- 查询 FPGA 信息 ----
    print(f'[+] 查询 FPGA 设备信息 (DB: {db_host})...')

    if args.fpga_name:
        fpga_info = query_fpga_by_name(args.fpga_name)
    elif args.jtag:
        fpga_info = query_fpga_by_jtag(args.jtag)
    else:
        rows = list_available_fpga()
        if not rows:
            print('[!] 没有可用设备')
            sys.exit(1)
        fpga_info = rows[0]

    if not fpga_info:
        print(f'[!] 未找到设备: {args.fpga_name or args.jtag}')
        sys.exit(1)

    print(f'\n{"="*60}')
    for key in ['fpga_name', 'IP', 'total_port', 'jtag_filter', 'com_name', 'vcom_name', 'result']:
        print(f'{key:<16}: {fpga_info.get(key, "N/A")}')
    print(f'{"="*60}')

    server_ip   = fpga_info['IP']
    vivado_port = fpga_info['total_port']
    jtag        = fpga_info['jtag_filter']
    com_name    = fpga_info['com_name']
    fpga_name   = fpga_info['fpga_name']
    success = False

    with SshSession(server_ip) as ssh:
        out, _, _ = ssh.exec('powershell -Command "[System.IO.Ports.SerialPort]::GetPortNames()"')
        com_list = out.splitlines()
    if com_name not in com_list:
        print(f'[!] {com_name} 已下线！')
        sys.exit(1)
    else:
        print(f'[+] {com_name} 存在！')

    try:
        with FpgaLock(fpga_name):
            print(f'{"="*60}')
            print(f'开始烧录: {jtag}')
            print(f'Bit 文件: {args.bit}')
            print(f'目标主机: {server_ip}')
            print(f'{"="*60}')

            with SshSession(server_ip) as ssh:
                print(f'[1/3] 部署远程脚本...')
                deploy_scripts(ssh)

                print(f'[2/3] 启动 hw_server 并烧录...')
                with HwServerSession(ssh, server_ip, vivado_port, jtag):
                    success = run_vivado_burn(ssh, server_ip, vivado_port, args.bit, jtag)
               
                if success:
                    print(f'[3/3] 读取远程串口 ({com_name}, {args.monitor_duration}s)...')
                    remote_serial_monitor(ssh, com_name, duration=args.monitor_duration)

    except RuntimeError as e:
        print(f'[!] {e}')
        sys.exit(1)
    except Exception as e:
        import traceback
        print(f'[!] 烧录过程异常: {e}')
        traceback.print_exc()
        success = False

    if success:
        print(f'[+] 板卡 {jtag} 烧录完成!')
    else:
        print(f'[!] 板卡 {jtag} 烧录失败!')
        sys.exit(1)


if __name__ == '__main__':
    main()
