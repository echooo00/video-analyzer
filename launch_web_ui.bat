@echo off
chcp 65001 >nul
title 视频分析工具

:: 查找 Python（优先 conda base，其次 PATH 中的 python）
set PYTHON=
for %%p in (
    "E:\anaconda\python.exe"
    "C:\Users\%USERNAME%\anaconda3\python.exe"
    "C:\ProgramData\anaconda3\python.exe"
) do (
    if exist %%p set PYTHON=%%p && goto :found_python
)
:: 最后尝试 PATH 中的 python
where python >nul 2>&1
if %ERRORLEVEL%==0 (set PYTHON=python) else goto :no_python

:found_python
echo 正在启动视频分析工具...
echo.

:: 设置 UTF-8 编码
set PYTHONIOENCODING=utf-8

:: 启动 Web UI
%PYTHON% -m video_analyzer.web_ui

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================
    echo 启动失败！
    echo.
    echo 请检查：
    echo 1. 是否已安装: pip install video-analyzer
    echo 2. API Key 是否配置: %%USERPROFILE%%\.video_analyzer\.env
    echo ========================================
    pause
)
exit /b 0

:no_python
echo 错误: 未找到 Python 安装
echo 请先安装 Python 或 Anaconda:
echo https://www.python.org/downloads/
pause
exit /b 1
