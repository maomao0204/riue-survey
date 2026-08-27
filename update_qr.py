# -*- coding: utf-8 -*-
"""
把海报 SVG 与独立二维码 PNG 的扫码目标，改为「当前公网隧道地址」，
并在海报 SVG 中就地替换原有二维码（保留其余海报设计不变）。
"""
import io, base64, re, os
import segno

ROOT = os.path.dirname(os.path.abspath(__file__))

# 当前正在运行、微信可扫、可实时汇总、仅后台可见的公网地址
URL = "https://brimy-240e-3a6-e0d-1948-8851-b2f-906f-a5be.run.pinggy-free.link"

# 二维码样式与 gen_poster_v5.py 保持一致（深墨绿模块 + 白底 + 高容错 + 静区）
qr = segno.make(URL, error="h")
buf = io.BytesIO()
qr.save(buf, kind="png", scale=24, border=4, dark="#1a2e28", light="#ffffff")
png_bytes = buf.getvalue()
qr_b64 = base64.b64encode(png_bytes).decode()
qr_uri = f"data:image/png;base64,{qr_b64}"

# 1) 就地替换海报 SVG 里的二维码（只改 <image href 的 base64，其余不动）
svg_path = os.path.join(ROOT, "RIUE问卷海报_v5.svg")
svg = open(svg_path, encoding="utf-8").read()
old_uri = re.search(r'href="data:image/png;base64,[^"]*"', svg).group(0)
if old_uri == f'href="{qr_uri}"':
    print("海报二维码已是指向公网地址的版本，无需改动（字节一致）。")
else:
    new_svg = re.sub(
        r'href="data:image/png;base64,[^"]*"',
        f'href="{qr_uri}"',
        svg,
        count=1,
    )
    open(svg_path, "w", encoding="utf-8").write(new_svg)
    print("海报二维码已替换为新生成的公网地址二维码。")

# 2) 重新生成独立二维码 PNG（用于单独打印/分享）
png_path = os.path.join(ROOT, "RIUE问卷二维码.png")
open(png_path, "wb").write(png_bytes)

print("二维码目标地址 :", URL)
print("SVG 二维码已替换 ->", svg_path)
print("独立二维码已生成 ->", png_path)
print("新二维码 base64 长度 :", len(qr_b64), "字符")
