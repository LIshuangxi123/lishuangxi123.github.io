# 重建源索引（Windows 版，和 build.sh 等价）
$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

# 让中文输出不乱码
try {
    [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
    $env:PYTHONIOENCODING = "utf-8"
} catch { }

$patterns = @(
    (Join-Path $env:LOCALAPPDATA "Programs\Python\Python3*\python.exe"),
    (Join-Path $env:ProgramFiles "Python3*\python.exe"),
    (Join-Path ${env:ProgramFiles(x86)} "Python3*\python.exe")
)

$py = $null
$pyArgs = @()

foreach ($pattern in $patterns) {
    $hit = Get-ChildItem -Path $pattern -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($hit) {
        $py = $hit.FullName
        break
    }
}

if (-not $py) {
    foreach ($name in @("python3", "python")) {
        $found = Get-Command $name -ErrorAction SilentlyContinue
        if ($found) {
            $py = $found.Source
            break
        }
    }
}

if (-not $py) {
    $launcher = Get-Command py -ErrorAction SilentlyContinue
    if ($launcher) {
        $py = $launcher.Source
        $pyArgs = @("-3")
    }
}

if (-not $py) {
    Write-Host "找不到 Python，请先安装：https://www.python.org/downloads/" -ForegroundColor Red
    exit 1
}

& $py @pyArgs (Join-Path $PSScriptRoot "tools\mkindex.py") @args
