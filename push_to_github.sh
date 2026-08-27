#!/usr/bin/env bash
# ============================================================
# RIUE 问卷仓库 → GitHub 一键推送脚本
# ------------------------------------------------------------
# 前置准备：
#   1) 在 GitHub 新建一个【空】仓库（不要勾选初始化 README / .gitignore / License）
#   2) 生成一个 Personal Access Token（PAT）：
#        GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
#        勾选 repo 权限，复制生成的 ghp_xxx 令牌
#   3) 把下面的 GH_USER / GH_REPO 改成你自己的值
#
# 用法（在 Git Bash 里运行）：
#       bash push_to_github.sh
#   首次推送会提示输入：
#       Username: 你的 GitHub 用户名
#       Password: 粘贴你的 PAT（输入时屏幕不显示，正常）
#   （Windows 上若装了 Git Credential Manager，凭据会被缓存，下次免输）
#
# ⚠️ 安全提示：
#   本脚本【不】把 token 写死。若你想用 token 内联（非交互），
#   取消最下方「可选：token 内联」段的注释并填入，用完务必删除该文件。
# ============================================================
set -e

GH_USER="你的GitHub用户名"
GH_REPO="riue-survey"

git remote remove origin 2>/dev/null || true
git remote add origin "https://github.com/${GH_USER}/${GH_REPO}.git"

# 统一分支名为 main（GitHub 默认）
git branch -M main

git push -u origin main

echo ""
echo "✅ 推送完成！"
echo "   下一步：打开 https://render.com → New + → Blueprint → 关联该仓库 → 建服务"
echo "   部署后在 Environment 填 ADMIN_PASSWORD（强密码），其余按 render.yaml 默认。"
echo "   拿到地址后，本机运行： python set_links.py https://你的地址.onrender.com"

# ── 可选：token 内联（仅在你确信不会误提交真 token 时使用）──
# GH_TOKEN="ghp_xxxxxxxxxxxxxxxx"
# git remote set-url origin "https://${GH_TOKEN}@github.com/${GH_USER}/${GH_REPO}.git"
# git push -u origin main
