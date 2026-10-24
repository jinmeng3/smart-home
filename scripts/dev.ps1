# 同时启动后端 (uvicorn) 与前端 (vite)，按 Ctrl+C 一起退出。
# 用法：在项目根目录执行 ./scripts/dev.ps1
# 默认使用 Bash + dev.sh；如果 Git Bash 可用则走 bash 路径，否则降级为分别启动两个新进程。

$ErrorActionPreference = "Stop"

$RootDir   = Split-Path -Parent $PSScriptRoot
$ApiDir    = Join-Path $RootDir "smarthome-api"
$WebDir    = Join-Path $RootDir "smarthome-web"
$ShScript  = Join-Path $RootDir "scripts/dev.sh"

function Test-BashAvailable {
    $candidates = @("bash", "C:\Program Files\Git\bin\bash.exe", "C:\Program Files\Git\usr\bin\bash.exe")
    foreach ($p in $candidates) {
        if (Get-Command $p -ErrorAction SilentlyContinue) { return $p }
    }
    return $null
}

$bash = Test-BashAvailable
if ($bash) {
    Write-Host "[dev.ps1] 使用 $bash 运行 dev.sh"
    & $bash $ShScript
    exit $LASTEXITCODE
}

Write-Host "[dev.ps1] 未找到 bash，分别启动后端与前端 (按 Ctrl+C 仅终止当前前台进程)"

# 后端
$backend = Start-Process -FilePath "python" `
    -ArgumentList @("-m", "uvicorn", "app.main:app", "--reload", "--host", "127.0.0.1", "--port", "8000") `
    -WorkingDirectory $ApiDir `
    -PassThru

# 前端
$frontend = Start-Process -FilePath "npm" `
    -ArgumentList @("run", "dev") `
    -WorkingDirectory $WebDir `
    -PassThru

Write-Host "[dev.ps1] 后端 PID=$($backend.Id)  前端 PID=$($frontend.Id)"

try {
    Wait-Process -Id @($backend.Id, $frontend.Id) -ErrorAction SilentlyContinue
} finally {
    Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $frontend.Id -Force -ErrorAction SilentlyContinue
}