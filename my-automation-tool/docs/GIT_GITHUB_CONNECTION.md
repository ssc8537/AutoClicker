# Git → GitHub 连接说明（Windows 11 / SSH 方式）

## 概述

本机 Git 已通过 **SSH 密钥认证** 的方式与 GitHub 账户 `ssc8537` 连接。
以下记录了完整配置过程和当前状态，方便后续 AI 或用户直接使用。

---

## 1. Git 全局配置

已设置以下全局参数（存储在 `~/.gitconfig`）：

| 字段 | 值 |
|------|----|
| `user.name` | `ssc8537` |
| `user.email` | `1970267588@qq.com` |

使用 `git config --global --list` 可查看完整配置。

---

## 2. SSH 密钥认证（核心连接方式）

### 2.1 密钥文件位置

| 文件 | 用途 |
|------|------|
| `C:\Users\s\.ssh\id_ed25519` | 私钥（**不要泄露**） |
| `C:\Users\s\.ssh\id_ed25519.pub` | 公钥（已添加到 GitHub 账户） |

### 2.2 公钥内容

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJ5SrhLahYoATBA4QO1C+e2a9Is2jdoMVD96EKPzyfAM 1970267588@qq.com
```

### 2.3 SSH 配置文件

`C:\Users\s\.ssh\config` 内容如下：

```
Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519
  IdentitiesOnly yes
```

作用：连接 `github.com` 时自动使用 `id_ed25519` 这个密钥。

### 2.4 GitHub 信任记录

第一次连接时，GitHub 的主机指纹已记录到 `C:\Users\s\.ssh\known_hosts`，后续不会再出现确认提示。

---

## 3. 如何验证连接是否正常

运行以下命令测试 SSH 连接（静默模式）：

```powershell
ssh -T git@github.com -o BatchMode=yes 2>&1
```

成功返回：

> Hi ssc8537! You've successfully authenticated, but GitHub does not provide shell access.

说明认证通过。

---

## 4. 后续使用方式

配置完成后，所有 `git clone`、`git push`、`git pull` 操作均已支持 SSH 协议的 GitHub 仓库。

### 4.1 克隆仓库（SSH 方式）

```powershell
git clone git@github.com:ssc8537/仓库名.git
```

### 4.2 已有仓库添加远程

```powershell
git remote add origin git@github.com:ssc8537/仓库名.git
git push -u origin main
```

### 4.3 推送/拉取

```powershell
git push
git pull
```

所有操作都会自动使用 SSH 密钥认证，无需输入密码。

---

## 5. 本机对应的 GitHub 仓库

| 项目 | 地址 |
|------|------|
| AutoClicker | [ssc8537/AutoClicker](https://github.com/ssc8537/AutoClicker) |

克隆方式：

```powershell
git clone git@github.com:ssc8537/AutoClicker.git
```

已有本地仓库关联远程：

```powershell
git remote add origin git@github.com:ssc8537/AutoClicker.git
git push -u origin main
```

---

## 6. 重要注意事项

- 私钥文件 `id_ed25519` 是敏感凭据，**不要分享、不要上传、不要提交到代码仓库**。
- 如果以后更换电脑或重装系统，需要重新生成密钥并添加到 GitHub。
- 如果 SSH 连接遇到问题，检查公钥是否仍存在于 [GitHub SSH Keys 设置页](https://github.com/settings/keys)。
- Git 的默认分支名可能为 `main`，推送时注意本地和远程分支名一致。

---

## 附录：连接方式变更记录

| 日期 | 操作 | 执行者 |
|------|------|--------|
| 2026-07-15 | 设置 git user.name / user.email | Codex |
| 2026-07-15 | 生成 ed25519 SSH 密钥对 | Codex |
| 2026-07-15 | 创建 SSH config 自动匹配 GitHub | Codex |
| 2026-07-15 | 公钥手动添加到 GitHub 账户 | 用户 |
| 2026-07-15 | SSH 连接验证通过 | Codex |
