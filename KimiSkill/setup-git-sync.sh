#!/bin/bash

# Kimi Roles Git 同步设置脚本
# 使用方法: ./setup-git-sync.sh

set -e  # 遇到错误立即退出

echo "🚀 Kimi Roles Git 同步设置"
echo "=========================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 Git 是否安装
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git 未安装${NC}"
    echo "请先安装 Git:"
    echo "  macOS: brew install git"
    echo "  Ubuntu: sudo apt install git"
    echo "  Windows: 下载 Git for Windows"
    exit 1
fi

echo -e "${GREEN}✅ Git 已安装${NC}: $(git --version)"
echo ""

# 配置目录
SKILLS_DIR="$HOME/.config/agents/skills"

# 检查 skills 目录是否存在
if [ ! -d "$SKILLS_DIR" ]; then
    echo -e "${RED}❌ Skills 目录不存在: $SKILLS_DIR${NC}"
    echo "请先创建角色系统"
    exit 1
fi

echo -e "${GREEN}✅ Skills 目录存在${NC}: $SKILLS_DIR"
echo ""

# 进入 skills 目录
cd "$SKILLS_DIR"

# 检查是否已经是 Git 仓库
if [ -d ".git" ]; then
    echo -e "${YELLOW}⚠️  已经是 Git 仓库${NC}"
    echo "当前远程仓库:"
    git remote -v || echo "  (无)"
    echo ""
    read -p "是否重新初始化? (y/N): " REINIT
    if [[ $REINIT =~ ^[Yy]$ ]]; then
        rm -rf .git
        echo "已删除旧的 Git 仓库"
    else
        echo "退出设置"
        exit 0
    fi
fi

echo ""
echo "📁 第 1 步: 初始化 Git 仓库"
echo "--------------------------"
git init
echo -e "${GREEN}✅ Git 仓库初始化完成${NC}"
echo ""

# 配置用户信息
echo "👤 第 2 步: 配置 Git 用户信息"
echo "--------------------------"
echo ""

# 检查是否已有全局配置
GIT_NAME=$(git config user.name || echo "")
GIT_EMAIL=$(git config user.email || echo "")

if [ -z "$GIT_NAME" ] || [ -z "$GIT_EMAIL" ]; then
    echo "请输入你的信息（用于提交记录）:"
    read -p "姓名: " USER_NAME
    read -p "邮箱: " USER_EMAIL
    
    git config user.name "$USER_NAME"
    git config user.email "$USER_EMAIL"
else
    echo "已配置的用户信息:"
    echo "  姓名: $GIT_NAME"
    echo "  邮箱: $GIT_EMAIL"
    read -p "是否修改? (y/N): " CHANGE_INFO
    if [[ $CHANGE_INFO =~ ^[Yy]$ ]]; then
        read -p "新姓名: " USER_NAME
        read -p "新邮箱: " USER_EMAIL
        git config user.name "$USER_NAME"
        git config user.email "$USER_EMAIL"
    fi
fi

echo -e "${GREEN}✅ Git 用户信息配置完成${NC}"
echo ""

# 创建 .gitignore
echo "📝 创建 .gitignore"
echo "--------------------------"
cat > .gitignore << 'EOF'
# 系统文件
.DS_Store
Thumbs.db

# 编辑器
.vscode/
.idea/
*.swp
*.swo
*~

# 日志
*.log

# 临时文件
*.tmp
.temp/
EOF
echo -e "${GREEN}✅ .gitignore 创建完成${NC}"
echo ""

# 添加文件到暂存区
echo "📦 第 3 步: 添加文件"
echo "--------------------------"
git add .
echo -e "${GREEN}✅ 文件已添加到暂存区${NC}"
echo ""

# 查看状态
echo "📊 当前状态:"
git status --short
echo ""

# 提交
echo "💾 第 4 步: 提交到本地仓库"
echo "--------------------------"
git commit -m "Initial commit: 添加 Kimi 角色系统

包含 7 个角色:
- role-orchestrator: 角色调度员
- role-researcher: 项目研究员
- role-code-reviewer: 代码审查员
- role-doc-writer: 文档作者
- role-skill-writer: Skill 作者
- role-mode-writer: Mode 作者
- role-architect: 架构师

详见 A0004 Git 同步设置指南.md"

echo -e "${GREEN}✅ 提交完成${NC}"
echo ""

# 显示提交历史
echo "📜 提交历史:"
git log --oneline -1
echo ""

# 设置远程仓库
echo "☁️  第 5 步: 连接远程仓库"
echo "--------------------------"
echo ""
echo "请在 GitHub 上创建新仓库:"
echo "  1. 访问 https://github.com/new"
echo "  2. Repository name: kimi-roles (建议)"
echo "  3. 不要勾选 'Initialize this repository with a README'"
echo "  4. 点击 Create repository"
echo ""
read -p "是否现在连接远程仓库? (y/N): " CONNECT_REMOTE

if [[ $CONNECT_REMOTE =~ ^[Yy]$ ]]; then
    echo ""
    read -p "GitHub 用户名: " GITHUB_USER
    read -p "仓库名 (默认: kimi-roles): " REPO_NAME
    REPO_NAME=${REPO_NAME:-kimi-roles}
    
    REMOTE_URL="https://github.com/$GITHUB_USER/$REPO_NAME.git"
    
    echo ""
    echo "添加远程仓库: $REMOTE_URL"
    git remote add origin "$REMOTE_URL"
    git branch -M main
    
    echo ""
    echo "推送到 GitHub..."
    echo -e "${YELLOW}提示: 如果提示输入密码，请使用 GitHub Personal Access Token${NC}"
    echo "获取 Token: https://github.com/settings/tokens"
    echo ""
    
    git push -u origin main && {
        echo ""
        echo -e "${GREEN}✅ 推送成功!${NC}"
        echo ""
        echo "🎉 设置完成!"
        echo "============"
        echo ""
        echo "你的角色系统已托管到:"
        echo "  $REMOTE_URL"
        echo ""
        echo "在其他电脑上安装:"
        echo "  git clone $REMOTE_URL ~/.config/agents/skills"
        echo ""
    } || {
        echo ""
        echo -e "${RED}❌ 推送失败${NC}"
        echo "可能原因:"
        echo "  1. 仓库不存在，请先创建"
        echo "  2. 用户名/密码错误"
        echo "  3. 网络问题"
        echo ""
        echo "手动推送命令:"
        echo "  cd $SKILLS_DIR"
        echo "  git push -u origin main"
    }
else
    echo ""
    echo "跳过远程仓库设置"
    echo "稍后手动设置:"
    echo "  cd $SKILLS_DIR"
    echo "  git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git"
    echo "  git push -u origin main"
fi

echo ""
echo "📚 常用命令:"
echo "  查看状态:  git status"
echo "  添加修改:  git add ."
echo "  提交修改:  git commit -m '描述'"
echo "  推送到云端: git push"
echo "  拉取更新:  git pull"
echo ""
