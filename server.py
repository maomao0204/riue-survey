# -*- coding: utf-8 -*-
"""
RIUE 新客户调查 · 聚合后端（方案 B：可独立部署版本）
==================================================
特性：
  - 零外部依赖（仅 Python 标准库），可直接部署到 Render / VPS / 任意公网主机。
  - 自带 SQLite 存储：每次提交自动落库，实时聚合。
  - 可选「腾讯文档镜像」：若配置开放平台凭据，提交同时复制到你的腾讯智能表格。
  - 密码保护的管理页（/admin）：只有你本人登录后能查看实时汇总、导出 CSV、清理数据。
  - 同源托管问卷页（/）与管理页（/admin），一个进程搞定全部，二维码只需指向本服务根地址。

路由：
  GET  /                      分步引导问卷页（survey-dist/index.html）
  GET  /admin                 管理后台页（admin.html）
  POST /api/submit            接收前端答案 -> 落库 +（可选）镜像到腾讯表格
  POST /api/admin/login       管理员登录，返回 token
  GET  /api/admin/records     拉取全部汇总（需 token）
  GET  /api/admin/export      导出 CSV（需 token）
  POST /api/admin/delete      删除单条/全部（需 token）
  GET  /healthz               健康检查

环境变量：
  PORT                监听端口（默认 8787）
  ADMIN_PASSWORD      管理后台密码（必填；未设置则随机生成并打印到日志）
  SECRET_KEY          token 签名密钥（可选；不设则每次启动随机）
  DB_PATH             数据库文件路径（默认 ./riue_survey.db）
  # ── 可选：腾讯文档镜像 ──
  TENCENT_DOCS_ENABLED  设为 1 开启镜像
  TENCENT_DOCS_FILE_ID  智能表格 file_id
  TENCENT_DOCS_SHEET_ID 工作表 sheet_id
  TENCENT_DOCS_TOKEN    开放平台 access_token（Bearer）
"""

import os
import sys
import json
import time
import sqlite3
import secrets
import hmac
import hashlib
import base64
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(ROOT, "survey-dist", "index.html")
ADMIN = os.path.join(ROOT, "admin.html")
DB_PATH = os.environ.get("DB_PATH", os.path.join(ROOT, "riue_survey.db"))

# ── 字段映射：前端答案键 -> 数据库列 ──
COL_MAP = {
    "昵称": "nickname",
    "手机号": "phone",
    "年龄段": "age",
    "地址": "address",                 # 前端用「地址」，库里存「收货地址」
    "身边有人用过RIUE": "used_before",
    "用过的产品": "used_products",
    "肤质": "skin",
    "发质": "hair",
    "生活状况": "lifestyle",
    "洗护系列选品": "care_pick",
    "素颜护肤系列选品": "skin_pick",
    "身体香氛系列选品": "fragrance_pick",
    "健康养生系列选品": "wellness_pick",
    "私护系列选品": "intimate_pick",
}

# 管理页展示列顺序（key, 中文标签）
DISPLAY_FIELDS = [
    ("created_at", "提交时间"),
    ("nickname", "昵称"),
    ("phone", "手机号"),
    ("age", "年龄段"),
    ("address", "收货地址"),
    ("used_before", "身边有人用过RIUE"),
    ("used_products", "用过的产品"),
    ("skin", "肤质"),
    ("hair", "发质"),
    ("lifestyle", "生活状况"),
    ("care_pick", "洗护系列选品"),
    ("skin_pick", "素颜护肤系列选品"),
    ("fragrance_pick", "身体香氛系列选品"),
    ("wellness_pick", "健康养生系列选品"),
    ("intimate_pick", "私护系列选品"),
]

AGE_OPTIONS = ["18-24", "25-30", "31-40", "40 以上"]
PICK_COLUMNS = ["care_pick", "skin_pick", "fragrance_pick", "wellness_pick", "intimate_pick"]
TAG_COLUMNS = ["skin", "hair", "lifestyle"]

# ── 鉴权 ──
SECRET = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")
TOKEN_TTL = 12 * 3600  # 12 小时

if not ADMIN_PASSWORD:
    ADMIN_PASSWORD = secrets.token_hex(6)
    print(f"[init] 未设置 ADMIN_PASSWORD，本次随机生成：{ADMIN_PASSWORD}")


def make_token():
    payload = {"iat": int(time.time()), "n": secrets.token_hex(8)}
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
    sig = hmac.new(SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()
    return body + "." + sig


def valid_token(tok):
    if not tok:
        return False
    try:
        body, sig = tok.split(".")
        exp = hmac.new(SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(exp, sig):
            return False
        payload = json.loads(base64.urlsafe_b64decode(body))
        if int(time.time()) - int(payload.get("iat", 0)) > TOKEN_TTL:
            return False
        return True
    except Exception:
        return False


# ── 数据库 ──
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            nickname TEXT, phone TEXT, age TEXT, address TEXT,
            used_before TEXT, used_products TEXT,
            skin TEXT, hair TEXT, lifestyle TEXT,
            care_pick TEXT, skin_pick TEXT, fragrance_pick TEXT,
            wellness_pick TEXT, intimate_pick TEXT,
            payload TEXT
        )
    """)
    conn.commit()
    conn.close()


def normalize(answers):
    """前端 answers -> 数据库列字典（多选 join 为「、」）。"""
    out = {}
    for k, col in COL_MAP.items():
        v = answers.get(k, "")
        if isinstance(v, list):
            out[col] = "、".join(str(x).strip() for x in v if x not in (None, ""))
        else:
            out[col] = str(v or "").strip()
    return out


def insert_submission(answers):
    rec = normalize(answers)
    rec["created_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    rec["payload"] = json.dumps(answers, ensure_ascii=False)
    cols = list(rec.keys())
    placeholders = ", ".join("?" for _ in cols)
    sql = "INSERT INTO submissions ({}) VALUES ({})".format(", ".join(cols), placeholders)
    conn = get_db()
    conn.execute(sql, [rec[c] for c in cols])
    conn.commit()
    conn.close()
    return rec


def fetch_all():
    conn = get_db()
    rows = conn.execute(
        "SELECT {} FROM submissions ORDER BY id DESC".format(", ".join(c for c, _ in DISPLAY_FIELDS))
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def fetch_stats():
    rows = fetch_all()
    by_age = {a: 0 for a in AGE_OPTIONS}
    used = {"是": 0, "否": 0}
    products = {}
    tags = {}
    for r in rows:
        if r.get("age") in by_age:
            by_age[r["age"]] += 1
        if r.get("used_before") in used:
            used[r["used_before"]] += 1
        for c in PICK_COLUMNS:
            for item in (r.get(c) or "").split("、"):
                item = item.strip()
                if item:
                    products[item] = products.get(item, 0) + 1
        for c in TAG_COLUMNS:
            for item in (r.get(c) or "").split("、"):
                item = item.strip()
                if item:
                    tags[item] = tags.get(item, 0) + 1
    top_products = sorted(products.items(), key=lambda x: -x[1])[:10]
    top_tags = sorted(tags.items(), key=lambda x: -x[1])[:10]
    return {
        "total": len(rows),
        "by_age": by_age,
        "used_before": used,
        "top_products": [{"name": k, "count": v} for k, v in top_products],
        "top_tags": [{"name": k, "count": v} for k, v in top_tags],
    }


def delete_rows(ids=None):
    conn = get_db()
    if ids:
        conn.execute("DELETE FROM submissions WHERE id IN ({})".format(", ".join("?" * len(ids))), ids)
    else:
        conn.execute("DELETE FROM submissions")
    conn.commit()
    conn.close()


# ── 可选：腾讯文档镜像 ──
class TencentMirror:
    def __init__(self):
        self.enabled = os.environ.get("TENCENT_DOCS_ENABLED") == "1"
        self.file_id = os.environ.get("TENCENT_DOCS_FILE_ID")
        self.sheet_id = os.environ.get("TENCENT_DOCS_SHEET_ID")
        self.token = os.environ.get("TENCENT_DOCS_TOKEN")

    def build_record(self, answers):
        """复用已验证过的字段结构（文本/选项/手机号分开）。"""
        KEY_TO_FIELD = {
            "昵称": "昵称", "手机号": "手机号", "年龄段": "年龄段",
            "地址": "收货地址", "身边有人用过RIUE": "身边有人用过RIUE",
            "用过的产品": "用过的产品", "肤质": "肤质", "发质": "发质",
            "生活状况": "生活状况", "洗护系列选品": "洗护系列选品",
            "素颜护肤系列选品": "素颜护肤系列选品",
            "身体香氛系列选品": "身体香氛系列选品",
            "健康养生系列选品": "健康养生系列选品",
            "私护系列选品": "私护系列选品",
        }
        SINGLE = {"年龄段", "身边有人用过RIUE"}
        MULTI = {"肤质", "发质", "生活状况", "洗护系列选品", "素颜护肤系列选品",
                 "身体香氛系列选品", "健康养生系列选品", "私护系列选品"}
        PHONE = {"手机号"}
        fvs = []
        for key, field in KEY_TO_FIELD.items():
            val = answers.get(key, "")
            if isinstance(val, list):
                items = [str(v).strip() for v in val if v not in (None, "")]
            else:
                items = [str(val).strip()] if val not in (None, "") else []
            if not items:
                continue
            if field in MULTI:
                fvs.append({"field": field, "option_value": {"items": [{"text": v} for v in items]}})
            elif field in SINGLE:
                fvs.append({"field": field, "option_value": {"items": [{"text": items[0]}]}})
            elif field in PHONE:
                fvs.append({"field": field, "string_value": items[0]})
            else:
                fvs.append({"field": field, "text_value": {"items": [{"text": items[0], "type": "text"}]}})
        return fvs

    def push(self, answers):
        if not self.enabled:
            return
        if not (self.file_id and self.sheet_id and self.token):
            print("[tencent-mirror] 未配置完整凭据，跳过镜像")
            return
        try:
            fvs = self.build_record(answers)
            if not fvs:
                return
            url = ("https://docs.qq.com/openapi/smartsheet/v1/{}/sheets/{}/records"
                   .format(self.file_id, self.sheet_id))
            body = json.dumps({"records": [{"field_values": fvs}]}).encode("utf-8")
            req = urllib.request.Request(url, data=body, method="POST")
            req.add_header("Authorization", "Bearer " + self.token)
            req.add_header("Content-Type", "application/json")
            with urllib.request.urlopen(req, timeout=10) as resp:
                code = resp.getcode()
                _ = resp.read()
            print(f"[tencent-mirror] 镜像状态 {code}")
        except Exception as e:
            print(f"[tencent-mirror] 镜像失败（不影响主存储）: {e}")


mirror = TencentMirror()


# ── HTTP 处理 ──
class Handler(BaseHTTPRequestHandler):
    def _send_json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path, ctype):
        if not os.path.exists(path):
            self.send_response(404); self.end_headers(); return
        with open(path, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _auth_token(self):
        # 支持 Authorization: Bearer <token> 或 ?token=
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            return auth[7:].strip()
        from urllib.parse import urlparse, parse_qs
        q = parse_qs(urlparse(self.path).query)
        return (q.get("token") or [""])[0]

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        p = self.path.split("?")[0]
        if p.startswith("/healthz"):
            return self._send_json(200, {"ok": True})
        if p in ("/", "/index.html"):
            return self._send_file(INDEX, "text/html; charset=utf-8")
        if p in ("/admin", "/admin.html"):
            return self._send_file(ADMIN, "text/html; charset=utf-8")
        if p == "/api/admin/records":
            if not valid_token(self._auth_token()):
                return self._send_json(401, {"ok": False, "error": "未授权"})
            rows = fetch_all()
            return self._send_json(200, {"ok": True, "total": len(rows),
                                         "columns": [{"key": k, "label": l} for k, l in DISPLAY_FIELDS],
                                         "rows": rows, "stats": fetch_stats()})
        if p == "/api/admin/export":
            if not valid_token(self._auth_token()):
                return self._send_json(401, {"ok": False, "error": "未授权"})
            return self._export_csv()
        self.send_response(404); self.end_headers()

    def _export_csv(self):
        rows = fetch_all()
        import csv, io
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow([l for _, l in DISPLAY_FIELDS])
        for r in rows:
            w.writerow([r.get(k, "") or "" for k, _ in DISPLAY_FIELDS])
        data = ("\ufeff" + buf.getvalue()).encode("utf-8-sig")
        self.send_response(200)
        self.send_header("Content-Type", "text/csv; charset=utf-8")
        self.send_header("Content-Disposition", 'attachment; filename="RIUE_survey_export.csv"')
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        p = self.path.split("?")[0]
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length else b"{}"
            payload = json.loads(raw.decode("utf-8") or "{}")
        except Exception as e:
            return self._send_json(400, {"ok": False, "error": "请求解析失败: " + str(e)})

        if p == "/api/submit":
            answers = payload.get("answers", {})
            if not isinstance(answers, dict) or not answers:
                return self._send_json(400, {"ok": False, "error": "空的答案"})
            insert_submission(answers)
            mirror.push(answers)   # 可选镜像，失败不影响主存储
            return self._send_json(200, {"ok": True, "msg": "已汇总"})

        if p == "/api/admin/login":
            pw = payload.get("password", "")
            if pw == ADMIN_PASSWORD:
                return self._send_json(200, {"ok": True, "token": make_token()})
            return self._send_json(401, {"ok": False, "error": "密码错误"})

        if p == "/api/admin/delete":
            if not valid_token(self._auth_token()):
                return self._send_json(401, {"ok": False, "error": "未授权"})
            ids = payload.get("ids")
            if ids is not None and not isinstance(ids, list):
                ids = [ids]
            delete_rows(ids if ids else None)
            return self._send_json(200, {"ok": True, "msg": "已删除"})

        return self._send_json(404, {"ok": False, "error": "not found"})

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    init_db()
    PORT = int(os.environ.get("PORT", "8787"))
    print(f"RIUE aggregator server on :{PORT}  (管理后台密码见上方日志 / ADMIN_PASSWORD)")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
