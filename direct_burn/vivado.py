# direct_burn/vivado.py — TCL 上传 + Vivado 远程烧录

from .config import REMOTE_TEMP, VIVADO_BAT, _TEMPLATE_DIR


def run_vivado_burn(ssh, ip, port, local_bitfile, jtag_filter, vivado_path=None):
    """上传 bit 文件 + 上传 TCL 模板 + 远程执行 Vivado. 返回 True/False."""
    if vivado_path is None:
        vivado_path = VIVADO_BAT

    print(f'\n[*] 上传 bit 文件并执行 Vivado 烧录...')

    # 确保远程目录存在
    ssh.exec(
        f'powershell -Command "New-Item -ItemType Directory '
        f"-Path '{REMOTE_TEMP}' -Force | Out-Null\""
    )

    remote_bit = f'{REMOTE_TEMP}/{jtag_filter}_fpga.bit'
    remote_tcl = f'{REMOTE_TEMP}/auto_program.tcl'

    # 1. SFTP 上传 bit 文件
    print(f'[+] 上传 bit: {local_bitfile} → {remote_bit}')
    ssh.sftp_put(local_bitfile, remote_bit)

    # 2. SFTP 上传 TCL 脚本
    local_tcl = f'{_TEMPLATE_DIR}/auto_program.tcl'
    print(f'[+] 上传 TCL: {local_tcl} → {remote_tcl}')
    ssh.sftp_put(local_tcl, remote_tcl)

    # 3. 执行 Vivado
    vivado_path_win = vivado_path.replace('/', '\\')
    cmd = (
        f'"{vivado_path_win}" -mode batch -source "{remote_tcl}" '
        f'-tclargs {ip} {port} "{remote_bit}"'
    )
    print(f'[+] 执行: {cmd}')
    out, err, exit_code = ssh.exec(cmd, timeout=120)

    print(f'\n  {"="*60}')
    print(f'  📤 Vivado stdout:')
    print(f'  {out.strip() or "(无输出)"}')
    if err.strip():
        print(f'  📥 Vivado stderr:')
        print(f'  {err.strip()}')
    print(f'  退出码: {exit_code}')
    print(f'  {"="*60}')

    return exit_code == 0
