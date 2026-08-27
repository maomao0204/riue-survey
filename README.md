# RIUE 新客户调查（方案 B：可独立部署版）

分步引导问卷 + 自动汇总 + 密码保护管理后台。零外部依赖，一个 Python 文件即可上线。

## 本地运行

```bash
pip install -r requirements.txt   # 实际无第三方依赖，仅用于平台识别
ADMIN_PASSWORD=你的强密码 python server.py
```

- 问卷页：`http://localhost:8787/`
- 管理后台：`http://localhost:8787/admin`（凭上面的密码登录）
- 健康检查：`http://localhost:8787/healthz`

## 部署到 Render（一键）

仓库根已含 `render.yaml`。把本仓库推到 GitHub 后，在 Render 用 **Blueprints** 导入即可。
详细步骤、环境变量、腾讯文档镜像配置见 **[DEPLOY.md](DEPLOY.md)**。

## 文件说明

| 文件 | 作用 |
|------|------|
| `server.py`        | 后端 + 问卷页 + 管理页（单文件，零依赖） |
| `survey-dist/index.html` | 分步引导问卷（被 server.py 托管） |
| `admin.html`       | 管理后台页（被 server.py 托管） |
| `DEPLOY.md`        | 完整部署与运维说明 |
| `set_links.py`     | 部署后改写二维码/海报指向并重新生成 |
| `gen_qr.py` / `gen_poster_v5.py` | 生成扫码物料（二维码/海报） |

## 数据归属

他人扫码只能提交自己的答案，看不到任何汇总；数据落在你的服务器数据库，
只有凭 `ADMIN_PASSWORD` 登录 `/admin` 的你本人能查看实时汇总。
