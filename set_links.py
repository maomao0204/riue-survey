# -*- coding: utf-8 -*-
"""
把二维码与海报的扫码目标改为最终部署地址，并重新生成。
用法：
  python set_links.py https://你的后端地址
例如部署到 Render 后：
  python set_links.py https://riue-survey.onrender.com
脚本会：
  1) 改写 gen_qr.py 里的 url
  2) 改写 gen_poster_v5.py 里的 URL
  3) 重新生成 RIUE问卷二维码.png 与 RIUE问卷海报_v5.svg
"""
import sys
import re
import os
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
PY = os.path.join(ROOT, "..", "..", ".workbuddy", "binaries", "python", "envs", "default", "Scripts", "python.exe")
PY = os.path.abspath(PY)

if len(sys.argv) < 2:
    print("用法: python set_links.py <最终部署地址，如 https://riue-survey.onrender.com>")
    sys.exit(1)

URL = sys.argv[1].strip().rstrip("/")
print("目标地址:", URL)

# 1) gen_qr.py : url = "..."
p1 = os.path.join(ROOT, "gen_qr.py")
s1 = open(p1, encoding="utf-8").read()
s1 = re.sub(r'(?m)^url = ".*"', f'url = "{URL}"', s1)
open(p1, "w", encoding="utf-8").write(s1)

# 2) gen_poster_v5.py : URL = "..."
p2 = os.path.join(ROOT, "gen_poster_v5.py")
s2 = open(p2, encoding="utf-8").read()
s2 = re.sub(r'(?m)^URL = ".*"', f'URL = "{URL}"', s2)
open(p2, "w", encoding="utf-8").write(s2)

# 3) 重新生成
print("=== 重新生成二维码 ===")
subprocess.run([PY, os.path.join(ROOT, "gen_qr.py")], check=True)
print("=== 重新生成海报 ===")
out_svg = os.path.join(ROOT, "RIUE问卷海报_v5.svg")
with open(out_svg, "w", encoding="utf-8") as f:
    subprocess.run([PY, os.path.join(ROOT, "gen_poster_v5.py")], stdout=f, check=True)
print("完成 ->", os.path.join(ROOT, "RIUE问卷二维码.png"))
print("完成 ->", out_svg)
