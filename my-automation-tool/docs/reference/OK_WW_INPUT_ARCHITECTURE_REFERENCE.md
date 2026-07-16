# ok-ww 输入与模块化参考索引

## 可借鉴的实现思想

| 层次 | 源码证据 | 本项目适配 |
|---|---|---|
| 高层脚本调用任务接口 | `src/char/BaseChar.py:47,844` | Python 宏只调用 `player.tap()`、`player.sleep()` 等小接口 |
| 任务层封装输入 | `src/task/BaseWWTask.py:345` | `src/core/script_player.py` 负责真实 SendInput、停止和按键释放 |
| 模块化职责 | `src/char` 与 `src/task` 分离 | 未来拆分为 `domain/services/ui`，不让页面直接做输入 |

## 明确排除

图像识别、OpenCV/YOLO、战斗状态机、角色 AI、刷图/登录任务、游戏状态判断及其配置。当前项目只执行用户明确写好的固定键盘序列。

## 当前接口约束

Python 宏必须使用已提供的 `player.tap(key, hold_ms=20)` 与 `player.sleep(ms)`，这样 F12、热键停止和窗口关闭才可立即中断并释放按键。后续的按下/释放/鼠标接口需单独设计和验收。
