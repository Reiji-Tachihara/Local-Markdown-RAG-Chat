$ErrorActionPreference = "Stop"

# Project root is one directory above this scripts directory.
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

$nodeDir = Join-Path $projectRoot ".tools\nodejs"
$webDir = Join-Path $projectRoot "web"

if (-not (Test-Path (Join-Path $nodeDir "node.exe"))) {
    Write-Error "Node.js was not found at $nodeDir. Run the Node.js setup step first."
}

$env:Path = "$nodeDir;$env:Path"

Set-Location $webDir

if (-not (Test-Path "node_modules")) {
    npm.cmd install
}

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
}

npm.cmd run dev
