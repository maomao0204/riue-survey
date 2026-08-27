# -*- coding: utf-8 -*-
"""
PythonAnywhere 部署用 WSGI 入口
================================
本文件内容用于粘贴到 PythonAnywhere 控制台的 WSGI 配置文件
（路径形如 /var/www/<你的用户名>_pythonanywhere_com_wsgi.py）。

使用前请：
  1. 把下面 USERNAME 改成你在 PythonAnywhere 注册的用户名（即子域名前缀）。
  2. 在 PA 的 Bash 控制台里执行：
        git clone https://github.com/maomao0204/riue-survey.git ~/riue-survey
  3. 把下面的 ADMIN_PASSWORD 改成你想要的密码（这里已用默认 137997953@）。

部署后访问地址：https://<你的用户名>.pythonanywhere.com
"""
import sys
import os

# ⚠️ 改成你的 PythonAnywhere 用户名（也是子域名前缀）
USERNAME = "YOURUSERNAME"

PROJECT_DIR = "/home/{}/riue-survey".format(USERNAME)
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

# 必须在 import server 之前设置密码：server.py 在导入时即读取该环境变量
os.environ["ADMIN_PASSWORD"] = "137997953@"
os.environ.setdefault("DB_PATH", os.path.join(PROJECT_DIR, "riue_survey.db"))

from server import Handler, init_db
from wsgi_adapter import make_wsgi_app

init_db()  # 确保数据库表已创建（首次部署必需）

# WSGI 服务器（PythonAnywhere 的 uWSGI）会调用这个 application
application = make_wsgi_app(Handler)
