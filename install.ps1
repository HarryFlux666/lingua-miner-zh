# LinguaMiner 中文学习版：在所选安装目录准备 Python、依赖和离线资源。
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$env:PYTHONIOENCODING = "utf-8"
if (-not $env:LINGUAMINER_DIR) { $env:LINGUAMINER_DIR = Join-Path $PSScriptRoot "data" }
$Runtime = Join-Path $PSScriptRoot ".runtime"
$env:UV_CACHE_DIR = Join-Path $Runtime "uv-cache"
$env:UV_PYTHON_INSTALL_DIR = Join-Path $Runtime "python"
$env:UV_INSTALL_DIR = Join-Path $Runtime "bin"
$env:UV_NO_MODIFY_PATH = "1"
$env:TEMP = Join-Path $env:LINGUAMINER_DIR "tmp"
$env:TMP = $env:TEMP
New-Item -ItemType Directory -Force -Path $Runtime,$env:TEMP | Out-Null
$env:PATH = "$env:UV_INSTALL_DIR;$env:PATH"

function Assert-Ok([string]$What) {
    if ($LASTEXITCODE -ne 0) {
        throw "$What 失败（退出代码 $LASTEXITCODE）；请保留错误信息，在本仓库 issues 页面反馈。"
    }
}

Write-Host "== LinguaMiner 中文学习版安装 =="
Write-Host "数据目录：$env:LINGUAMINER_DIR"
Write-Host "首次安装需要联网下载资源；完成后本地视频、词典和字幕识别可离线使用。"
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "正在准备 Python 安装工具……"
    Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) { throw "uv 安装未完成，请检查网络后重试。" }
}
if (-not (Test-Path .venv\Scripts\python.exe)) {
    uv venv --python 3.12 .venv
    Assert-Ok "创建 Python 环境"
}
uv sync --frozen --no-dev
Assert-Ok "安装项目依赖"
Write-Host "正在安装英语语言模型……"
uv pip install -p .venv\Scripts\python.exe https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl
Assert-Ok "安装英语语言模型"
.\.venv\Scripts\python.exe -m app.setup_zh
Assert-Ok "准备离线资源"
.\.venv\Scripts\python.exe -c "from app.main import app"
Assert-Ok "检查应用启动"
try {
    $StartDir = [Environment]::GetFolderPath('StartMenu')
    $Shell = New-Object -ComObject WScript.Shell
    $Sc = $Shell.CreateShortcut((Join-Path $StartDir "Programs\LinguaMiner 中文学习版.lnk"))
    $Sc.TargetPath = Join-Path $PSScriptRoot "run.bat"
    $Sc.WorkingDirectory = $PSScriptRoot
    $Sc.IconLocation = Join-Path $PSScriptRoot "assets\AppIcon.ico"
    $Sc.Description = "看英语视频、查中文释义"
    $Sc.Save()
} catch { Write-Warning "快捷方式创建失败，仍可双击 run.bat 启动。" }
Write-Host "安装完成！双击 run.bat，或从开始菜单打开 LinguaMiner 中文学习版。"
