# LinguaMiner 中文学习版
# 本版使用下载 ZIP 后双击 install.bat 的安装方式，避免旧入口克隆原版。
# 在解压后的源码目录执行此文件，也会调用同一安装程序。
$ErrorActionPreference = "Stop"
if (-not $PSScriptRoot -or -not (Test-Path (Join-Path $PSScriptRoot "install.ps1"))) {
    throw "请下载中文版源码 ZIP 并完整解压，然后双击 install.bat；不要使用原版的远程安装命令。"
}
& (Join-Path $PSScriptRoot "install.ps1")
if ($LASTEXITCODE -ne 0) {
    throw "安装未完成，请保留上方错误信息，在中文版仓库 issues 页面反馈。"
}
