# -*- coding: utf-8 -*-
"""
一次性设置辅助：读取 `cloudflared tunnel list`，找出名为 riue-survey 的隧道，
取出其固定 UUID，写出：
  tunnel_name.txt -> "riue-survey"
  tunnel_url.txt  -> "https://<uuid>.cfargotunnel.com"
"""
import subprocess
import re
import sys

try:
    out = subprocess.run(
        ["cloudflared", "tunnel", "list"],
        capture_output=True, text=True, timeout=30
    ).stdout
except Exception as e:
    print("执行 cloudflared tunnel list 失败：", e, file=sys.stderr)
    sys.exit(1)

m = re.search(
    r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\s+riue-survey",
    out,
)
if not m:
    print("未找到名为 riue-survey 的隧道。cloudflared tunnel list 输出如下：", file=sys.stderr)
    print(out, file=sys.stderr)
    sys.exit(1)

tid = m.group(1)
url = f"https://{tid}.cfargotunnel.com"
with open("tunnel_name.txt", "w", encoding="utf-8") as f:
    f.write("riue-survey")
with open("tunnel_url.txt", "w", encoding="utf-8") as f:
    f.write(url)
print("固定地址已保存：", url)
