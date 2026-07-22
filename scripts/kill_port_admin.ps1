param($Port)

$ownerPid = (Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue).OwningProcess |
            Where-Object { $_ -ne 0 } | Select-Object -First 1
if ($ownerPid) {
    taskkill /F /PID $ownerPid
    Write-Host "killed PID $ownerPid on port $Port"
} else {
    Write-Host "no process on port $Port"
}
