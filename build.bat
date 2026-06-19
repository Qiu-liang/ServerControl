@echo off
chcp 65001 >nul
echo ========================================
echo   ServerControl 打包脚本
echo ========================================
echo.

REM 检查 PyInstaller 是否已安装
pyinstaller --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 PyInstaller，正在安装...
    pip install pyinstaller
    if errorlevel 1 (
        echo [错误] PyInstaller 安装失败，请检查网络连接
        pause
        exit /b 1
    )
)

echo [1/2] 开始打包 ServerControl...
echo.

pyinstaller ^
    --onefile ^
    --windowed ^
    --name "ServerControl" ^
    --add-data "config;config" ^
    --hidden-import "keyring.backends.windows" ^
    --hidden-import "paramiko.transport" ^
    --hidden-import "paramiko.channel" ^
    --hidden-import "cryptography.fernet" ^
    --noconfirm ^
    src/main.py

if errorlevel 1 (
    echo.
    echo [错误] 打包失败，请检查上方错误信息
    pause
    exit /b 1
)

echo.
echo [2/2] 打包成功！
echo.
echo 输出文件: dist\ServerControl.exe
echo.
echo 请将 dist\ServerControl.exe 和 config\commands.json
echo 一起分发给用户使用。
echo.
pause
