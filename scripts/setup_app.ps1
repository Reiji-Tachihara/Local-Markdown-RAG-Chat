$ErrorActionPreference = "Stop"

# 初回セットアップ用スクリプト。
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

$frontendDir = Join-Path $projectRoot "frontend"
$backendEnv = Join-Path $projectRoot ".env"
$backendEnvExample = Join-Path $projectRoot ".env.example"
$frontendEnv = Join-Path $frontendDir ".env"
$frontendEnvExample = Join-Path $frontendDir ".env.example"

Set-Location $projectRoot

if (-not (Test-Path $backendEnv) -and (Test-Path $backendEnvExample)) {
    Copy-Item $backendEnvExample $backendEnv
    Write-Host "Created .env from .env.example"
}

if (-not (Test-Path $frontendEnv) -and (Test-Path $frontendEnvExample)) {
    Copy-Item $frontendEnvExample $frontendEnv
    Write-Host "Created frontend/.env from frontend/.env.example"
}

Write-Host "Installing Python dependencies..."
python -m pip install -r requirements.txt

Write-Host "Installing frontend dependencies..."
Set-Location $frontendDir
npm.cmd install

Set-Location $projectRoot

if (Get-Command ollama -ErrorAction SilentlyContinue) {
    Write-Host "Pulling Ollama models..."
    ollama pull qwen3:8b
    ollama pull nomic-embed-text
} else {
    Write-Host "Ollama コマンドが見つかりません。Ollama をインストール後、以下を実行してください。" -ForegroundColor Yellow
    Write-Host "ollama pull qwen3:8b"
    Write-Host "ollama pull nomic-embed-text"
}

Write-Host ""
Write-Host "セットアップが完了しました。起動するには以下を実行してください。"
Write-Host "powershell.exe -ExecutionPolicy Bypass -File .\scripts\start_app.ps1"
