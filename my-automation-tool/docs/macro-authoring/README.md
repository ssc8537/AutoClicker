# Python 宏作者手册

软件内“AI 提示词”窗口每次打开都会读取 `config/ai_prompt.txt`。它既供人类直接阅读，也可复制给 AI；窗口会显示当前文件和 `config/ai_prompt.default.txt` 默认备份的绝对路径。本目录的详细手册补充示例和边界。

可以用记事本直接编辑当前文件；保存后关闭并重新打开窗口生效。当前文件缺失时程序会用默认备份恢复；当前文件不是 UTF-8 时程序只显示默认文本，不会覆盖它。默认备份只供人工恢复，程序绝不自动改写。

- [完整编写说明](AUTHORING_GUIDE.md)

当前发布 `player.tap(key, hold_ms=20)`、`player.sleep(ms)`、`player.切换(1|2|3)`、`player.战技()`、`player.声骸()`、`player.大招()`、`player.跳跃()`、`player.处决()`，以及仅左/右键的 `player.mouse_down()`、`player.mouse_up()`、`player.mouse_click()`、`player.mouse_repeat()`。语义函数使用“设置”页保存的共享键盘物理键；鼠标不支持坐标、滚轮、录制或游戏识别，新热键和自动判断仍未发布，不能写入宏。
