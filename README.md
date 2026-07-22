# develop/ 鈥?鐩存帴杩滅▼鐑у綍宸ュ叿

鍏嶇櫥褰曘€佸厤鏁版嵁搴撴洿鏂扮殑 FPGA 杩滅▼鐑у綍宸ュ叿銆備粠鍘熷簲鐢?`gui_handlers.py` 鎻愬彇鏍稿績鐑у綍娴佺▼锛?鍓ョ鎵€鏈夎璇佸拰鐘舵€佺鐞嗛€昏緫銆?
## 蹇€熷紑濮?
```bash
# 1. 鍒涘缓铏氭嫙鐜 & 瀹夎渚濊禆
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# 2. 閰嶇疆鍑嵁
cp direct_burn/secret.example.py direct_burn/secret.py
# 缂栬緫 secret.py 濉叆瀹為檯 SSH/DB 瀵嗙爜

# 3. 鏌ョ湅鍙敤 FPGA
python direct_burn.py --list

# 4. 鐑у綍
python direct_burn.py --jtag C306A4BBABCD --bit path/to/fpga.bit
```

## 椤圭洰缁撴瀯

```
develop/
鈹溾攢鈹€ direct_burn.py              # CLI 鍏ュ彛 鈥?鍙傛暟瑙ｆ瀽 + 鐑у綍缂栨帓
鈹溾攢鈹€ direct_burn/                # 鏍稿績搴?(Python package)
鈹?  鈹溾攢鈹€ __init__.py             # 鍏紑 API 鈥?re-export 鎵€鏈夊叧閿鍙?鈹?  鈹溾攢鈹€ config.py               # 閰嶇疆鍏ュ彛 (浠?secret.py 瀵煎叆, 鍙畨鍏ㄦ彁浜?
鈹?  鈹溾攢鈹€ secret.example.py  # 鍑嵁妯℃澘 鈥?澶嶅埗涓?secret.py 濉叆鐪熷疄鍊?鈹?  鈹溾攢鈹€ secret.py          # 瀹為檯鍑嵁 (gitignored, 涓嶆彁浜ゅ埌浠撳簱)
鈹?  鈹溾攢鈹€ db.py                   # MySQL 鏁版嵁搴?鈥?鏌ヨ + FpgaLock 浜掓枼閿?鈹?  鈹溾攢鈹€ ssh.py                  # SSH 浼氳瘽 (SshSession) + PS1 鑴氭湰閮ㄧ讲
鈹?  鈹溾攢鈹€ hw_server.py            # hw_server 涓婁笅鏂囩鐞嗗櫒 (HwServerSession)
鈹?  鈹溾攢鈹€ vivado.py               # TCL 涓婁紶 + Vivado 杩滅▼鎵ц
鈹?  鈹溾攢鈹€ serial.py               # 18-byte LE 甯цВ鏋?+ 鏁扮爜绠¤В鐮?(鍏变韩妯″潡)
鈹?  鈹斺攢鈹€ monitor.py              # 杩滅▼涓插彛鐩磋 鈥?SSH + PowerShell .NET SerialPort
鈹溾攢鈹€ scripts/                    # 閮ㄧ讲鍒拌繙绋?FPGA 鏉垮崱鐨勮剼鏈ā鏉?鈹?  鈹溾攢鈹€ start_hw_server.ps1     # hw_server 鍚姩鍣?(绔彛娓呯悊 + .bat 鐢熸垚)
鈹?  鈹溾攢鈹€ read_serial.ps1         # 涓插彛涓诲姩鏌ヨ (鍙戦€?0x80, 璇?18-byte LE 甯?
鈹?  鈹溾攢鈹€ kill_port_admin.ps1     # 鎸夌鍙ｆ潃杩涚▼
鈹?  鈹斺攢鈹€ auto_program.tcl        # Vivado TCL 鐑у綍鑴氭湰妯℃澘
鈹溾攢鈹€ requirements.txt            # pip 渚濊禆娓呭崟
鈹溾攢鈹€ pyproject.toml              # 椤圭洰鍏冩暟鎹?(PEP 621)
鈹溾攢鈹€ .gitignore                  # 蹇界暐 __pycache__, secret.py, 涓存椂鏂囦欢绛?鈹斺攢鈹€ README.md                   # 鏈枃浠?```

## 閰嶇疆

```bash
# 1. 澶嶅埗鍑嵁妯℃澘
cp direct_burn/secret.example.py direct_burn/secret.py

# 2. 缂栬緫 secret.py 濉叆瀹為檯鍑嵁
# secret.py 宸插湪 .gitignore 鈥?瀵嗙爜涓嶄細鎻愪氦鍒?GitHub
```

`secret.py` 鍐呭:

```python
# --- SSH 鍑嵁 (杩滅▼ FPGA 鏉垮崱) ---
SSH_PORT = 22
SSH_USER = 'remoteuser'
SSH_PASSWORD = 'your_password'

# --- MySQL 鍑嵁 (FPGA 鐘舵€佹暟鎹簱) ---
DB_HOST = '192.168.1.100'
DB_PORT = 3306
DB_USER = 'root'
DB_PASSWORD = 'your_password'

# --- Vivado 宸ュ叿閾捐矾寰?---
VIVADO_BAT = 'D:/vivado/Vivado/2023.2/bin/vivado.bat'
HW_SERVER_BAT = 'D:/vivado/Vivado/2023.2/bin/hw_server.bat'

# --- 杩滅▼涓存椂鐩綍 ---
REMOTE_TEMP = 'C:/Temp/hw_script'
```

涔熷彲閫氳繃 CLI 鍙傛暟瑕嗙洊 (浼樺厛绾ф渶楂?:

```bash
python direct_burn.py --bit test.bit --ssh-user admin --ssh-pass mypass --db-host 10.0.0.1
```

浼樺厛绾? **CLI 鍙傛暟 > secret.py**

## 渚濊禆

```
conda activate test        # 鎴栦娇鐢?venv
pip install -r requirements.txt

# 鍙€? Fernet 鍑嵁瑙ｅ瘑
pip install cryptography

# 鍙€? WebSocket 楠岃瘉
pip install websockets

# 鍙€? 鏈湴 RFC2217 涓插彛杞彂 (--monitor 妯″紡)
pip install pyserial
```

## 鐢ㄦ硶

```bash
# 鏌ョ湅鎵€鏈夊彲鐢?FPGA
python direct_burn.py --list

# 鑷姩鍒嗛厤绌洪棽鏉垮崱鐑у綍 (鐑у綍鍚庤嚜鍔ㄤ覆鍙ｇ洃鎺?30s)
python direct_burn.py --bit path/to/fpga.bit

# 鎸?JTAG 缂栧彿鎸囧畾璁惧
python direct_burn.py --jtag C306A4BBABCD --bit path/to/fpga.bit

# 鎸?FPGA 鍚嶇О鎸囧畾璁惧
python direct_burn.py --fpga-name FPGA_3121 --bit my_fpga.bit

# 鑷畾涔変覆鍙ｇ洃鎺ф椂闀?(榛樿 30s)
python direct_burn.py --jtag C306A4BBABCD --bit test.bit --monitor-duration 60

# 鑷畾涔?Vivado 璺緞鍜岃秴鏃?python direct_burn.py --jtag C306A4BBABCD --bit test.bit --vivado-path "C:/Xilinx/Vivado/2024.1/bin/vivado.bat" --timeout 180

# 瑕嗙洊 SSH/DB 鍑嵁 (鍛戒护琛屽弬鏁颁紭鍏堜簬 secret.py)
python direct_burn.py --bit test.bit --ssh-user admin --ssh-pass mypass --db-host 10.0.0.1
```

## 鏋舵瀯

```
direct_burn.py                      # CLI 鍏ュ彛
鈹?鈹溾攢鈹€ direct_burn/config.py           # 鍑嵁 & 璺緞
鈹?  鈹溾攢鈹€ get_ssh_default_config()    # SSH 鍑嵁 (host 鐢?FPGA IP 鍐冲畾)
鈹?  鈹斺攢鈹€ get_db_default_config()     # MySQL 鍑嵁
鈹?鈹溾攢鈹€ direct_burn/db.py               # 鏁版嵁搴?(鍙)
鈹?  鈹溾攢鈹€ list_available_fpga()       # 鍒楀嚭鍙敤璁惧
鈹?  鈹溾攢鈹€ query_fpga_by_jtag()        # 鎸?JTAG 鏌ヨ
鈹?  鈹溾攢鈹€ query_fpga_by_name()        # 鎸夊悕绉版煡璇?鈹?  鈹斺攢鈹€ FpgaLock                    # 浜掓枼閿?+ 蹇冭烦涓婁笅鏂囩鐞嗗櫒
鈹?鈹溾攢鈹€ direct_burn/ssh.py              # SSH 杩滅▼鎿嶄綔
鈹?  鈹溾攢鈹€ SshSession                  # SSH 杩炴帴灏佽 (paramiko)
鈹?  鈹斺攢鈹€ deploy_ps1_scripts()        # 閮ㄧ讲 PS1 鍒?C:\Temp\hw_script
鈹?鈹溾攢鈹€ direct_burn/hw_server.py        # JTAG 妗ョ鐞?鈹?  鈹溾攢鈹€ HwServerSession             # hw_server 涓婁笅鏂囩鐞嗗櫒 (鑷姩鍥炴敹)
鈹?  鈹斺攢鈹€ wait_for_hw_server()        # Socket 绔彛杞
鈹?鈹溾攢鈹€ direct_burn/vivado.py           # FPGA 鐑у綍
鈹?  鈹斺攢鈹€ run_vivado_burn()           # SFTP + TCL + Vivado 鎵ц
鈹?鈹溾攢鈹€ direct_burn/monitor.py          # 涓插彛鐩戞帶
鈹?  鈹斺攢鈹€ remote_serial_monitor_direct()  # SSH 杩滅▼涓插彛鐩磋
鈹?鈹斺攢鈹€ direct_burn/serial.py           # 鍗忚瑙ｆ瀽 (鍏变韩)
    鈹溾攢鈹€ SEGMENT_MAP                 # 7 娈垫暟鐮佺鏄犲皠
    鈹溾攢鈹€ parse_18byte_frame()        # 18-byte LE 甯цВ鏋?    鈹斺攢鈹€ parse_seg_display()         # 鏁扮爜绠¤В鐮?```

## 鐑у綍娴佺▼

```
1. 閮ㄧ讲 PS1 鑴氭湰 鈫?FPGA 鏉垮崱 C:\Temp\hw_script\
   鈹溾攢鈹€ start_hw_server.ps1   (绔彛娓呯悊 + .bat 鐢熸垚)
   鈹溾攢鈹€ read_serial.ps1       (涓插彛涓诲姩鏌ヨ)
   鈹斺攢鈹€ kill_port_admin.ps1   (鎸夌鍙ｆ潃杩涚▼)

2. SSH 鈫?FPGA 鏉垮崱
   鈹溾攢鈹€ 鍚姩 hw_server (JTAG 妗? 鐩戝惉 tcp:<port>)
   鈹?  鈹斺攢鈹€ PS1 鐢熸垚 .bat 鈫?Python fire-and-forget cmd.exe /c .bat
   鈹斺攢鈹€ 杞绛夊緟绔彛灏辩华 (socket connect)

3. Vivado 鐑у綍
   鈹溾攢鈹€ SFTP 涓婁紶 .bit + auto_program.tcl 鈫?C:\Temp\hw_script\
   鈹斺攢鈹€ SSH 鎵ц vivado.bat -mode batch -source auto_program.tcl

4. 涓插彛鐩戞帶 (榛樿寮€鍚? --monitor-duration 鎺у埗鏃堕暱)
   鈹溾攢鈹€ PS1 寰幆鍙戦€?0x80 鈫?璇诲彇 18-byte LE 鍝嶅簲甯?   鈹斺攢鈹€ 瑙ｆ瀽鏁扮爜绠?鎸夐敭/寮€鍏?LED

5. 娓呯悊 鈥?HwServerSession.__exit__ 鑷姩鎵ц
   鈹斺攢鈹€ kill_port_admin.ps1 鈫?缁堟 hw_server
```

## 涓插彛鍗忚 (18-byte Little-Endian)

| 瀛楄妭 | 瀛楁 | 璇存槑 |
|------|------|------|
| 0-4  | seg  | 鏁扮爜绠?40-bit (5 bytes LE) |
| 5    | key  | 鎸夐敭 1 byte |
| 6-13 | sw   | 寮€鍏?64-bit (8 bytes LE) |
| 14-17| led  | LED 32-bit (4 bytes LE) |

涓诲姩鏌ヨ: 鍙戦€?`0x80` 鈫?璇诲彇 18 bytes 鍝嶅簲銆?
## 鐩爣鐜

| 缁勪欢 | 璺緞/鍊?|
|---|---|
| Vivado | `C:\Xilinx\Vivado\2023.2\bin\vivado.bat` |
| hw_server | `C:\Xilinx\Vivado\2023.2\bin\hw_server.bat` |
| 杩滅▼鑴氭湰鐩綍 | `C:\Temp\hw_script\` |
| DB 鏈嶅姟鍣?| `192.168.1.100:3306` (port_manager) |
| SSH 绔彛 | `22` |
| 鍑嵁 | `secret.py` (澶嶅埗鑷?`secret.example.py`, gitignored) |
| Python | 鈮?3.9 |

## 涓庡師濮嬪簲鐢ㄧ殑宸紓

| 鍘熷娴佺▼ | direct_burn.py | 璇存槑 |
|---|---|---|
| `authenticate_user()` 鐧诲綍 | 鉂?璺宠繃 | 鏃犵櫥褰曠棔杩?|
| `mark_fpga_in_use()` | 鉁?淇濈暀 | 鍘熷瓙浜掓枼, 闃叉姠鍗?|
| `start_heartbeat()` | 鉁?淇濈暀 | 淇濇椿, 闃茶秴鏃跺洖鏀?|
| `increment_usage_count()` | 鉂?璺宠繃 | **涓嶆洿鏂?`used_times`** (鏍稿績闇€姹? |
| `save_result()` | 鉂?璺宠繃 | 涓嶅啓 `experiment_results` |
| `update_fpga_status()` (閲婃斁) | 鉁?淇濈暀 | 鐑у畬閲婃斁鍥?`status='available'` |
| `start_countdown()` / `close_all()` | 鉂?璺宠繃 | 涓嶈嚜鍔ㄥ叧闂? 鎵嬪姩绠＄悊 |
| `fetch_available_fpga_smart()` (鍙) | 鉁?淇濈暀 | 璇诲彇 FPGA 淇℃伅 |
| `start_remote_hw_server()` | 鉁?淇濈暀 | HwServerSession 涓婁笅鏂囩鐞嗗櫒 |
| `start_remote_com2tcp()` | 鉂?鏈疄鐜?| 涓插彛鐩磋鏇夸唬 (SSH + .NET SerialPort) |
| `stop_remote_hw_server()` | 鉁?鑷姩 | `__exit__` 鑷姩鍥炴敹, 鏃犻渶鎵嬪姩 |
| 鏈湴 com2tcp / FPGA.exe / WebSocket | 鉂?鏈疄鐜?| 涓嶅湪褰撳墠鐗堟湰鑼冨洿鍐?|

## 娉ㄦ剰浜嬮」

1. **鏁版嵁搴撳啓鍏ヨ寖鍥?*: 浠呭啓 `fpga_boards` 琛?(`status` + `last_heartbeat`), **涓嶅啓 `users` 琛?* (鏃?`used_times` 鍙樻洿), 涓嶅啓 `experiment_results`
2. **鍘熷瓙浜掓枼**: 鐑у綍鍓嶆爣璁?`status='in_use'` + 鍚姩蹇冭烦, 鍘熺▼搴忕敤鎴锋棤娉曟姠鍗犲悓涓€鏉垮崱
3. **宕╂簝鎭㈠**: 杩涚▼宕╂簝 鈫?蹇冭烦鍋滄 鈫?3 鍒嗛挓鍚?smart query 鑷姩鍥炴敹
4. **姝ｅ父閲婃斁**: 鐑у綍鎴愬姛鎴栧け璐ラ兘浼氬湪 `finally` 涓噴鏀?(`status='available'`)
5. **hw_server 鑷姩鍥炴敹**: `HwServerSession` 涓婁笅鏂囩鐞嗗櫒纭繚 hw_server 鍦ㄧ儳褰曞畬鎴愬悗鑷姩缁堟, 鏃犻渶鎵嬪姩绠＄悊
6. **PS1 鑴氭湰閮ㄧ讲**: 棣栨浣跨敤浼氳嚜鍔ㄥ皢 PS1 鑴氭湰閮ㄧ讲鍒?FPGA 鏉垮崱鐨?`C:\Temp\hw_script\`, 鍚庣画浣跨敤浼氳烦杩?7. **FPGA 鏉垮崱蹇呴』鏈?Vivado 2023.2 瀹夎鍦?`D:\vivado\Vivado\2023.2\`**
8. **鍑嵁浼樺厛绾?*: CLI 鍙傛暟 > secret.py
