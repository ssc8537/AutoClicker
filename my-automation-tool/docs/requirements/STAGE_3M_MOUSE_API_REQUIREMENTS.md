# Stage 3M 鼠标语义 API 需求规格

日期：2026-07-18
状态：实施前 READY（仅本文件范围）

## 目标

让唯一已启用的可信 Python 宏能在当前鼠标位置安全地执行左/右键按下、等待、松开、单击和有限重复；F12、异常和关闭不会遗留程序发送的按住鼠标键。

## 公开 API

```python
player.mouse_down(button="left")
player.sleep(400)
player.mouse_up(button="left")

player.mouse_click(button="left")
player.mouse_repeat(count, button="left", interval_ms=10)
```

- `button` 仅可为精确小写字符串 `"left"` 或 `"right"`。
- `mouse_down`/`mouse_up` 只管理当前 `ScriptPlayer` 自己发送的状态；对同一按钮重复调用是幂等的，不重复发送系统事件。
- `mouse_click` 发送一次按下及释放，默认按住 10ms；若中断，仍在 finally 中释放。
- `mouse_repeat` 的 `count` 必须是非 bool 整数 1–100；`interval_ms` 必须是非 bool 整数且不小于 10。每次单击之间按真实时间等待该间隔，不受 `SPEED` 缩短；等待可被停止中断。
- 每次 F9 宏轮次的 finally 必须释放该轮次尚未释放的左/右键；因此正常返回、普通异常、`ScriptInterrupted`、F12 和窗口关闭均不遗留本程序按键。

## 范围外

不实现中键、侧键、滚轮、坐标移动、坐标点击、录制、窗口绑定、图像识别、游戏状态判断、额外热键、多宏并行、JSON/QIM 或 AI 提示词更新。

## 验证

- 自动测试用依赖注入的假鼠标发送器覆盖左右键动作、重复参数拒绝、最小间隔、停止/异常/正常结束释放与原有键盘回归。
- 用户仅在记事本或安全空白窗口按中文教程验证左/右键按住—等待—松开、单击/有限重复、F9/F12；不在游戏中验收，不测试坐标移动或自动判断。
