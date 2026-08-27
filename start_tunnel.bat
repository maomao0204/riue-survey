@echo off
setlocal
chcp 65001 >nul 2>&1

rem ===== 配置区（可按需修改）=====
set PORT=8787
set TUNNEL_LOG=tunnel.log
set MAX_WAIT=40

rem ===== 1. 检查网络连通性 =====
echo [1/3] 正在检查网络连通性...
ping -n 1 -w 3000 8.8.8.8 >nul 2>&1
if errorlevel 1 goto NET_FAIL

rem ===== 2. 检查系统自带 SSH 是否可用 =====
echo [2/3] 正在检查系统 SSH 客户端...
where ssh >nul 2>&1
if errorlevel 1 goto SSH_FAIL

rem ===== 3. 启动 localhost.run 公网隧道 =====
echo [3/3] 正在通过系统 SSH 连接 localhost.run 隧道 端口 %PORT% ...
echo. > "%TUNNEL_LOG%"
start "" /B ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=nul -o ServerAliveInterval=30 -R 80:localhost:%PORT% nokey@localhost.run > "%TUNNEL_LOG%" 2>&1

echo 正在等待隧道地址生成，最长 %MAX_WAIT% 秒...
set URL=
set COUNT=0

:WAIT_LOOP
set /a COUNT=COUNT+1
if %COUNT% gtr %MAX_WAIT% goto WAIT_TIMEOUT
for /f "tokens=7" %%u in ('findstr /i "lhr.life" "%TUNNEL_LOG%" 2^>nul') do set URL=%%u
if not "%URL%"=="" goto SHOW
for /f "tokens=1" %%u in ('findstr /i "pinggy.io" "%TUNNEL_LOG%" 2^>nul') do set URL=%%u
if not "%URL%"=="" goto SHOW
ping -n 2 127.0.0.1 >nul 2>&1
goto WAIT_LOOP

:SHOW
echo ==================================================
echo 公网隧道已成功建立
echo 问卷地址 : %URL%
echo 管理后台 : %URL%/admin
echo 隧道日志 : %TUNNEL_LOG%
echo ==================================================
echo 窗口保持打开以维持隧道；按 Ctrl+C 退出并关闭隧道。
echo.

:KEEP
ping -n 61 127.0.0.1 >nul 2>&1
goto KEEP

:NET_FAIL
echo 错误: 无法连通外部网络，请检查 Wi-Fi 或网线后重试。
pause
goto END

:SSH_FAIL
echo 错误: 系统中未找到 ssh 命令。
echo 安装方法: 开始菜单 - 设置 - 应用 - 可选功能 - 添加功能 - 安装 OpenSSH 客户端。
pause
goto END

:WAIT_TIMEOUT
echo 错误: %MAX_WAIT% 秒内未能获取公网地址，隧道可能连接失败。
echo 以下是隧道日志内容，方便排查:
echo --------------------------------------------------
type "%TUNNEL_LOG%"
echo --------------------------------------------------
pause
goto END

:END
endlocal
