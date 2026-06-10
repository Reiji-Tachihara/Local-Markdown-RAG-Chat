$ErrorActionPreference = "Stop"

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
    "^web/\.env$",
    "^web/dist/",
    "^web/node_modules/"
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

Write-Host "Public safety check passed." -ForegroundColor Green
