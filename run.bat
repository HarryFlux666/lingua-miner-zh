@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not defined LINGUAMINER_DIR set "LINGUAMINER_DIR=%~dp0data"
set "PYTHONIOENCODING=utf-8"
if not exist ".venv\Scripts\python.exe" (
  echo 请先双击 install.bat 完成安装。
  pause
  exit /b 1
)
start "" /b cmd /c "timeout /t 2 >nul & start http://localhost:8977"
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8977
if errorlevel 1 (
  echo 启动失败，请检查是否已经打开本软件，并保留上方错误信息。
  pause
)
