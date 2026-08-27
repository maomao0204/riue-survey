import segno

# 当前有效公网地址（localhost.run 隧道 → 本机交互式答题页，server.py :8787）
# 无警告页，扫码直达。免费版约 60 分钟有效；失效后重跑 投放问卷.bat 或用 set_links.py 更新。
url = "https://1e2038f82cc16f.lhr.life"

qrcode = segno.make(url, error="h")  # 高容错，方便手机远距离扫码
out = r"C:\Users\ASUS\WorkBuddy\2026-08-26-20-14-03\RIUE问卷二维码.png"
qrcode.save(out, scale=18, border=4, dark="#1a1a1a", light="#ffffff")
print("QR saved ->", out)
