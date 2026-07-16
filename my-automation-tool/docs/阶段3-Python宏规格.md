# 阶段 3：单 Python 宏规格

> 状态：已实现，待用户验收 | 日期：2026-07-16
>
> 本文档是当前脚本格式的唯一规格；它取代阶段 2 的 JSON 运行格式。

## 一、目标与边界

项目保留 Quickinput 的热键、切换/按下执行、全局禁用、可中断播放和鼠标窗口抑制逻辑；用户宏改为可信本地 Python 文件。优秀案例 2 只参考 `send_key` 风格的小输入接口，不引入图像识别、状态判断或角色 AI。

本步只加载一个 `scripts/hello_world.py`，固定 F9 和 F12。不做多脚本、脚本发现、UI 编辑器、鼠标、组合键或自定义热键。

## 二、Python 脚本格式

```python
NAME = "hello world"
HOTKEY = "f9"
MODE = "down"      # switch 或 down
COUNT = 1            # 0 为无限，1–99 为完整轮数
SPEED = 1.0          # 0.01–8.0，越大越快

def run(player):
    player.tap("h")
    player.sleep(50)
```

| 元数据 | 阶段 3 规则 |
|---|---|
| `NAME` | 非空字符串。 |
| `HOTKEY` | 必须为 `f9`。 |
| `MODE` | `switch` 或 `down`。 |
| `COUNT` | 整数 `0–99`。 |
| `SPEED` | 数字 `0.01–8.0`。 |
| `run(player)` | 必须存在且可调用。 |

`player.tap(key, hold_ms=20)` 使用 SendInput 真实按下并释放一个受支持单键。`player.sleep(ms)` 按 `ms / SPEED` 等待。脚本必须使用这两个接口，F12、按住模式松开和关闭窗口才能立即中断并释放按键。

## 三、加载和停止

每次 F9 启动前，程序直接从磁盘读取并编译 Python 源码，不使用 Python 字节码缓存。Ctrl+S 保存后，无需重启，下一次 F9 使用新的 `COUNT`、`MODE`、`SPEED` 和 `run` 内容；正在运行的一轮保持启动时快照。

脚本语法或元数据无效时，程序保留最后一次有效宏但拒绝本次启动，显示红色“Python 宏无效，未启动”提示。Python 宏被视为用户自己编写的可信本地代码，不提供安全沙箱。

## 四、后续范围

本步验收后再单独规划：多个 Python 脚本及各自热键、`key_down/key_up`、鼠标动作、脚本管理 UI 和编辑器。
