@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
REM ============================================================
REM  RIUE 问卷 · 一次性设置（固定公网地址 / named tunnel）
REM  只需运行【一次】。之后每天双击「投放问卷.bat」即可拿到永久不变地址。
REM ============================================================
echo ============================================================
echo   RIUE 问卷 · 一次性设置（固定公网地址）
echo   只需运行一次。之后每天双击「投放问卷.bat」。
echo ============================================================
echo.

where cloudflared >nul 2>nul || (
  echo [错误] 未检测到 cloudflared。请先下载：
  echo   https://github.com/cloudflare/cloudflared/releases
  echo   取 cloudflared-windows-amd64.exe 重命名为 cloudflared.exe 放入 PATH。
  pause & exit /b
)

echo [1/3] 登录 Cloudflare（将打开浏览器，免费账号即可，按提示完成授权）...
cloudflared tunnel login
if errorlevel 1 ( echo [错误] 登录失败。 & pause & exit /b )

echo.
echo [2/3] 创建固定隧道 riue-survey ...
cloudflared tunnel create riue-survey
echo.

echo [3/3] 记录固定地址 ...
"C:\Users\ASUS\.workbuddy\binaries\python\envs\default\Scripts\python.exe" setup_parse_url.py
if errorlevel 1 ( echo [错误] 解析固定地址失败，请检查上方 cloudflared 输出。 & pause & exit /b )

echo.
echo 完成！固定地址已存到 tunnel_url.txt：
type tunnel_url.txt
echo.
echo 以后每天只需双击「投放问卷.bat」即可（地址永久不变）。
pause
