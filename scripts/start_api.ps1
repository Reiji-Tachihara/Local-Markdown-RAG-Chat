$ErrorActionPreference = "Stop"

# プロジェクトルートは scripts ディレクトリの1階層上。
$scriptPath = $MyInvocation.MyCommand.Path
if (-not $scriptPath) {
    $scriptPath = $PSCommandPath
}

if ($scriptPath) {
    $scriptDir = Split-Path -Parent $scriptPath
    $projectRoot = Split-Path -Parent $scriptDir
} else {
    $projectRoot = (Get-Location).Path
}

Set-Location $projectRoot
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
