# -*- coding: utf-8 -*-
"""
从隧道日志里解析出公网地址并写入 captured_url.txt。
支持 cloudflared (*.trycloudflare.com / *.cfargotunnel.com) 与
localhost.run 系统自带 SSH 隧道 (*.lhr.life，零下载)。
用法： python capture_url.py <日志文件>
"""
import sys
import re
import time
import os

LOG = sys.argv[1] if len(sys.argv) > 1 else "tunnel.log"
PATTERN = re.compile(
    r"https://[A-Za-z0-9\-]+\.(?:trycloudflare|cfargotunnel)\.com"
    r"|https://[A-Za-z0-9\-]+\.lhr\.life"
    r"|https://[A-Za-z0-9\-]+\.run\.pinggy-free\.link"
    r"|https://[A-Za-z0-9\-]+\.free\.pinggy\.net"
    r"|https://[A-Za-z0-9\-]+\.a\.pinggy\.(?:io|link)"
)

out = ""
for _ in range(20):  # 最多等 20 秒
    try:
        with open(LOG, encoding="utf-8", errors="ignore") as f:
            out = f.read()
    except FileNotFoundError:
        out = ""
    m = PATTERN.search(out)
    if m:
        url = m.group(0)
        with open("captured_url.txt", "w", encoding="utf-8") as f:
            f.write(url)
        print(url)
        sys.exit(0)
    time.sleep(1)

print("TIMEOUT: 未在日志中解析到公网地址", file=sys.stderr)
sys.exit(1)
