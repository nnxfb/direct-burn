param(
    $Port,
    $Jtag,
    $TempDir,
    $HwServerBat
)

$logPath = "${TempDir}/${Jtag}_hw_server_exec_log.txt"
$batPath = "${TempDir}/${Jtag}_run_hw.bat"

function Write-Log {
    param([string]$msg)
    $line = "$((Get-Date).ToString('yyyy-MM-dd HH:mm:ss')) - $msg" 
    $line | Out-File $logPath -Append
    Write-Output $line
}

# 1. kill any existing process on the target port
try {
    $conns = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    if ($conns) {
        foreach ($c in $conns) {
            $p = Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue
            if ($p) {
                Write-Log "killing $($p.ProcessName) (PID=$($p.Id)) on port $Port"
                Stop-Process -Id $c.OwningProcess -Force
            }
        }
    }
} catch {
    Write-Log "port pre-check failed: $_"
}

# 2. generate .bat file with correct quoting (cmd.exe /c .bat approach bypasses escaping hell)
#    convert forward slashes to backslashes for cmd.exe compatibility
$hwBatWin = $HwServerBat -replace '/', '\'
@"
@"$hwBatWin" -s tcp::$Port -e "set jtag-port-filter $Jtag"
"@ | Out-File $batPath -Encoding ascii

Write-Log "generated $batPath"
Write-Log "bat content: @""$hwBatWin"" -s tcp::$Port -e ""set jtag-port-filter $Jtag"""
