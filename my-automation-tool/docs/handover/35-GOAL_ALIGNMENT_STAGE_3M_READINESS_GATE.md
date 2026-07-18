# Stage 3M 接手对齐与需求门槛交接

日期：2026-07-18
状态：GoalAlignmentMonitor 发现的文档 DRIFT 已纠正；Stage 3M 仍未 READY

## 本次已核实

- 用户已确认 Stage 3K 反馈教程 1–6 全部通过；该阶段不包含鼠标、多宏并行、游戏识别或托盘。
- 功能分支 `codex/v021-ui-shell` 已发布，草稿 PR #3 指向 `master`，未合并。
- `CURRENT_PRODUCT_DECISIONS.md` 与 `CURRENT_HANDOVER.md` 的旧“Stage 3K 待验收”文字已纠正；AI 提示词尚未更新不表示已发布的键盘语义 API 不可用。

## 唯一下一步

RequirementCertifier 接手初审已给出 **NOT READY**。本次负责人不得自动再次调用该员工或开始实现。下一步只可由 CodeExplorer 和 KnowledgeExpert 补充公开 API、左右键边界、坐标语义、有限重复上限、F12/异常/关闭释放、自动测试和记事本验收的本地证据；若仍存在会改变安全或验收结果的选择，再向用户提出最少问题。未给出新的负责人 `READY` 前不得修改运行代码。

## 已补充的只读证据

- `src/core/input_simulator.py:197-249` 已能发出鼠标点击、左/右/中按下和释放；`src/core/script_player.py:15-81` 只管理键盘，因此尚不能保证中断时释放鼠标。
- 优秀案例 1 的解释器区分鼠标 `up/down/click`，但与录制、坐标、窗口、JSON/QIM 架构耦合；只可借鉴动作分离，不能复制。
- 优秀案例 2 在取消或运动切换时显式释放鼠标；只可借鉴“清理必须释放”的安全原则，图像识别、坐标点击和角色状态机均排除。

候选安全范围是当前指针位置的左/右键按下、释放、单击和有限重复；不实现中键、侧键、坐标移动、滚轮、录制、窗口绑定、图像识别、游戏判断或多宏。仍待用户锁定：有限重复的最大次数与最小间隔；在此之前 Stage 3M 继续 **NOT READY**。
