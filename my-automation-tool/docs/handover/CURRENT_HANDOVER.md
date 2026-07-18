# 当前交接：Stage 5P 已验收；Stage 6 多宏触发设计中

Stage 4T 原教程 1–5 与 Stage 5P EXE 验收均已由用户通过。便携版 `dist/MyAutoPlayer/MyAutoPlayer.exe` 使用 EXE 同级宏、配置、日志；窗口、任务栏和托盘使用自制粉色图标，名称为“自动连招”。停止/自然结束 OSD 已按本轮实际宏名显示。下一候选为 Stage 6 多宏独立触发：只允许顺序执行，F12 统一停止；案例专家正在只读取证，尚未写 Stage 6 代码。

自动证据：66/66 单测、编译、差异检查和真实 PyInstaller 构建通过；构建产物含 EXE、同级 config/macros/logs 及打包 SVG。Stage 5P 已获用户 Windows 验收；Stage 6 尚无实现或验收教程。

已发布：GitHub 分支 `codex/v021-ui-shell` 的版本提交为 `ab3f5f8`，回退标签为 `v020-stage4t-and-ui-polish`。用户已确认清理旧员工体系、历史交接、旧审查/治理文档和 `项目管理` 版本快照；需要时从 Git 标签读取。总阶段路线为 `../../PROJECT_TASKS.md`。永久案例专家规则在根 `AGENTS.md` 与 `.codex/agents/case-expert.md`：只有技术/案例难题才调用。新接手只读根 `AGENTS.md`、本文件和 `git status --short`；开始新功能才读它的一页规格/教程。个人宏已按用户授权纳入 V020。
