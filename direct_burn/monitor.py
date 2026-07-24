# direct_burn/monitor.py — 远程串口直读 (SSH + PowerShell .NET SerialPort)

import time

from .config import REMOTE_TEMP
from .serial import parse_data_frame, parse_seg_display, parse_led_bits
from .ssh import SshSession


def remote_serial_monitor(ssh: SshSession, com_port: str, duration=30, baudrate=9600):
    """通过 SSH + PowerShell .NET SerialPort 查询远程 FPGA 串口.

    PS1 发送 0x80 命令 -> 读取 18 字节 LE 响应 -> 解析数码管. 

    Args:
        ssh: SshSession 实例
        com_port: 远程物理串口号 (e.g. 'COM14')
        duration: 监控时长秒数
        baudrate: 波特率 (默认 9600)
    """
    print(f'\n{"="*60}')
    print(f'远程串口: {com_port} (SSH + .NET SerialPort, {baudrate} 8N1)')
    print(f'协议: 发送 0x80 -> 读取 18 字节 LE 响应')
    print(f'监控时长: {duration}s  (Ctrl+C 中断)')
    print(f'{"="*60}')

    state = {'left': None, 'right': None, 'reads': 0}
    start = time.time()

    def handle_frame(hex_bytes):
        """每收到完整一行 18 hex 字节时回调."""
        state['reads'] += 1

        frame = parse_data_frame(hex_bytes)
        if frame is None:
            return

        digits, side = parse_seg_display(frame['seg'])
        if digits is None:
            return

        if side == 'L':
            state['left'] = digits
        elif side == 'R':
            state['right'] = digits

        if state['left'] and state['right']:
            combined = ''
            for i in range(4):
                combined += state['left'][i] + state['right'][i]
            state['left'] = None
            state['right'] = None

            led_data = parse_led_bits(frame['led'])

            print(f'[{time.strftime('%H:%M:%S')}]')
            print(led_data[0].replace('0','.').replace('1','#'), combined)
            print(led_data[1].replace('0','.').replace('1','#'))
            print(led_data[2].replace('0','.').replace('1','#'))
            print(led_data[3].replace('0','.').replace('1','#'))
                
        elif state['reads'] % 20 == 1:
            ts = time.strftime('%H:%M:%S')
            print(f'[{ts}] 偏帧 {side}: {digits}  (共 {state["reads"]} 次读取)')

    try:
        _stream_ssh_serial(ssh, com_port, duration, baudrate, handle_frame)
    except KeyboardInterrupt:
        print('\n[!] 用户中断')
    except Exception as e:
        print(f'\n[!] 串口监控异常: {e}')
        import traceback
        traceback.print_exc()

    elapsed = int(time.time() - start)
    print(f'[+] 共 {state["reads"]} 次读取, 耗时 {elapsed}s')


def _stream_ssh_serial(ssh, com_port, duration, baudrate, callback):
    """SSH 执行远程 read_serial.ps1, 逐行解析 18-byte hex.

    PS1 每行输出 18 个空格分隔的 hex 字节, 最后输出 "DONE".
    """
    ps1_path = f'{REMOTE_TEMP}/read_serial.ps1'
    cmd = f'powershell -ExecutionPolicy Bypass -File "{ps1_path}" -ComPort "{com_port}" -BaudRate {baudrate} -Duration {duration}'

    print(f'[>] {cmd}')
    out, err, _ = ssh.exec(cmd)

    for line in out.splitlines():
        line = line.strip()
        if line == 'DONE':
            break
        if line:
            hex_bytes = line.split()
            if len(hex_bytes) >= 18:
                callback(hex_bytes)

    if err.strip():
        print(f'[!] 远程 stderr: {err.strip()[:200]}')
