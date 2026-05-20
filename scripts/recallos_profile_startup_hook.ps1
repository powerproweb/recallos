# RecallOS startup health check
$recallosHealthPython = "C:\Users\Juan Jose.DESKTOP-1K9D47O\AppData\Local\Programs\Python\Python312\python.exe"
$recallosHealthScript = "M:\01_Warp_Projects\01_projects\10_recallos\scripts\check_recallos_health.py"
$recallosHealthLogDir = Join-Path $env:USERPROFILE ".recallos\logs"
$recallosHealthLog = Join-Path $recallosHealthLogDir "startup-health-check.log"
function Write-RecallosHealthLogSafely {
    param(
        [Parameter(Mandatory = $true)]
        [object[]]$Content,
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [int]$LockTimeoutMs = 3000
    )

    $mutexName = "Local\RecallOS_StartupHealthLog_Write"
    $mutex = [System.Threading.Mutex]::new($false, $mutexName)
    $lockAcquired = $false

    try {
        try {
            $lockAcquired = $mutex.WaitOne($LockTimeoutMs)
        } catch [System.Threading.AbandonedMutexException] {
            $lockAcquired = $true
        }

        if ($lockAcquired) {
            $Content | Out-File -FilePath $Path -Encoding utf8
            return $Path
        }

        $fallbackName = "startup-health-check.$PID.log"
        $fallbackPath = Join-Path ([System.IO.Path]::GetDirectoryName($Path)) $fallbackName
        $Content | Out-File -FilePath $fallbackPath -Encoding utf8
        Write-Warning "[RecallOS] startup-health-check.log busy, wrote to $fallbackPath"
        return $fallbackPath
    } finally {
        if ($lockAcquired) {
            $mutex.ReleaseMutex() | Out-Null
        }
        $mutex.Dispose()
    }
}

if ((Test-Path $recallosHealthPython) -and (Test-Path $recallosHealthScript)) {
    New-Item -ItemType Directory -Path $recallosHealthLogDir -Force -ErrorAction SilentlyContinue | Out-Null
    $oldPythonUtf8 = $env:PYTHONUTF8
    $oldPythonIoEncoding = $env:PYTHONIOENCODING
    try {
        $env:PYTHONUTF8 = "1"
        $env:PYTHONIOENCODING = "utf-8"
        $healthOutput = & $recallosHealthPython $recallosHealthScript --timeout 60 --json --auto-repair-mcp 2>&1
        $checkExitCode = $LASTEXITCODE
        [void](Write-RecallosHealthLogSafely -Content $healthOutput -Path $recallosHealthLog)
        if ($checkExitCode -eq 0) {
            Write-Host "[RecallOS] MCP+Vault health check: PASS" -ForegroundColor Green
        } else {
            Write-Warning "[RecallOS] MCP+Vault health check: FAIL (see $recallosHealthLog)"
        }
    } catch {
        Write-Warning "[RecallOS] Health check failed to run: $($_.Exception.Message)"
    } finally {
        if ($null -eq $oldPythonUtf8) {
            Remove-Item Env:PYTHONUTF8 -ErrorAction SilentlyContinue
        } else {
            $env:PYTHONUTF8 = $oldPythonUtf8
        }
        if ($null -eq $oldPythonIoEncoding) {
            Remove-Item Env:PYTHONIOENCODING -ErrorAction SilentlyContinue
        } else {
            $env:PYTHONIOENCODING = $oldPythonIoEncoding
        }
    }
} else {
    Write-Warning "[RecallOS] Health check skipped (missing python or script path)."
}
