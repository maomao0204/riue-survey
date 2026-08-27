# -*- coding: utf-8 -*-
"""
PythonAnywhere 部署用 WSGI 入口
================================
把本文件【全部内容】整体粘贴到 PythonAnywhere 控制台的 WSGI 配置文件
（路径形如 /var/www/<用户名>_pythonanywhere_com_wsgi.py），然后 Save + Reload。

前提：在 PA 的 Bash 控制台执行过
    git clone https://github.com/maomao0204/riue-survey.git ~/riue-survey

部署后访问地址：https://<你的用户名>.pythonanywhere.com
后台地址：https://<你的用户名>.pythonanywhere.com/admin  （密码见下方 ADMIN_PASSWORD）
"""
import sys
import os

# 项目目录：自动对应当前 PA 用户的 home（~/riue-survey），无需手填用户名
PROJECT_DIR = os.path.expanduser("~/riue-survey")
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
