# 9-给下一位AI工作-C1自动检测与唯一活动状态终审交接

> 日期：2026-07-17｜状态：C1 最小实现待人工验收；自动检测与唯一活动状态扩展仅待实施前终审。

## Git 与工作区

- 分支：`codex/v021-ui-shell`；本地基线：`51ad74a`。
- 本轮未提交、未推送；不得清理、覆盖或提交现有工作区。远端在 `51ad74a` 后未实时核验，不得猜测。
- 用户已通过 V023 外观、安全与中文显示，但明确本次不发布。

## 已完成 C1 最小实现

- `scripts/hello_world.py` 已迁移至 `macros/hello_world.py`；顶层扫描、校验、手动刷新、有效宏选择和无选择 F9 安全空操作已实现。
- 自动验证：`python -m unittest discover -s tests -v` 26/26 通过；`python -m compileall -q main.py src macros` 与 `git diff --check` 通过。
- 尚未进行本轮 Windows GUI/真实输入验收；教程入口为 `docs/test-plans/C1_MANUAL_TEST.md`。

## 当前唯一任务

在实施前终审后，实现“取消刷新、Qt 自动检测、文件校验与唯一活动状态分离”。有效宏状态可启用/停用且全程仅一个活动宏；无效宏显示中文错误且不可启用；保存、删除、改名后自动更新。

两个优秀案例均没有后台文件监听。自动监听是本项目 fail-closed 设计：Qt 主线程 `QFileSystemWatcher` 监听目录与文件，150ms 防抖后全量重建；监听回调不执行宏，F9 不隐式扫描。活动宏消失或失效时，停止播放器、`mark_finished("f9")`、清空选择并显示中文原因。

未获新的 GoalAlignmentMonitor `ALIGNED` 和 RequirementCertifier `READY` 前，禁止修改自动检测、状态列、热键、输入或运行配置。

## 严格边界与恢复顺序

- 禁止编辑、保存、重命名、创建宏、导入导出、多宏并发、额外热键、鼠标、窗口、音效、录制、定时、JSON/QIM、提交或推送。F12 仍唯一总开关，F2 仍仅占位。
- 先读 `AGENTS.md`、项目负责人说明、`PROJECT_OUTLINE.md`、`REVIEW_LOG.md`、当前交接、7/8/9 号交接、产品决定与 C1 规格；第一员工 GoalAlignmentMonitor，第二员工 RequirementCertifier。
- 实施后必须补自动测试、编译、差异检查、中文小白教程和记事本人工验收；最后 AntiHallucination 与 Handover 归档。
