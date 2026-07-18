# Python 宏完整编写说明

## 先了解当前范围

本项目的宏是可信本地 Python 文件。程序只会在 F9 启动已启用宏时加载它；编辑、列表扫描和 AI 提示词不会执行宏代码。F12 会全局禁用并停止运行，F2 仍只是界面占位。

## 必须保留的文件结构

```python
NAME = "示例角色"
HOTKEY = "f9"
MODE = "switch"
COUNT = 1
SPEED = 1.0

def run(player):
    player.tap("e")
    player.sleep(300)
```

| 项目 | 规则 |
|---|---|
| `NAME` | 非空显示名称。 |
| `HOTKEY` | 必须固定为 `"f9"`，不可自定义。 |
| `MODE` | 只能是 `"switch"` 或 `"down"`。 |
| `COUNT` | 0–99 的整数。 |
| `SPEED` | 0.01–8.0 的数字；越大则 `sleep` 实际等待越短。 |
| `run(player)` | 必须存在；所有自动按键都从这里开始。 |

保存时会执行静态检查；缺少字段、字段错误或没有 `run(player)` 都会被拒绝，旧的可用文件不会被覆盖。

## 当前可用函数

### `player.tap(key, hold_ms=20)`

发送一个物理键盘按下与释放。`key` 是受支持的单键名称，例如 `"1"`、`"e"`、`"q"`、`"r"`、`"space"`、`"f"`；不支持的键会报错。`hold_ms` 是按住时长，必须是至少 1 的整数，默认 20 毫秒。停止、异常或关闭时会释放已按下的键。

### `player.sleep(ms)`

等待动作间隔。`ms` 可为 0 或正数；实际等待为 `ms / SPEED`。F12、`down` 模式松开 F9 或关闭程序会中断等待，不会继续执行下一步。

### 共享键位语义函数

`player.切换(1|2|3)`、`player.战技()`、`player.声骸()`、`player.大招()`、`player.跳跃()`、`player.处决()` 会发送“设置”页保存的共享物理键。默认分别是 1/2/3/E/Q/R/Space/F；每个宏都使用同一份 `config/game_keybinds.ini`。这些函数不识别角色、动画、CD 或其他游戏状态，只是复用 `player.tap()` 的可中断键盘发送路径。

### 鼠标函数（仅当前位置左/右键）

```python
def run(player):
    player.mouse_down("left")
    player.sleep(400)
    player.mouse_up("left")
    player.mouse_click("right")
    player.mouse_repeat(3, "left", interval_ms=100)
```

| 函数 | 规则 |
|---|---|
| `player.mouse_down(button="left")` | 按住左/右键。相同按钮重复按下不会重复发送系统事件。 |
| `player.mouse_up(button="left")` | 松开该播放器此前按住的左/右键；重复松开安全无副作用。 |
| `player.mouse_click(button="left", hold_ms=10)` | 按下后 10ms 松开；F12、关闭或停止等待时仍会松开。 |
| `player.mouse_repeat(count, button="left", interval_ms=10)` | 只能重复 1–100 次；两次点击之间按真实时间至少 10ms，不受 `SPEED` 缩短。 |

`button` 只能是精确小写的 `"left"` 或 `"right"`。不支持中键、侧键、滚轮、移动鼠标或坐标点击。一个 F9 宏轮次无论正常结束、抛出错误、被 F12 停止或关闭窗口，都会释放它尚未释放的左右键；但仍应在脚本中按下后明确写出对应的 `mouse_up()`，让代码容易阅读和审查。

## 当前物理按键参考

| 物理键 | 当前参考名称 | 是否能在宏中使用 |
|---|---|---|
| 1、2、3 | 角色切换 | 可以通过 `player.tap` 发送物理键 |
| E | 战技 | 可以通过 `player.tap` 发送物理键 |
| Q | 声骸技能 | 可以通过 `player.tap` 发送物理键 |
| R | 大招 | 可以通过 `player.tap` 发送物理键 |
| Space | 跳跃 | 可以通过 `player.tap` 发送物理键 |
| F | 处决 | 可以通过 `player.tap` 发送物理键 |
| 鼠标左键 | 平A | 可用 `mouse_down` / `mouse_up` / `mouse_click` / `mouse_repeat` |
| 鼠标右键 | 闪避 | 可用 `mouse_down` / `mouse_up` / `mouse_click` / `mouse_repeat` |

这是默认物理键参考；设置页保存后，语义函数会使用新物理键。F2、F9、F12 为程序保留键，不能配置；重复或不支持的键也会被拒绝。

## 角色编号和通用切人规则

每份三角色宏都应在文件开头用 Python 注释写清角色编号，例如“1号角色：名称”。这只帮助人类阅读；切换可使用 `player.切换(1)`、`player.切换(2)`、`player.切换(3)`，或需要固定物理键时使用 `player.tap()`。

三个角色之间共用同一套规则，覆盖 1→2、1→3、2→1、2→3、3→1、3→2：

| 情形 | 必须等待 | 写法 |
|---|---:|---|
| 任意不同角色 A→B | 切换前至少 50ms | `player.sleep(50)` 后 `player.tap("B")` |
| 刚 A→B 后立即回切 B→A | 从成功切到 B 起至少 1080ms | `player.tap("B")`、`player.sleep(1080)`、`player.tap("A")` |
| 刚发送 R 后切到任一其他槽位 | R 后立即等待 1500ms | `player.tap("R")`、`player.sleep(1500)`、`player.tap("1"/"2"/"3")` |

1080ms 由 1000ms 冷却和额外 80ms 安全余量组成。R 成功发送后立刻开始的 1500ms 是作者规则，它覆盖普通切人 50ms 与回切 1080ms；等待结束后可以直接发送任一其他数字槽位。程序不会识别游戏动画、检测切人 CD 或当前角色，也不提供角色语义 API 或自动输入逻辑。实际按下数字键可以立即发生；等待是切换前或回切冷却期间必须满足的时间窗口。三角色仍由同一个 `run(player)` 顺序执行，不代表多宏并发或角色语义 API 已实现。

```python
# 角色编号说明
# 1号角色：请填写名称
# 2号角色：请填写名称
# 3号角色：请填写名称

def run(player):
    player.sleep(50)     # 任意 A→B 切换前的窗口
    player.tap("2")
    player.sleep(1080)   # 2→1 回切的冷却加安全余量
    player.tap("1")
    player.tap("R")
    player.sleep(1500)   # 覆盖普通切人和回切等待
    player.tap("2")
```

## 不找 AI 时如何自己写

复制上面的完整文件结构，修改 `NAME`，在 `run(player)` 中按顺序写已发布的键盘或鼠标函数和 `sleep`。每个动作后加入足够等待；先保存，再在安全的目标窗口中按现有教程测试。不要改 F9、F12、F2，不要写坐标鼠标、图像识别、角色判断或未发布函数。

## 让 AI 协助时

在软件中打开“AI 提示词”，可在窗口下方查看当前提示词和默认备份的绝对路径。所有作者和使用者都可用记事本直接编辑 `config/ai_prompt.txt`；保存后关闭并重新打开提示词窗口即可生效。编辑出错时，用 `config/ai_prompt.default.txt` 人工覆盖当前文件恢复。用户编辑的本地文字不代表软件新增能力；只有用户明确要求时，AI 才可更新随仓库交付的默认模板。

填写 1号、2号、3号角色名称、动作、物理键和时序后复制。要求 AI 返回完整文件和角色编号注释，粘贴回编辑器保存。阅读 AI 返回内容，确认它只调用当前已发布函数，并遵守 50ms/1080ms 规则和 R 后 1500ms 规则，再进行人工测试。软件内 AI 提示词尚未因 Stage 3M 自动更新；若要让其生成鼠标函数，必须由用户明确要求更新提示词。
