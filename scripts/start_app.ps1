$ErrorActionPreference = "Stop"

# API とフロントエンドをまとめて起動する開発用スクリプト。
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
$nodeModules = Join-Path $frontendDir "node_modules"

if (-not (Test-Path $backendEnv) -and (Test-Path $backendEnvExample)) {
    Copy-Item $backendEnvExample $backendEnv
    Write-Host "Created .env from .env.example"
}

if (-not (Test-Path $frontendEnv) -and (Test-Path $frontendEnvExample)) {
    Copy-Item $frontendEnvExample $frontendEnv
    Write-Host "Created frontend/.env from frontend/.env.example"
}

if (-not (Test-Path $nodeModules)) {
    Write-Host "frontend/node_modules がありません。初回だけ以下を実行してください。" -ForegroundColor Yellow
    Write-Host "cd $frontendDir"
    Write-Host "npm install"
    exit 1
}

Write-Host "API:      http://127.0.0.1:8000"
Write-Host "Docs:     http://127.0.0.1:8000/docs"
Write-Host "Frontend: http://127.0.0.1:5173"
Write-Host ""
Write-Host "停止するときは Ctrl + C を押してください。"
Write-Host ""

function Wait-HttpOk {
    param(
        [string]$Url,
        [int]$TimeoutSeconds = 60
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -UseBasicParsing $Url -TimeoutSec 2
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                return
            }
        } catch {
            Start-Sleep -Milliseconds 500
        }
    }

    throw "$Url の起動確認がタイムアウトしました。"
}

$apiJob = $null
$frontendJob = $null

try {
    $apiJob = Start-Job -Name "local-rag-api" -ScriptBlock {
        param($root)
        Set-Location $root
        python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
    } -ArgumentList $projectRoot

    $frontendJob = Start-Job -Name "local-rag-frontend" -ScriptBlock {
        param($root)
        Set-Location (Join-Path $root "frontend")
        npm.cmd run dev -- --host 127.0.0.1
    } -ArgumentList $projectRoot

    Write-Host "API の起動を確認しています..."
    Wait-HttpOk "http://127.0.0.1:8000/health"

    Write-Host "フロントエンドの起動を確認しています..."
    Wait-HttpOk "http://127.0.0.1:5173"

    Start-Process "http://127.0.0.1:5173"

    while ($true) {
        foreach ($job in @($apiJob, $frontendJob)) {
            if ($job -and $job.State -ne "Running") {
                $previousErrorActionPreference = $ErrorActionPreference
                $ErrorActionPreference = "Continue"
                Receive-Job $job -ErrorAction Continue
                $ErrorActionPreference = $previousErrorActionPreference
                throw "$($job.Name) stopped with state $($job.State)."
            }
        }
        Start-Sleep -Milliseconds 500
    }
}
finally {
    foreach ($job in @($apiJob, $frontendJob)) {
        if ($job) {
            Stop-Job $job -ErrorAction SilentlyContinue
            Remove-Job $job -Force -ErrorAction SilentlyContinue
        }
    }
    Write-Host "停止しました。"
}
