# RIUE 新客户调查 · 部署说明（方案 B：自建可部署后端）

> 目标：扫码填写 → 自动汇总 → **只有你本人凭密码在管理后台看实时数据**。
> 一条命令起服务、零外部依赖（仅 Python 标准库）、可部署到 Render 免费主机或任意 VPS；**也可直接跑在自己电脑上通过 Cloudflare 隧道暴露公网（见第八节，无需任何账号）**。

---

## 一、架构（部署后）

```
客户微信扫码
   │
   ▼
[ 你的公网地址 / ]  ← server.py 同进程托管「分步引导问卷页」
   │  POST /api/submit
   ▼
[ server.py ]  ── 写入本地 SQLite（实时聚合，权威数据源）
   │
   ├─（可选）TENCENT_DOCS_ENABLED=1 时，同时镜像到你的腾讯文档智能表格
   │
   ▼
[ /admin ] 密码登录后查看实时汇总 / 统计 / 导出 CSV / 清空
```

- **谁能看数据？** 只有知道 `ADMIN_PASSWORD` 的人能进 `/admin`。填写者只能提交自己的答案，看不到任何汇总。
- **数据存在哪？** 默认在服务器上的 `riue_survey.db`（SQLite 文件）。可随时在后台「导出 CSV」全量下载。
- **稳定吗？** 部署到 Render / VPS 后 7×24 在线，不再依赖会断的隧道。

---

## 二、准备文件

部署只需两个文件（都在本项目目录）：

| 文件 | 作用 |
|------|------|
| `server.py`        | 后端 + 问卷页 + 管理页（单文件，零依赖） |
| `survey-dist/index.html` | 分步引导问卷（被 server.py 托管，一般无需改） |
| `admin.html`       | 管理后台页（被 server.py 托管） |

> 不需要 `tencentdocs` 连接器、不需要 Flask、不需要任何 pip 包。

---

## 三、部署到 Render（推荐，免费）

1. 把本目录推到你的 GitHub 仓库（新建一个仓库，例如 `riue-survey`）。
2. 打开 https://render.com → **New + → Web Service** → 关联该仓库。
3. 配置：
   - **Runtime**: Python 3
   - **Build Command**: 留空（零依赖，无需安装）
   - **Start Command**: `python server.py`
4. **Environment（环境变量）** 添加：
   - `PORT` = `10000`（Render 默认；server.py 会自动读）
   - `ADMIN_PASSWORD` = `你的强密码`（**务必设置**，否则每次重启随机生成）
   - 可选：`DB_PATH` = `./riue_survey.db`
   - 可选（腾讯镜像）：见第五节
5. 部署完成后，Render 给你一个地址，例如 `https://riue-survey.onrender.com`。
6. **重指向二维码/海报**：在本机运行
   ```bash
   python set_links.py https://riue-survey.onrender.com
   ```
   会重新生成 `RIUE问卷二维码.png` 与 `RIUE问卷海报_v5.svg`，扫码即进你的稳定地址。
7. 打开 `https://riue-survey.onrender.com/admin` → 输入密码 → 即可看实时汇总。

> 免费版 Render 有「冷启动」：15 分钟无访问会休眠，下次访问约 30 秒唤醒。如需常驻，升级付费档或选 VPS。

---

## 四、部署到自有 VPS（通用 Linux）

```bash
# 1) 上传文件（server.py 即可）
scp server.py user@your-server:/opt/riue/

# 2) 安装 supervisor 或用 nohup 常驻
cd /opt/riue
ADMIN_PASSWORD='你的强密码' PORT=8787 nohup python3 server.py > server.log 2>&1 &

# 3) 用 Nginx 反代（示例）
# location / { proxy_pass http://127.0.0.1:8787; }
```

- 对外地址即你的域名/IP，例如 `https://survey.yourdomain.com`。
- 同样用 `python set_links.py https://survey.yourdomain.com` 重生成二维码/海报。
- 数据库 `riue_survey.db` 在服务器上，定期备份该文件即可。

---

## 五、（可选）同时镜像到你的腾讯文档智能表格

若希望数据**除了**进后端数据库，**也**自动写入你自己的腾讯文档智能表格（方便在腾讯文档里直接看），开启镜像：

环境变量：

| 变量 | 说明 |
|------|------|
| `TENCENT_DOCS_ENABLED` | 设为 `1` 开启 |
| `TENCENT_DOCS_FILE_ID` | 智能表格的 file_id |
| `TENCENT_DOCS_SHEET_ID` | 工作表 sheet_id |
| `TENCENT_DOCS_TOKEN`   | 腾讯文档开放平台 access_token（Bearer） |

获取 token 的方式（二选一）：
- **方式 A（最简单）**：在你本机已连好的 `tencent-docs` 连接器环境里，把连接器当前会话的 access_token 取出填入（注意它有时效，适合临时）。
- **方式 B（正式）**：到 https://docs.qq.com/open 注册应用，走 OAuth2 拿到长期 token。

> 镜像失败**不影响**主数据库与后台查看（仅打印日志跳过）。此路径依赖腾讯开放平台接口，部署前请先用你的凭据自测一次。

---

## 六、管理后台使用

打开 `<你的地址>/admin`：

- **登录**：输入 `ADMIN_PASSWORD`。
- **实时汇总**：表格按提交时间倒序展示全部答案（15 列：提交时间 / 昵称 / 手机号 / 年龄段 / 收货地址 / 身边有人用过RIUE / 用过的产品 / 肤质 / 发质 / 生活状况 / 五大系列选品）。
- **统计卡**：累计提交数、身边是否用过 RIUE 分布、热门选品 Top、肤质/发质/生活标签 Top。
- **搜索**：顶部输入框按昵称/手机号/任意内容过滤。
- **自动刷新**：勾选后每 15 秒拉取最新。
- **导出 CSV**：一键下载全量数据（含 BOM，Excel 直接打开中文不乱码）。
- **清空全部**：危险操作，二次确认后删除所有提交（仅清数据库，不影响腾讯镜像里的历史）。

---

## 七、安全提示

- `ADMIN_PASSWORD` 务必设为强密码，并通过环境变量注入，**不要写进代码或公开仓库**。
- 管理后台无账号体系，仅凭这一密码；如多人需要查看，请通过腾讯文档镜像共享表格，而非共用此密码。
- 数据库文件 `riue_survey.db` 含客户手机号等个人信息，请妥善保管服务器访问权限并定期备份。
- 若地址暴露被刷，可在 `/api/submit` 前加一层限流或验证码（按需二次开发）。

---

## 八、零账号方案：自己电脑 + Cloudflare 隧道（无需 GitHub，推荐给不想注册云账号的用户）

**适合**：不想注册 GitHub / Render，希望客户数据**全留自己电脑**、只有你凭密码看后台。

**本质**：在你电脑上跑 `server.py`，再用 Cloudflare 免费隧道把 `localhost:8787` 变成一个公网 https 地址。无需任何云账号——quick tunnel 连 Cloudflare 账号都不用注册。

**交互引导 + 自动汇总 + 仅你能看后台，三点全部保留**，与部署到 Render/VPS 完全一致。

### 步骤

1. 双击本项目里的 **`start_survey.bat`**（先启动后端，再拉起 Cloudflare 隧道）。
2. 隧道窗口会打印一个 `https://xxxx.trycloudflare.com` 地址——这就是公网入口。
3. 在本机运行，把二维码/海报指过去：
   ```bash
   python set_links.py https://xxxx.trycloudflare.com
   ```
4. 后台：`https://xxxx.trycloudflare.com/admin` → 输入 `ADMIN_PASSWORD` → 看实时汇总。

### 固定地址（named tunnel，适合长期 / 多次投放）

不想每次重启都重指二维码？注册个免费 Cloudflare 账号，建一条 named tunnel，地址就固定不变（`https://<隧道ID>.cfargotunnel.com`）。

一次性准备（在 cmd 里执行）：
```bash
cloudflared tunnel login                # 浏览器登录 Cloudflare（免费账号）
cloudflared tunnel create riue-survey   # 建隧道，记下隧道名
```
然后打开 `start_survey.bat`，把顶部的 `set "TUNNEL_NAME="` 改成 `set "TUNNEL_NAME=riue-survey"`，保存。
之后每次双击脚本即复用固定地址，只需在第一次运行完后执行一次：
```bash
python set_links.py https://<隧道ID>.cfargotunnel.com
```
（脚本首次运行会打印这个固定地址，抄下来即可。）

> named tunnel 的默认主机名就是 `<隧道ID>.cfargotunnel.com`，免费账号无需自己配 DNS；若想用自有域名，再执行 `cloudflared tunnel route dns <隧道名> <子域>` 即可。

### 注意

- 收集期间**电脑要保持开机**、`start_survey.bat` 的窗口别关。
- 隧道重启（或电脑重启）后网址会变 → 重新跑第 3 步 `set_links.py` 指过去即可。
- 若提示找不到 `cloudflared`：到 https://github.com/cloudflare/cloudflared/releases 下载 `cloudflared-windows-amd64.exe`，重命名为 `cloudflared.exe` 放进 PATH，再重跑脚本。
- 数据在电脑上的 `riue_survey.db`，随时在后台「导出 CSV」下载备份。
- 想要固定地址、不用每次重指二维码：见上方「固定地址（named tunnel）」小节，改 `start_survey.bat` 顶部的 `TUNNEL_NAME` 即可。
