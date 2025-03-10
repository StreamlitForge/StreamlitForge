@echo off
echo ========================================
echo    {app_name} - 启动器
echo ========================================
echo.

setlocal enabledelayedexpansion

:: 设置颜色
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "RESET=[0m"

echo %GREEN%正在检查系统环境...%RESET%
echo.

:: 检查 Python 是否已安装
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo %YELLOW%未检测到 Python，将尝试安装...%RESET%
    
    :: 下载 Python 安装程序
    echo 正在下载 Python 安装程序...
    
    :: 使用 PowerShell 下载 Python
    powershell -Command "& {{Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.10.0/python-3.10.0-amd64.exe' -OutFile 'python-installer.exe'}}"
    
    if not exist "python-installer.exe" (
        echo %RED%Python 安装程序下载失败。%RESET%
        echo 请访问 https://www.python.org/downloads/ 手动安装 Python 3.7+ 后再运行此启动器。
        pause
        exit /b 1
    )
    
    echo %YELLOW%正在安装 Python...%RESET%
    echo 请按照安装向导完成 Python 安装，并确保勾选 "Add Python to PATH" 选项。
    
    :: 运行安装程序
    start /wait python-installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    
    :: 清理
    del /q python-installer.exe
    
    :: 检查安装是否成功
    where python >nul 2>&1
    if %errorlevel% neq 0 (
        echo %RED%Python 安装可能未成功完成。%RESET%
        echo 请访问 https://www.python.org/downloads/ 手动安装 Python 3.7+ 后再运行此启动器。
        pause
        exit /b 1
    )
    
    echo %GREEN%Python 安装成功！%RESET%
)

:: 获取当前目录
set "APP_DIR=%~dp0"
cd "%APP_DIR%"

:: 创建并激活虚拟环境
if not exist "venv" (
    echo %YELLOW%正在创建Python虚拟环境...%RESET%
    python -m venv venv
) else (
    echo %GREEN%检测到已存在的虚拟环境。%RESET%
)

:: 激活虚拟环境
call venv\\Scripts\\activate.bat

if %errorlevel% neq 0 (
    echo %RED%虚拟环境激活失败！%RESET%
    pause
    exit /b 1
)

echo %GREEN%已激活虚拟环境。%RESET%
echo.

:: 安装依赖
echo %YELLOW%正在安装依赖...%RESET%
python -m pip install --upgrade pip
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo %RED%依赖安装失败！%RESET%
    pause
    exit /b 1
)

echo %GREEN%依赖安装完成！%RESET%
echo.

:: 启动应用
echo %GREEN%正在启动 {app_name}...%RESET%
start "" http://localhost:8501
python -m streamlit run app.py

:: 结束
deactivate
endlocal
pause 