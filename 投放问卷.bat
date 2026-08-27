@echo off
setlocal
chcp 65001 >nul 2>&1
cd /d "%~dp0"

REM ============================================================
REM  RIUE 问卷 - 一键投放（纯双击，零下载，零命令行）
REM  双击本文件即可：起后端 -> 起公网隧道 -> 自动重指二维码/海报 -> 打开成品
REM  隧道用 Windows 自带 SSH + 公网转发（优先 pinggy.io 443端口，更稳；失败兜底 localhost.run）
REM  收集期间请保持本窗口与电脑开机；结束请双击 stop_survey.bat
REM  本脚本刻意不使用任何 if/for 括号代码块，避免 ") was unexpected" 错误
REM ============================================================

set "ADMIN_PASSWORD=137997953@"
set "PORT=8787"
set "TUNNEL_LOG=tunnel.log"
set "CAPTURED=captured_url.txt"

REM ===== Python 路径：优先 WorkBuddy 管理版（已带 segno），否则系统 python / py =====
set "PY=C:\Users\ASUS\.workbuddy\binaries\python\envs\default\Scripts\python.exe"
if not exist "%PY%" set "PY=C:\Users\ASUS\.workbuddy\binaries\python\versions\3.13.12\python.exe"
if not exist "%PY%" set "PY=py"
if not exist "%PY%" set "PY=python"

REM ===== 检查二维码依赖 segno =====
"%PY%" -c "import segno" >nul 2>&1
if errorlevel 1 "%PY%" -m pip install segno >nul 2>&1

echo ===================================================
echo   RIUE 问卷 - 一键投放
echo ===================================================

REM ===== [1/3] 启动问卷后端 =====
echo [1/3] 启动问卷后端 server.py ...
start /B "" "%PY%" "%~dp0server.py" > "%~dp0server.log" 2>&1
ping -n 3 127.0.0.1 >nul 2>&1
"%PY%" -c "import urllib.request;urllib.request.urlopen('http://localhost:%PORT%/healthz',timeout=3)" >nul 2>&1
if errorlevel 1 goto BACKEND_WARN
echo   [OK] 后端已启动 地址 http://localhost:%PORT%
goto STEP2

:BACKEND_WARN
echo   [警告] 后端未响应，将仍尝试起隧道，详见 server.log
goto STEP2

REM ===== [2/3] 启动公网隧道（优先 pinggy.io 443端口，更稳）=====
:STEP2
echo [2/3] 启动公网隧道（系统自带 SSH，无需下载）...
where ssh >nul 2>&1
if errorlevel 1 goto SSH_FAIL

del /q "%~dp0%TUNNEL_LOG%" 2>nul
del /q "%~dp0%CAPTURED%" 2>nul
echo. > "%~dp0%TUNNEL_LOG%"
start /B "" ssh -p 443 -o StrictHostKeyChecking=no -o UserKnownHostsFile=nul -o ServerAliveInterval=30 -R 0:localhost:%PORT% a.pinggy.io > "%~dp0%TUNNEL_LOG%" 2>&1
echo   正在连接 pinggy.io ...
call :GET_URL
if not "%URL%"=="" goto TUNNEL_OK
goto TUNNEL_FALLBACK

REM ===== 兜底：localhost.run（pinggy 连不上时）=====
:TUNNEL_FALLBACK
echo   pinggy.io 未成功，自动改用 localhost.run ...
taskkill /f /im ssh.exe >nul 2>&1
del /q "%~dp0%TUNNEL_LOG%" 2>nul
echo. > "%~dp0%TUNNEL_LOG%"
start /B "" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=nul -o ServerAliveInterval=30 -R 80:localhost:%PORT% nokey@localhost.run > "%~dp0%TUNNEL_LOG%" 2>&1
echo   正在连接 localhost.run ...
call :GET_URL
if not "%URL%"=="" goto TUNNEL_OK
goto TUNNEL_FAIL

REM ===== 用 capture_url.py 健壮提取公网地址，并严格校验 =====
:GET_URL
set "URL="
"%PY%" "%~dp0capture_url.py" "%~dp0%TUNNEL_LOG%" >nul 2>&1
if exist "%~dp0%CAPTURED%" (
  set /p URL=<"%~dp0%CAPTURED%"
)
if "%URL%"=="" goto :EOF
echo %URL% | findstr /i "https://" >nul 2>&1
if errorlevel 1 set "URL="
echo %URL% | findstr /i "lhr.life pinggy" >nul 2>&1
if errorlevel 1 set "URL="
goto :EOF

REM ===== [3/3] 生成二维码/海报并打开 =====
:TUNNEL_OK
echo   [OK] 隧道已建立： %URL%
echo [3/3] 已拿到公网地址，正在生成二维码/海报 ...
"%PY%" "%~dp0set_links.py" "%URL%"
if errorlevel 1 (
  echo 警告: 二维码自动生成失败（请确认 Python/segno 正常），但公网地址本身可用：
  echo   %URL%
  echo   你可手动在手机浏览器打开该地址填写；后台为 %URL%/admin
) else (
  echo   二维码与海报已生成
)
echo.
echo ===================================================
echo   问卷页  ： %URL%
echo   管理后台： %URL%/admin
echo   后台密码： %ADMIN_PASSWORD%
echo ===================================================
echo 正在打开问卷页与二维码图片 ...
start "" "%URL%"
start "" "%~dp0RIUE问卷二维码.png"
start "" "%~dp0RIUE问卷海报_v5.svg"
echo.
echo 保持本窗口与电脑开机；结束请双击 stop_survey.bat
echo.

:KEEP
ping -n 31 127.0.0.1 >nul 2>&1
REM 保活：检查后端是否还活着，不在则重启
"%PY%" -c "import urllib.request;urllib.request.urlopen('http://localhost:%PORT%/healthz',timeout=3)" >nul 2>&1
if errorlevel 1 goto RESTART_BACKEND
REM 保活：检查隧道 ssh 进程是否还在，不在则自动重连
tasklist | findstr /i "ssh.exe" >nul 2>&1
if errorlevel 1 goto RECONNECT
goto KEEP

:RESTART_BACKEND
echo [保活] 后端未响应，尝试重启 server.py ...
start /B "" "%PY%" "%~dp0server.py" > "%~dp0server.log" 2>&1
goto KEEP

:RECONNECT
echo [保活] 隧道已断开，正在自动重连 ...
goto STEP2

REM ===== 错误处理 =====
:SSH_FAIL
echo 错误: 系统中未找到 ssh 命令。
echo 安装方法: 开始菜单 - 设置 - 应用 - 可选功能 - 添加功能 - 安装 OpenSSH 客户端。
pause
goto END

:TUNNEL_FAIL
echo 错误: 两次隧道都没连上。
echo 常见原因: 1) 电脑未联网；2) 网络屏蔽了 SSH 出站（公司/校园网很常见）。
echo 建议: 先连手机热点再试；或改用稳定的腾讯问卷（RIUE问卷_腾讯问卷二维码.png）。
echo.
echo 隧道日志如下，可截图发我排查:
echo --------------------------------------------------
type "%~dp0%TUNNEL_LOG%" 2>nul
echo --------------------------------------------------
pause
goto END

:END
endlocal
