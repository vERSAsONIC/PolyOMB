# GitHub 认证问题排查

## ❌ 错误信息分析

```
remote: Invalid username or token.
Password authentication is not supported for Git operations.
```

**可能原因：**
1. Token 没有正确复制
2. Token 没有勾选 `repo` 权限
3. Token 已经过期或被撤销
4. 用户名大小写不匹配

---

## ✅ 解决方案

### 方案 1：检查 Token 权限（最可能的原因）

1. 访问 https://github.com/settings/tokens
2. 找到你创建的 Token（或创建新的）
3. **确保勾选了 `repo` 权限**：
   ```
   ☑️ repo
      ☑️ repo:status
      ☑️ repo_deployment
      ☑️ public_repo
      ☑️ repo:invite
      ☑️ security_events
   ```

4. 如果没有勾选，删除旧的，重新创建

---

### 方案 2：使用 GitHub CLI（更简单）

```bash
# 1. 安装 GitHub CLI
brew install gh

# 2. 登录（浏览器自动打开授权）
gh auth login
# 选择 HTTPS → 浏览器登录 → 授权

# 3. 使用 gh 推送
cd ~/.config/agents/skills
gh repo create kimi-roles --public --source=. --push
```

---

### 方案 3：切换到 SSH（推荐长期使用）

```bash
# 1. 生成 SSH 密钥
ssh-keygen -t ed25519 -C "your_email@example.com"

# 2. 添加到 SSH agent
ssh-add ~/.ssh/id_ed25519

# 3. 复制公钥
pbcopy < ~/.ssh/id_ed25519.pub

# 4. 添加到 GitHub：https://github.com/settings/keys
#    点击 "New SSH key" → 粘贴 → 保存

# 5. 修改远程仓库为 SSH
cd ~/.config/agents/skills
git remote set-url origin git@github.com:vERSAsONIC/kimi-roles.git

# 6. 推送
git push -u origin main
```

---

### 方案 4：检查仓库是否存在

访问：https://github.com/vERSAsONIC/kimi-roles

- 如果显示 **404**，说明仓库不存在，需要先创建
- 如果显示仓库页面，说明存在

**如果仓库不存在，创建后再推送：**
1. 访问 https://github.com/new
2. Repository name: `kimi-roles`
3. **不要勾选** "Initialize this repository with a README"
4. 点击 Create repository
5. 然后重新推送

---

## 🔧 快速修复命令

### 先检查当前状态：
```bash
cd ~/.config/agents/skills
git remote -v
git status
```

### 如果仓库不存在，使用 gh 一键创建并推送：
```bash
# 安装 gh
brew install gh

# 登录（浏览器授权，更简单）
gh auth login

# 创建仓库并推送
cd ~/.config/agents/skills
gh repo create kimi-roles --public --source=. --remote=origin --push
```

---

## 🆘 还是不行？

请检查以下几点：

1. **用户名是否正确**：
   ```bash
   # 必须是精确匹配
   vERSAsONIC  ✓
   versasonic  ✗
   VersaSonic  ✗
   ```

2. **Token 是否完整复制**：
   - Token 格式：`ghp_xxxxxxxxxxxxxxxxxxxx`
   - 确保没有遗漏字符
   - 确保没有多余的空格

3. **Token 权限是否正确**：
   - 必须勾选 `repo`
   - 否则无法推送代码

4. **仓库是否存在**：
   - 访问 https://github.com/vERSAsONIC/kimi-roles
   - 404 说明不存在

---

## 💡 最简单的解决方案

**使用 GitHub Desktop 或 VS Code：**

1. 打开 GitHub Desktop
2. File → Add local repository
3. 选择 `~/.config/agents/skills`
4. 它会自动检测并提示创建远程仓库
5. 点击 Publish repository

或者使用 VS Code：
1. 打开文件夹 `~/.config/agents/skills`
2. 点击左侧源代码管理图标
3. 点击 "Publish Branch"
4. 按提示登录 GitHub

---

## 📞 告诉我

执行以下命令，把输出发给我：

```bash
cd ~/.config/agents/skills
git remote -v
git status
curl -s https://api.github.com/users/vERSAsONIC | grep login
```

这样可以帮你精确定位问题！
