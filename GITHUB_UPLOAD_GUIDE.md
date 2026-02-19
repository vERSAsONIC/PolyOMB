# GitHub 上传指南

## 步骤 1：在 GitHub 创建仓库

1. 打开 https://github.com/new
2. 填写仓库信息：
   - **Repository name**: `omb-architecture-worm` （或你喜欢的名字）
   - **Description**: `PolyOMB 波动率做市策略系统 - 架构设计与实现`
   - **Visibility**: ☑️ Public（让别人可以阅读）
   - **Initialize**: ☐ 不要勾选 "Add a README file"

3. 点击 **Create repository**

## 步骤 2：推送本地代码

创建仓库后，GitHub 会显示类似以下的命令，在终端执行：

```bash
cd "/Users/liuqiong/Documents/My Games/00022 - OMB Architecture Worm"

# 添加远程仓库（用你的用户名替换 USERNAME）
git remote add origin https://github.com/USERNAME/omb-architecture-worm.git

# 推送代码
git branch -M main
git push -u origin main
```

## 步骤 3：验证上传

访问 `https://github.com/USERNAME/omb-architecture-worm` 查看是否成功。

---

## 方案二：使用 GitHub CLI（更快）

如果你愿意安装 GitHub CLI：

```bash
# macOS 安装
brew install gh

# 登录
gh auth login

# 创建并推送仓库
cd "/Users/liuqiong/Documents/My Games/00022 - OMB Architecture Worm"
gh repo create omb-architecture-worm --public --source=. --push
```

---

## 可选：美化你的仓库

### 添加 README.md

```markdown
# PolyOMB Architecture Worm

波动率做市策略系统的架构设计与实现

## 项目结构

```
├── PolyOMB_Skills/          # Skill 模块
├── KimiSkill/               # Kimi Skill 框架
├── CodeLib/                 # 代码库
└── docs/                    # 文档
```

## 快速开始

```bash
cd PolyOMB_Skills/00002_volatility_market_maker
streamlit run app.py
```

## 文档

- [架构设计](PolyOMB_Skills/00002_volatility_market_maker/tests/A0004%20多页面应用架构设计.md)
- [使用说明](PolyOMB_Skills/00002_volatility_market_maker/A0005%20多页面应用使用说明.md)

## License

MIT
```

### 添加 .gitattributes（处理中文文件名）

```gitattributes
*.md text eol=lf
*.py text eol=lf
```

---

## 常见问题

### Q: 推送时提示需要用户名密码？
A: GitHub 已不支持密码，需要使用 Personal Access Token：
   1. 访问 https://github.com/settings/tokens
   2. 生成 Token（勾选 repo 权限）
   3. 用 Token 代替密码输入

### Q: 文件名包含中文有问题？
A: 执行以下命令：
```bash
git config core.quotepath false
```

### Q: 仓库太大上传慢？
A: 检查是否有大文件：
```bash
# 查看大文件
git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | awk '/^blob/ {sum+=$3} END {print "总大小: " sum/1024/1024 " MB"}'
```
