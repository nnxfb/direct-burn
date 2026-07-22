# secret.example.py 鈥?鍑嵁閰嶇疆妯℃澘
# 澶嶅埗涓?secret.py 骞跺～鍏ュ疄闄呭€?
#   cp direct_burn/secret.example.py direct_burn/secret.py
# secret.py 宸插湪 .gitignore 涓? 鍙畨鍏ㄦ彁浜ゅ埌鍏紑浠撳簱

# --- SSH 鍑嵁 (杩滅▼ FPGA 鏉垮崱) ---
SSH_PORT = 22
SSH_USER = 'your_username'
SSH_PASSWORD = 'your_password'

# --- MySQL 鍑嵁 (FPGA 鐘舵€佹暟鎹簱) ---
DB_HOST = '192.168.1.100'
DB_PORT = 3306
DB_USER = 'root'
DB_PASSWORD = 'your_password'

# --- Vivado 宸ュ叿閾捐矾寰?(杩滅▼鏉垮崱涓婄殑瀹夎璺緞) ---
VIVADO_BAT = 'D:/vivado/Vivado/2023.2/bin/vivado.bat'
HW_SERVER_BAT = 'D:/vivado/Vivado/2023.2/bin/hw_server.bat'

# --- 杩滅▼涓存椂鐩綍 ---
REMOTE_TEMP = 'C:/Temp/hw_script'
