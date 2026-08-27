#!/usr/bin/env python3
"""Generate RIUE survey poster SVG — v5
Changes vs v4:
  - Top "RIUE" outer circle replaced with rectangular vine border
    (rounded-rect main vine + 4 corner tendrils + 4 mid-edge leaves).
  - Badge center raised slightly to 90 for better top balance.
"""
import sys, io, base64
sys.path.insert(0, r"C:\Users\ASUS\.workbuddy\plugins\cache\workbuddy-builtin\tencent-docs-plugin\1.0.0\skills\tencent-docs")
import segno

URL = "https://1e1c640dd4a9fb.lhr.life"

BG_TOP    = "#d6ebe4"
BG_BOT    = "#eef5f2"
ACCENT    = "#2a8c7a"
ACCENT_DK = "#1f6b5d"
DARK      = "#1a2e28"
MID       = "#4a6b62"
LIGHT_TXT = "#6b8a82"
WHITE     = "#ffffff"

W, H = 680, 907
cx = W // 2

qr = segno.make(URL, error="h")
buf = io.BytesIO()
qr.save(buf, kind="png", scale=15, border=3, dark="#1a2e28", light="#ffffff")
qr_b64 = base64.b64encode(buf.getvalue()).decode()
qr_uri = f"data:image/png;base64,{qr_b64}"

QR = 248
qr_top = 374
qr_bot = qr_top + QR
qr_cy  = qr_top + QR // 2

# ── Vine badge helpers ──────────────────────────────────────────

BADGE_CY = 90          # badge vertical centre (was 94)
INN_W, INN_H = 168, 96 # inner frame size
INN_RX = 16            # inner corner radius
OUT_PAD = 14           # vine border outside inner frame
OUT_W = INN_W + OUT_PAD * 2   # 196
OUT_H = INN_H + OUT_PAD * 2   # 124
OUT_RX = 22            # outer vine corner radius


def leaf(x, y, angle_deg, scale=1.0, color=ACCENT):
    """A single leaf: base at (x,y), grows along rotated +X axis."""
    s = scale
    return (
        f'<g transform="translate({x},{y}) rotate({angle_deg}) scale({s})">'
        f'<path d="M0,0 C 7,-9 22,-9 28,0 C 22,9 7,9 0,0 Z" fill="{color}"/>'
        f'<path d="M1.5,0 L26,0" stroke="{ACCENT_DK}" stroke-width="0.8" '
        f'fill="none" opacity="0.5"/></g>'
    )


def tendril(x, y, angle_deg, color=ACCENT_DK):
    """A small curling tendril sprouting outward from a corner."""
    return (
        f'<path transform="translate({x},{y}) rotate({angle_deg})" '
        f'fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" '
        f'd="M0,0 q 10,-3 13,-14 q 2,-11 -8,-15 q -9,-2 -7,8 q 1,5 7,4"/>'
    )


def small_leaf(x, y, angle_deg, scale=0.55, color=ACCENT):
    """Tiny accent leaf."""
    return leaf(x, y, angle_deg, scale, color)


# Build the vine badge SVG fragment
ix = cx - INN_W // 2       # inner left
iy = BADGE_CY - INN_H // 2 # inner top
ox = cx - OUT_W // 2       # outer (vine) left
oy = BADGE_CY - OUT_H // 2 # outer top

vine_parts = []

# 1) Inner subtle frame (very light)
vine_parts.append(
    f'<rect x="{ix}" y="{iy}" width="{INN_W}" height="{INN_H}" rx="{INN_RX}" '
    f'fill="none" stroke="{ACCENT}" stroke-width="1.2" opacity="0.35"/>'
)

# 2) Outer main vine — rounded rectangle (the "rectangle" part)
vine_parts.append(
    f'<rect x="{ox}" y="{oy}" width="{OUT_W}" height="{OUT_H}" rx="{OUT_RX}" '
    f'fill="none" stroke="{ACCENT_DK}" stroke-width="2.4"/>'
)

# 3) Corner tendrils (sprout outward from each corner)
#    angles chosen so tendril curls away from the centre
corner_tendils = [
    (ox, oy,           -145),  # top-left
    (ox + OUT_W, oy,    -35),  # top-right
    (ox, oy + OUT_H,    145),  # bottom-left
    (ox + OUT_W, oy + OUT_H, 35),  # bottom-right
]
for tx, ty, ang in corner_tendils:
    vine_parts.append(tendril(tx, ty, ang))

# 4) Mid-edge leaves (one per side, pointing outward)
mid_leaves = [
    (cx, oy,             -90, 1.0),   # top
    (cx, oy + OUT_H,      90, 1.0),   # bottom
    (ox, BADGE_CY,        180, 1.0),  # left
    (ox + OUT_W, BADGE_CY,  0, 1.0),  # right
]
for lx, ly, la, ls in mid_leaves:
    vine_parts.append(leaf(lx, ly, la, ls))

# 5) Extra tiny accent leaves near corners for lushness
tiny_leaves = [
    (ox + 18, oy + 10,         -120, 0.45),
    (ox + OUT_W - 18, oy + 10,  -60, 0.45),
    (ox + 18, oy + OUT_H - 10,  120, 0.45),
    (ox + OUT_W - 18, oy + OUT_H - 10, 60, 0.45),
]
for lx, ly, la, ls in tiny_leaves:
    vine_parts.append(small_leaf(lx, ly, la, ls))

badge_svg = "\n".join(vine_parts)

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{BG_TOP}"/>
      <stop offset="100%" stop-color="{BG_BOT}"/>
    </linearGradient>
    <pattern id="lines" width="64" height="64" patternUnits="userSpaceOnUse">
      <line x1="0" y1="0" x2="64" y2="64" stroke="{ACCENT}" stroke-width="0.4" opacity="0.05"/>
    </pattern>
    <radialGradient id="halo" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="{ACCENT}" stop-opacity="0.12"/>
      <stop offset="70%" stop-color="{ACCENT}" stop-opacity="0.05"/>
      <stop offset="100%" stop-color="{ACCENT}" stop-opacity="0"/>
    </radialGradient>
    <filter id="cardShadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="8" stdDeviation="16" flood-color="#1a2e28" flood-opacity="0.10"/>
    </filter>
  </defs>

  <rect width="{W}" height="{H}" fill="url(#bg)"/>
  <rect width="{W}" height="{H}" fill="url(#lines)"/>
  <circle cx="{cx}" cy="{qr_cy}" r="162" fill="url(#halo)"/>

  <!-- ═══ Brand Badge — Rectangular Vine Border ═══ -->
  <g transform="translate(0,0)">
{badge_svg}
    <!-- RIUE text centred inside the vine frame -->
    <text x="{cx}" y="{BADGE_CY + 19}" text-anchor="middle"
          font-family="Georgia, 'Times New Roman', serif"
          font-size="54" font-weight="bold" fill="{ACCENT}" letter-spacing="3">RIUE</text>
  </g>

  <!-- ═══ Main Title ═══ -->
  <text x="{cx}" y="222" text-anchor="middle"
        font-family="'PingFang SC', 'Microsoft YaHei', 'Noto Sans CJK SC', sans-serif"
        font-size="42" font-weight="700" fill="{DARK}" letter-spacing="3">
    新客户调查问卷
  </text>

  <text x="{cx}" y="268" text-anchor="middle"
        font-family="'PingFang SC', 'Microsoft YaHei', sans-serif"
        font-size="18" font-weight="500" fill="{ACCENT_DK}" letter-spacing="6">
    体验装选品调查
  </text>

  <g transform="translate({cx}, 298)">
    <line x1="-55" y1="0" x2="-10" y2="0" stroke="{ACCENT}" stroke-width="1.5"/>
    <path d="M0,-4 L4,0 L0,4 L-4,0 Z" fill="{ACCENT}"/>
    <line x1="10" y1="0" x2="55" y2="0" stroke="{ACCENT}" stroke-width="1.5"/>
  </g>

  <text x="{cx}" y="334" text-anchor="middle"
        font-family="'Helvetica Neue', Helvetica, Arial, sans-serif"
        font-size="14" font-weight="300" font-style="italic" fill="{MID}" letter-spacing="3">
    RIUE  一个懂你的品牌
  </text>

  <!-- ═══ QR Code (focal point) ═══ -->
  <g transform="translate({cx - QR//2}, {qr_top})" filter="url(#cardShadow)">
    <rect x="0" y="0" width="{QR}" height="{QR}" rx="16" fill="{WHITE}"/>
    <rect x="9" y="9" width="{QR-18}" height="{QR-18}" rx="11" fill="#fafdfb"/>
    <image x="16" y="16" width="{QR-32}" height="{QR-32}"
           href="{qr_uri}" preserveAspectRatio="xMidYMid meet"/>
  </g>

  <text x="{cx}" y="658" text-anchor="middle"
        font-family="'PingFang SC', 'Microsoft YaHei', sans-serif"
        font-size="16" font-weight="600" fill="{DARK}" letter-spacing="1">
    微信扫码 · 1 分钟完成填写
  </text>

  <text x="{cx}" y="712" text-anchor="middle"
        font-family="'PingFang SC', 'Microsoft YaHei', sans-serif"
        font-size="17" font-weight="600" fill="{ACCENT_DK}" letter-spacing="1">
    认真选 · 用心送 · 你的专属定制礼盒
  </text>

  <text x="{cx}" y="754" text-anchor="middle"
        font-family="'PingFang SC', 'Microsoft YaHei', sans-serif"
        font-size="14" font-weight="400" fill="{LIGHT_TXT}" letter-spacing="2">
    不玩套路 · 只送好物
  </text>

  <line x1="200" y1="800" x2="480" y2="800"
        stroke="{ACCENT}" stroke-width="0.8" opacity="0.3"/>

  <text x="{cx}" y="882" text-anchor="middle"
        font-family="'PingFang SC', 'Microsoft YaHei', sans-serif"
        font-size="11" font-weight="400" fill="{LIGHT_TXT}" letter-spacing="1" opacity="0.75">
    数据仅用于产品调研，严格保密
  </text>

</svg>'''

print(svg)
