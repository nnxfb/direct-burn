# develop/ — FPGA 远程烧录工具

FPGA 远程烧录工具，通过 SSH + Vivado 批量烧录 .bit 文件，支持 JTAG 指定、自动分配、串口监控。

## 快速开始

```bash
# 1. 创建虚拟环境 & 安装依赖
conda activate test         # 或 python -m venv venv
pip install -r requirements.txt

# 2. 配置凭据
cp direct_burn/secret.example.py direct_burn/secret.py
# 编辑 secret.py 填入实际 SSH/DB 密码

# 3. 查看可用 FPGA
python direct_burn.py --list

# 4. 烧录
python direct_burn.py --jtag C306A4BBABCD --bit top.bit
```

## 项目结构

```
develop/
├── direct_burn.py                  # CLI 入口 — 参数解析 + 烧录编排
├── direct_burn/                    # 核心库 (Python package)
│   ├── __init__.py                 # 公开 API — re-export 所有关键符号
│   ├── config.py                   # 配置入口 (从 secret.py 导入)
│   ├── secret.example.py           # 凭据模板 — 复制为 secret.py 填入真实值
│   ├── secret.py                   # 实际凭据 (gitignored)
│   ├── db.py                       # MySQL — 查询 + FpgaLock 互斥锁 + 心跳
│   ├── ssh.py                      # SSH 会话 (SshSession) + PS1 脚本部署
│   ├── hw_server.py                # hw_server 生命周期 + Vivado 远程烧录
│   ├── vivado.py                   # TCL 上传 + Vivado 执行 (占位)
│   ├── monitor.py                  # 远程串口直读 (SSH + PowerShell .NET SerialPort)
│   └── serial.py                   # 18-byte LE 帧解析 + 数码管解码 (共享模块)
├── scripts/                        # 部署到远程 FPGA 板卡的脚本模板
│   ├── start_hw_server.ps1         # hw_server 启动器 (端口清理 + .bat 生成)
│   ├── read_serial.ps1             # 串口主动查询 (发送 0x80, 读 18-byte LE)
│   ├── kill_port_admin.ps1         # 按端口杀进程
│   └── auto_program.tcl            # Vivado TCL 烧录脚本模板
├── requirements.txt                # pip 依赖清单
├── pyproject.toml                  # 项目元数据 (PEP 621)
├── .gitignore                      # 忽略 __pycache__, secret.py, 临时文件等
└── README.md                       # 本文件
```

## 配置

```bash
cp direct_burn/secret.example.py direct_burn/secret.py
```

`secret.py` 内容:

```python
# --- SSH 凭据 (远程 FPGA 板卡) ---
SSH_USER = 'remoteuser'
SSH_PASSWORD = 'mhw168'

# --- MySQL 凭据 (FPGA 状态数据库) ---
DB_HOST = '192.168.2.200'
DB_PORT = 3306
DB_USER = 'root'
DB_PASSWORD = 'mhw168'
DB_NAME = 'port_manager'

# --- Vivado 工具链路径 ---
VIVADO_BAT = 'D:/vivado/Vivado/2023.2/bin/vivado.bat'
HW_SERVER_BAT = 'D:/vivado/Vivado/2023.2/bin/hw_server.bat'

# --- 远程临时目录 ---
REMOTE_TEMP = 'C:/Temp/hw_script'
```

## 用法

```bash
# 查看所有可用 FPGA
python direct_burn.py --list

# 自动分配空闲板卡烧录 (烧录后自动串口监控 30s)
python direct_burn.py --bit path/to/fpga.bit

# 按 JTAG 编号指定设备
python direct_burn.py --jtag C306A4BBABCD --bit top.bit

# 按 FPGA 名称指定设备
python direct_burn.py --fpga-name FPGA_3121 --bit my_fpga.bit

# 自定义串口监控时长 (默认 30s)
python direct_burn.py --jtag C306A4BBABCD --bit top.bit --monitor-duration 60
```

## 架构

```
direct_burn.py                        # CLI 入口
 ├── direct_burn/config.py            # 凭据 & 路径
 │    ├── get_ssh_default_config()    # SSH 凭据
 │    └── get_db_default_config()     # MySQL 凭据 (含 DB_NAME)
 ├── direct_burn/db.py                # 数据库 (只读 + 互斥写)
 │    ├── list_all_fpga()             # 列出全部设备
 │    ├── list_available_fpga()       # 列出空闲设备 (status='available')
 │    ├── query_fpga_by_jtag()        # 按 JTAG 查询
 │    ├── query_fpga_by_name()        # 按名称查询
 │    └── FpgaLock                    # 互斥锁 + 心跳上下文管理器
 ├── direct_burn/ssh.py               # SSH 远程操作
 │    ├── SshSession                  # SSH 连接封装 (paramiko, 上下文管理器)
 │    └── deploy_scripts()            # 部署 PS1/TCL 到 C:\Temp\hw_script
 ├── direct_burn/hw_server.py         # JTAG 桥管理
 │    ├── HwServerSession             # hw_server 上下文管理器 (自动回收, 输出 PID)
 │    ├── _wait_for_hw_server()       # Socket 端口轮询 + 远程 PID 查询
 │    └── run_vivado_burn()           # SFTP 上传 + TCL 模板 + Vivado 执行
 ├── direct_burn/vivado.py            # TCL 上传 + Vivado 执行 (占位, 逻辑在 hw_server.py)
 ├── direct_burn/monitor.py           # 串口监控
 │    ├── remote_serial_monitor()     # SSH 远程串口直读入口
 │    └── _stream_ssh_serial()        # SSH + PowerShell .NET SerialPort 流式解析
 └── direct_burn/serial.py            # 协议解析 (共享)
      ├── SEGMENT_MAP                 # 7 段数码管映射
      ├── parse_data_frame()          # 18-byte LE 帧解析 → {seg, key, sw, led}
      ├── parse_seg_display()         # 40-bit seg → 4 位数码管 + 左右侧
      └── parse_led_bits()            # 32-bit led → 4×8 位图
```

## 烧录流程

```
1. 检查 COM 口存在性
   └── SSH 执行 [System.IO.Ports.SerialPort]::GetPortNames()

2. FpgaLock 占位
   ├── UPDATE status='in_use'
   └── 启动心跳线程 (45s 间隔)

3. 部署 + 烧录 (SSH → FPGA 板卡)
   ├── [1/3] 部署脚本
   │   ├── start_hw_server.ps1
   │   ├── read_serial.ps1
   │   ├── kill_port_admin.ps1
   │   └── auto_program.tcl
   │
   ├── [2/3] 启动 hw_server 并烧录
   │   ├── start_hw_server.ps1 → 生成 .bat → cmd.exe /c .bat
   │   ├── _wait_for_hw_server() → 端口就绪 + 输出 PID
   │   ├── run_vivado_burn()
   │   │   ├── SFTP 上传 .bit + auto_program.tcl
   │   │   └── vivado.bat -mode batch -source auto_program.tcl
   │   └── HwServerSession.__exit__ → kill_port_admin.ps1
   │
   └── [3/3] 远程串口监控
       └── read_serial.ps1 → 0x80 查询 → 18-byte LE 响应 → 数码管解码 + LED 位图

4. 清理
   ├── FpgaLock.__exit__ → UPDATE status='available'
   └── SSH 断开
```

## 串口协议 (18-byte Little-Endian)

| 字节 | 字段 | 说明 |
|------|------|------|
| 0-4  | seg  | 数码管 40-bit (5 bytes LE) |
| 5    | key  | 按键 1 byte |
| 6-13 | sw   | 拨码开关 64-bit (8 bytes LE) |
| 14-17| led  | LED 32-bit (4 bytes LE) |

主动查询: 发送 `0x80` → 读取 18 bytes 响应。

## 目标环境

| 组件 | 路径/值 |
|---|---|
| Vivado | `D:\vivado\Vivado\2023.2\bin\vivado.bat` |
| hw_server | `D:\vivado\Vivado\2023.2\bin\hw_server.bat` |
| 远程脚本目录 | `C:\Temp\hw_script\` |
| DB 服务器 | `192.168.2.200:3306` (port_manager) |
| SSH | `remoteuser@<FPGA_IP>:22` |
| Python | ≥3.9 |

## 注意事项

1. **原子互斥**: 烧录前标记 `status='in_use'` + 心跳, 防并发抢占
2. **崩溃恢复**: 进程崩溃 → 心跳停止 → 3 分钟后自动回收
3. **hw_server 自动回收**: `HwServerSession` 上下文管理器确保 hw_server 烧录完成后自动终止
4. **COM 口预检**: 烧录前检查目标 COM 口是否在线, 离线则直接退出
5. **PID 输出**: `_wait_for_hw_server` 就绪时输出远程 hw_server 进程 PID
