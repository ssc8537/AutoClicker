# 环境配置说明

> 任何 AI 接手本项目时，先看这个文件，按步骤配置环境。
> 本项目是 Python + PySide6 桌面应用程序。

---

## 系统要求

- Windows 10 或 Windows 11
- Python 3.9 或更高版本（推荐 Python 3.12+）
- 网络连接（用于安装依赖包）

---

## 第一步：安装 Python

1. 打开 https://www.python.org/downloads/
2. 下载最新 Python 3.x 版本
3. 安装时务必勾选"Add Python to PATH"
4. 安装完成后，打开 PowerShell 验证：python --version

---

## 第二步：创建虚拟环境（推荐）

在项目根目录执行：

  python -m venv venv
  .\venv\Scripts\Activate.ps1

激活后，PowerShell 提示符前面会显示 (venv)。

---

## 第三步：安装依赖

确保虚拟环境已激活，然后在项目根目录执行：

  pip install -r my-automation-tool/requirements.txt

requirements.txt 包含：
| 包名 | 用途 |
|------|------|
| pyside6 | 图形界面（窗口、OSD浮层） |
| pynput | 输入模拟（备用） |
| keyboard | 全局热键监听 |

---

## 第四步：运行程序

  python my-automation-tool/main.py

### 测试方法
1. 程序启动后，窗口顶部显示红色"热键已禁用"
2. 按 F12 - 标签变绿色"热键已启用"
3. 光标放在记事本中，按 F9
4. 程序自动打出 Hello World，同时屏幕顶部弹出绿色提示
5. 按 F12 可随时禁用所有热键

---

## 常见问题

Q：程序报错"keyboard 权限不足"
A：右键 PowerShell 以管理员身份运行，再运行程序。

Q：依赖安装失败
A：尝试升级 pip：python -m pip install --upgrade pip

Q：虚拟环境激活失败
A：先执行 Set-ExecutionPolicy RemoteSigned -Scope CurrentUser，然后重新激活。

---

## 给 AI 的提示

当你（AI）接手本项目时：
1. 检查 venv/ 目录是否存在（虚拟环境）
2. 如果存在，执行 .\venv\Scripts\Activate.ps1 激活
3. 检查 requirements.txt 是否已安装
4. 直接运行 python my-automation-tool/main.py 测试
5. 查看 logs/app.log 排查问题
