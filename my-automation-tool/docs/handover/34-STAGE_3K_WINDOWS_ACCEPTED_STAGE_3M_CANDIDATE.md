# Stage 3K Windows 验收归档与 Stage 3M 候选交接

日期：2026-07-18
状态：Stage 3K 已 Windows 验收通过；Stage 3M 仅为下一候选，未 READY
Git：已发布功能分支 `codex/v021-ui-shell`；草稿 PR #3 未合并

## 已确认事实

用户已按 `../test-plans/STAGE_3K_FEEDBACK_DELETE_ACTIVE_EDIT_MANUAL_TEST.md` 确认 1–6 全部通过：共享键位表可见、启用宏可编辑保存改名、中文确认删除/回收站删除及 F9/F12/F2 回归均正确。该验收不包含游戏输入、鼠标、多宏并行、角色/动画/CD 判断或系统托盘。

发布记录：功能提交与说明已普通推送到 `codex/v021-ui-shell`；草稿 PR #3 指向 `master`，未合并。最终 Windows 验收通过不自动授权合并、Stage 3M 或多宏并行。

## 唯一下一候选

Stage 3M：仅研究可信 Python 宏中的鼠标左/右键按下、释放、单击及有限重复。用户已举例“按下鼠标 → `player.sleep(400)` → 松开鼠标”作为候选场景。下一位负责人必须先完成新的 GoalAlignmentMonitor 与 RequirementCertifier 门槛，查询优秀案例/输入层证据，再决定公开 API、按键冲突、F12/异常/关闭释放、有限次数、自动测试和记事本验收；未获 READY 前不得写鼠标代码。
