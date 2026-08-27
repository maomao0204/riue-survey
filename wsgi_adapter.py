# -*- coding: utf-8 -*-
"""
RIUE 问卷 · WSGI 适配器
======================
把零依赖的 BaseHTTPRequestHandler（server.py 里的 Handler）包装成一个
标准 WSGI application，使其可部署到 PythonAnywhere / 任意 WSGI 服务器
（无需 Flask、无需任何第三方库）。

- 完全不改动 server.py 原有逻辑：Render / VPS 上仍可用 `python server.py` 监听端口。
- 本文件仅在本机/云端以 WSGI 模式托管时由 wsgi.py 引入。

原理：绕过 BaseHTTPRequestHandler 的 socket 层，直接把标准输入/输出缓冲区
（BytesIO）接成 rfile / wfile，再由 handler 的原生 do_GET / do_POST 处理一个
请求，最后从输出缓冲解析出 WSGI 需要的 (status, headers, body)。

用法（见 wsgi.py）：
    from wsgi_adapter import make_wsgi_app
    from server import Handler
    application = make_wsgi_app(Handler)
"""
import io

# 跳过的逐跳（hop-by-hop）头，WSGI 服务器会自行处理，不能由应用转发。
_HOP_BY_HOP = {
    "connection", "transfer-encoding", "keep-alive", "upgrade",
    "proxy-authenticate", "proxy-authorization", "te", "trailers",
    "server", "date",
}


class _NoopConn:
    """setup() 需要一个 connection 占位对象，实际不会被用到。"""
    pass


def make_wsgi_app(handler_cls):
    """返回一个 WSGI application(callable)。"""

    class _BufferHandler(handler_cls):
        """用内存缓冲替代 socket 的 handler 变体，只为处理单个请求。"""

        def __init__(self, request_bytes, out_buf):
            self._in = io.BytesIO(request_bytes)
            self._out = out_buf
            # 满足 BaseHTTPRequestHandler 的最小状态
            self.request = None
            self.client_address = ("127.0.0.1", 0)
            self.server = None
            self.setup()
            try:
                self.handle()
            finally:
                self.finish()

        def setup(self):
            # 关键：直接把 rfile / wfile 指向内存缓冲，彻底绕开 socket.makefile
            self.rfile = self._in
            self.wfile = self._out
            self.connection = _NoopConn()

        def finish(self):
            # 不要关闭 wfile，外部还要读取响应
            pass

    def application(environ, start_response):
        method = environ["REQUEST_METHOD"]
        path = environ.get("PATH_INFO", "") or "/"
        qs = environ.get("QUERY_STRING", "")
        full_path = path + ("?" + qs if qs else "")

        try:
            length = int(environ.get("CONTENT_LENGTH", "0") or "0")
        except (ValueError, TypeError):
            length = 0
        body = b""
        if length:
            body = environ["wsgi.input"].read(length)

        # 把 WSGI 环境重组成一段标准 HTTP 请求文本，喂给 handler
        header_lines = []
        for k, v in environ.items():
            if k.startswith("HTTP_"):
                name = k[5:].replace("_", "-").title()
                header_lines.append(f"{name}: {v}")
        if "CONTENT_TYPE" in environ:
            header_lines.append(f"Content-Type: {environ['CONTENT_TYPE']}")
        if length:
            header_lines.append(f"Content-Length: {length}")

        req_text = (f"{method} {full_path} HTTP/1.1\r\n"
                    + "\r\n".join(header_lines) + "\r\n\r\n")
        req_bytes = req_text.encode("utf-8") + body

        out = io.BytesIO()
        try:
            _BufferHandler(req_bytes, out)
        except Exception as exc:  # 适配器兜底，避免整页 500 无信息
            start_response("500 Internal Server Error",
                           [("Content-Type", "text/plain; charset=utf-8")])
            return [f"adapter error: {exc}".encode("utf-8")]

        raw = out.getvalue()
        if not raw:
            start_response("500 Internal Server Error",
                           [("Content-Type", "text/plain; charset=utf-8")])
            return [b"empty response"]

        # 解析 handler 写回的响应：状态行 + 头 + 空行 + 体
        status_line = raw.split(b"\r\n", 1)[0].decode("utf-8", "replace")
        parts = status_line.split(" ", 2)
        status_code = int(parts[1]) if len(parts) > 1 else 500
        status_text = parts[2] if len(parts) > 2 else "Error"

        head_end = raw.find(b"\r\n\r\n")
        header_block = raw[len(status_line) + 2:head_end].decode("utf-8", "replace")
        wsgi_headers = []
        for line in header_block.split("\r\n"):
            if ":" in line:
                hname, hval = line.split(":", 1)
                hname = hname.strip().lower()
                if hname in _HOP_BY_HOP:
                    continue
                wsgi_headers.append((hname, hval.strip()))

        body_out = raw[head_end + 4:]
        start_response(f"{status_code} {status_text}", wsgi_headers)
        return [body_out]

    return application
