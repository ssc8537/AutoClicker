# 当前交接：Stage 1–12 全部验收，当前范围毕业

安全回退基线已发布：提交 `6e4caf0`、标签 `VV023-accepted-baseline`、分支 `codex/v021-ui-shell`。根 `PRODUCT_REQUIREMENTS.md` 是全部真实需求，根 `PROJECT_ROADMAP.md` 是唯一阶段路线；历史阶段文档已清理，优秀案例源码、源码、测试、用户宏/config 和视觉源保留。

用户已确认上一份 Stage 10–11 教程步骤 1、2、3、4 全部正确：统一图标、Markdown 首次顶部、启动体验和秧秧/琳奈/千咲宏均通过；非模态提示词窗口此前也已确认。Stage 10–11 视为 Windows 验收完成。

Stage 12 来源：用户截图显示长宏名 OSD 左右裁切，并反馈脚本在记事本有效、游戏内完全无效果。OSD 根因是旧 `400×60` 固定窗口；现按字体宽度自动扩展，超屏时换行增高，并设为不接受焦点、鼠标穿透。优秀案例与本项目普通输入均为 VK + MapVirtualKey 扫描码 + SendInput，禁止继续猜改扫描码。案例工程要求管理员权限，而当前日志每次正式启动都警告非管理员；正式构建已加入 `--uac-admin`。SendInput 0/部分成功现在每 5 秒最多记录一次事件、管理员状态和错误码。

自动证据：122 项通过、7 项历史跳过；`compileall`、`git diff --check` 和正式 PyInstaller 构建通过。生成规格确认 `uac_admin=True`、`console=False`。正式包位于 `dist/MyAutoPlayer/MyAutoPlayer.exe`。案例专家只读核对了 `input.h`、`func.cpp`、`QPopText.h` 与案例管理员工程设置，未改代码。

用户已确认 Stage 12 教程步骤 1、2、3 全部通过：管理员正式版能在游戏前台工作，长名称 OSD 完整显示且不抢焦点，按下模式持续按住后能执行并在松开时停止。Stage 1–12 的全部毕业条件现已满足。

完整验收版本已归档并发布：标签 `VV024-graduation` 固定指向提交 `b209425ab641dca0ac05ac0451ab6c85defe023c`；GitHub 默认分支 `master` 已普通快进到该完整版本并实时核验，未强推。当前本地也切换到 `master`。下一步只在收到新的明确产品需求后建立新阶段；禁止为了延长路线擅自增加录制、OCR、坐标、驱动输入等已排除功能。不得执行、覆盖或清理用户 `macros/`、`config/`。
