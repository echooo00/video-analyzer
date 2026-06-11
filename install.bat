@echo off
chcp 65001 >nul
title 安装视频分析工具

echo ========================================
echo   视频分析工具 — 安装程序
echo ========================================
echo.

:: 查找 Python
set PYTHON=
for %%p in (
    "E:\anaconda\python.exe"
    "C:\Users\%USERNAME%\anaconda3\python.exe"
    "C:\ProgramData\anaconda3\python.exe"
) do (
    if exist %%p set PYTHON=%%p && goto :found_python
)
where python >nul 2>&1
if %ERRORLEVEL%==0 (set PYTHON=python) else goto :no_python

:found_python
echo [1/3] 安装 video-analyzer 包...
%PYTHON% -m pip install -e "%~dp0." --quiet
if %ERRORLEVEL% NEQ 0 (
    echo 安装失败，请检查 Python 环境和依赖。
    pause
    exit /b 1
)
echo   ✓ 安装完成

:: 创建配置目录和 .env
echo [2/3] 配置环境...
set CONFIG_DIR=%USERPROFILE%\.video_analyzer
if not exist "%CONFIG_DIR%" mkdir "%CONFIG_DIR%"
if not exist "%CONFIG_DIR%\.env" (
    if exist "%~dp0video_analyzer\.env" (
        copy "%~dp0video_analyzer\.env" "%CONFIG_DIR%\.env" >nul
        echo   ✓ 已复制配置文件到 %CONFIG_DIR%\.env
    ) else (
        echo   ! 未找到 .env 模板，请手动在 %CONFIG_DIR% 创建 .env 文件
    )
) else (
    echo   ✓ 配置文件已存在
)

:: 创建桌面快捷方式（使用 PowerShell 创建 .lnk）
echo [3/3] 创建桌面快捷方式...
set BAT_PATH=%~dp0launch_web_ui.bat
set DESKTOP=%USERPROFILE%\Desktop
set ICON_PATH=E:\anaconda\python.exe

powershell -NoProfile -Command ^
    "$WshShell = New-Object -ComObject WScript.Shell; " ^
    "$Shortcut = $WshShell.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\视频分析工具.lnk'); " ^
    "$Shortcut.TargetPath = '%BAT_PATH%'; " ^
    "$Shortcut.IconLocation = '%ICON_PATH%,0'; " ^
    "$Shortcut.WorkingDirectory = '%USERPROFILE%'; " ^
    "$Shortcut.Description = '本地视频内容识别与要点总结'; " ^
    "$Shortcut.Save(); " ^
    "Write-Host '  ✓ 桌面快捷方式已创建'"

echo.
echo ========================================
echo   安装完成！
echo.
echo   双击桌面 "视频分析工具" 即可启动
echo   配置文件: %CONFIG_DIR%\.env
echo ========================================
echo.
pause
exit /b 0

:no_python
echo 错误: 未找到 Python 安装
echo 请先安装 Python 或 Anaconda。
pause
exit /b 1
