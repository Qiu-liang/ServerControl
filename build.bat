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

echo [1/3] 清理旧的构建文件...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "ServerControl.spec" del /q "ServerControl.spec"
echo 完成
echo.

echo [2/3] 开始打包 ServerControl...
echo.

pyinstaller ^
    --onefile ^
    --windowed ^
    --name "ServerControl" ^
    --add-data "config;config" ^
    --add-data "assets;assets" ^
    --hidden-import "keyring.backends.windows" ^
    --hidden-import "keyring.backends.macOS" ^
    --hidden-import "keyring.backends.SecretService" ^
    --hidden-import "paramiko.transport" ^
    --hidden-import "paramiko.channel" ^
    --hidden-import "paramiko.ecdsakey" ^
    --hidden-import "paramiko.rsakey" ^
    --hidden-import "paramiko.dsskey" ^
    --hidden-import "cryptography.fernet" ^
    --hidden-import "cryptography.hazmat.primitives.ciphers" ^
    --hidden-import "cryptography.hazmat.primitives.kdf.pbkdf2" ^
    --noconfirm ^
    src/main.py

if errorlevel 1 (
    echo.
    echo [错误] 打包失败，请检查上方错误信息
    pause
    exit /b 1
)

echo.
echo [3/3] 打包成功！
echo.
echo 输出文件: dist\ServerControl.exe
echo.
echo 使用说明:
echo   1. 将 dist\ServerControl.exe 复制到目标机器
echo   2. 程序首次运行时会自动创建配置目录
echo   3. 预设命令已内置在程序中
echo.
pause
