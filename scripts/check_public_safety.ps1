$ErrorActionPreference = "Stop"
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

# GitHub に push する前に、個人用 knowledge やローカル生成物が追跡されていないか確認する。
$trackedFiles = git ls-files

$blockedPatterns = @(
    "^knowledge/(?!sample/)",
    "^data/",
    "^\.env$",
    "^README3\.md$",
    "^AGENT\.md$",
    "__pycache__",
    "\.pyc$",
    "^frontend/\.env$",
    "^frontend/dist/",
    "^frontend/node_modules/"
)

$violations = foreach ($file in $trackedFiles) {
    foreach ($pattern in $blockedPatterns) {
        if ($file -match $pattern) {
            $file
            break
        }
    }
}

if ($violations) {
    Write-Host "Unsafe tracked files detected:" -ForegroundColor Red
    $violations | Sort-Object -Unique
    exit 1
}

$textFilePatterns = @(
    "\.css$",
    "\.env$",
    "\.example$",
    "\.html$",
    "\.js$",
    "\.json$",
    "\.md$",
    "\.ps1$",
    "\.py$",
    "\.ts$",
    "\.tsx$",
    "\.txt$",
    "\.yml$",
    "\.yaml$",
    "^requirements\.txt$",
    "^\.editorconfig$",
    "^\.gitignore$"
)

$utf8Strict = [System.Text.UTF8Encoding]::new($false, $true)
$mojibakeChars = @(
    0x7E1D,
    0x7E3A,
    0x8B41,
    0x879F,
    0x8373,
    0x8708,
    0x90B1,
    0x9015,
    0x9B18,
    0x9A5B,
    0x9AF1,
    0x83A8,
    0x873F,
    0x8C3F,
    0x8757,
    0x9695,
    0x8811,
    0x8815,
    0x8C82,
    0x83EB,
    0x8B80,
    0x87B3,
    0x86F9,
    0x87C6,
    0x9052
)
$mojibakePattern = ($mojibakeChars | ForEach-Object { [regex]::Escape([char]$_) }) -join "|"
$encodingViolations = @()
$mojibakeViolations = @()

foreach ($file in $trackedFiles) {
    $isTextFile = $false
    foreach ($pattern in $textFilePatterns) {
        if ($file -match $pattern) {
            $isTextFile = $true
            break
        }
    }

    if (-not $isTextFile -or -not (Test-Path $file)) {
        continue
    }

    $bytes = [System.IO.File]::ReadAllBytes((Resolve-Path $file))
    try {
        $text = $utf8Strict.GetString($bytes)
    } catch {
        $encodingViolations += $file
        continue
    }

    if ($text -match $mojibakePattern) {
        $mojibakeViolations += $file
    }
}

if ($encodingViolations) {
    Write-Host "Non UTF-8 tracked text files detected:" -ForegroundColor Red
    $encodingViolations | Sort-Object -Unique
    exit 1
}

if ($mojibakeViolations) {
    Write-Host "Possible mojibake detected in tracked text files:" -ForegroundColor Red
    $mojibakeViolations | Sort-Object -Unique
    exit 1
}

Write-Host "Public safety check passed." -ForegroundColor Green
