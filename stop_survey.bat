@echo off
setlocal
chcp 65001 >nul 2>&1
cd /d "%~dp0"

REM ============================================================
REM  RIUE 问卷 - 停止服务（双击即可，干净退出）
REM  按命令行精确结束隧道 ssh.exe 与后端 server.py，不误伤其他进程
REM  括号内均为 wmic 查询条件（位于双引号内，cmd 视为字面文本，安全）
REM ============================================================

echo 正在停止问卷服务与隧道...

REM 精确结束隧道进程（系统 SSH 起的 localhost.run / pinggy.io）
wmic process where "name='ssh.exe' and (commandline like '%%localhost.run%%' or commandline like '%%pinggy.io%%')" call terminate >nul 2>nul

REM 精确结束后端 server.py 进程
wmic process where "name='python.exe' and commandline like '%%server.py%%'" call terminate >nul 2>nul

echo 已停止。可安全关闭所有窗口。
pause
endlocal
