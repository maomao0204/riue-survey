@echo off
chcp 65001 >nul
REM ============================================================
REM  RIUE 问卷 · 一键启动（自己电脑当服务器 + Cloudflare 隧道）
REM  无需 GitHub / 无需云账号。收集期间请保持本窗口与电脑开机。
REM ============================================================
setlocal
set PORT=8787

REM 管理后台密码（必填！客户看不到，只有你登录 /admin 看数据用）
REM 改成你自己的强密码，例如： set "ADMIN_PASSWORD=Riue@2026"
set "ADMIN_PASSWORD="

REM ---- 可选：固定公网地址（named tunnel）----
REM 留空 = 用 quick tunnel（每次地址随机，重启后需重指二维码）
REM 填隧道名 = 用固定地址（需先 cloudflared tunnel login 与 create，见 DEPLOY.md 第八节）
REM 例： set "TUNNEL_NAME=riue-survey"
set "TUNNEL_NAME="

REM 优先用 WorkBuddy 管理的 Python，否则回退到系统 python
set "PY=C:\Users\ASUS\.workbuddy\binaries\python\versions\3.13.12\python.exe"
if not exist "%PY%" set "PY=python"

echo [1/2] 启动问卷后端 server.py  (端口 %PORT%) ...
start "RIUE-Server" "%PY%" "%~dp0server.py"

timeout /t 2 >nul
echo [2/2] 通过 Cloudflare 隧道暴露公网地址（免费、无需账号）...

where cloudflared >nul 2>nul
if errorlevel 1 (
  echo.
  echo [警告] 未检测到 cloudflared。当前仅在本机运行，外网（客户手机）暂无法访问。
  echo   请下载 Windows 版： https://github.com/cloudflare/cloudflared/releases
  echo   取 cloudflared-windows-amd64.exe，重命名为 cloudflared.exe 放入 PATH，再重跑本脚本。
  echo.
  echo   本机预览地址： http://localhost:%PORT%/
  pause
  exit /b
)

echo.
if defined TUNNEL_NAME (
  echo 使用固定隧道 [%TUNNEL_NAME%]，地址固定不变，只需运行一次：
  echo   python set_links.py https://^<隧道ID^>.cfargotunnel.com
  echo （首次运行 cloudflared 会打印该固定地址，记下来即可）
  echo 按 Ctrl+C 停止隧道。
  echo.
  cloudflared tunnel run --url http://localhost:%PORT% %TUNNEL_NAME%
) else (
  echo 使用 quick tunnel（地址随机）。隧道启动后下方会显示 https://xxxx.trycloudflare.com
  echo 复制它，然后在本机运行：  python set_links.py https://xxxx.trycloudflare.com
  echo 即可重生成二维码/海报（重启后地址会变，需再指一次）。按 Ctrl+C 停止。
  echo.
  cloudflared tunnel --url http://localhost:%PORT%
)
