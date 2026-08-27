import segno

# 指向分步引导式问卷网页（CloudStudio 静态部署，微信扫码即开、逐项引导填写）
url = "https://2fed42f989974d93b86369f1cc058390.app.workbuddy.link"

qrcode = segno.make(url, error="h")  # 高容错，方便手机远距离扫码
out = r"C:\Users\ASUS\WorkBuddy\2026-08-26-20-14-03\RIUE问卷二维码.png"
qrcode.save(out, scale=12, border=4, dark="#1a1a1a", light="#ffffff")
print("QR saved ->", out)
