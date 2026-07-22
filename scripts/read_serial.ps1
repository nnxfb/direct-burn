param(
    $ComPort,
    $BaudRate = 9600,
    $Duration = 30
)

# .NET System.IO.Ports.SerialPort — 主动查询 FPGA 状态
# 协议: 发送 0x80 → 读取 18 字节 LE 响应 → 输出 hex 行
# 每行 18 个空格分隔的 hex 字节, 最后一行 "DONE"

$port = New-Object System.IO.Ports.SerialPort $ComPort, $BaudRate, 'None', 8, 'One'
$port.ReadTimeout = 2000
$port.Open()

$cmd = [byte]0x80
$end = (Get-Date).AddSeconds($Duration)

while ((Get-Date) -lt $end) {
    # 发送查询命令
    $port.Write($cmd, 0, 1)

    # 读取 18 字节响应
    $buffer = New-Object byte[] 18
    $bytesRead = 0
    while ($bytesRead -lt 18) {
        try {
            $n = $port.Read($buffer, $bytesRead, 18 - $bytesRead)
            $bytesRead += $n
        } catch {
            break
        }
    }

    if ($bytesRead -eq 18) {
        $hex = ($buffer[0..17] | ForEach-Object { $_.ToString('X2') }) -join ' '
        Write-Output $hex
    }

    Start-Sleep -Milliseconds 100
}

$port.Close()
Write-Output 'DONE'
