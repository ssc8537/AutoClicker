# 当前交接：Stage 15 与 VV025 已发布

安全回退基线已发布：提交 `6e4caf0`、标签 `VV023-accepted-baseline`、分支 `codex/v021-ui-shell`。根 `PRODUCT_REQUIREMENTS.md` 是全部真实需求，根 `PROJECT_ROADMAP.md` 是唯一阶段路线；历史阶段文档已清理，优秀案例源码、源码、测试、用户宏/config 和视觉源保留。

用户已确认上一份 Stage 10–11 教程步骤 1、2、3、4 全部正确：统一图标、Markdown 首次顶部、启动体验和秧秧/琳奈/千咲宏均通过；非模态提示词窗口此前也已确认。Stage 10–11 视为 Windows 验收完成。

Stage 12 来源：用户截图显示长宏名 OSD 左右裁切，并反馈脚本在记事本有效、游戏内完全无效果。OSD 根因是旧 `400×60` 固定窗口；现按字体宽度自动扩展，超屏时换行增高，并设为不接受焦点、鼠标穿透。优秀案例与本项目普通输入均为 VK + MapVirtualKey 扫描码 + SendInput，禁止继续猜改扫描码。案例工程要求管理员权限，而当前日志每次正式启动都警告非管理员；正式构建已加入 `--uac-admin`。SendInput 0/部分成功现在每 5 秒最多记录一次事件、管理员状态和错误码。

自动证据：122 项通过、7 项历史跳过；`compileall`、`git diff --check` 和正式 PyInstaller 构建通过。生成规格确认 `uac_admin=True`、`console=False`。正式包位于 `dist/MyAutoPlayer/MyAutoPlayer.exe`。案例专家只读核对了 `input.h`、`func.cpp`、`QPopText.h` 与案例管理员工程设置，未改代码。

用户已确认 Stage 12 教程步骤 1、2、3 全部通过：管理员正式版能在游戏前台工作，长名称 OSD 完整显示且不抢焦点，按下模式持续按住后能执行并在松开时停止。Stage 1–12 的全部毕业条件现已满足。

完整验收版本已归档并发布：标签 `VV024-graduation` 固定指向提交 `b209425ab641dca0ac05ac0451ab6c85defe023c`；GitHub 默认分支 `master` 已普通快进到该完整版本并实时核验，未强推。当前本地也切换到 `master`。下一步只在收到新的明确产品需求后建立新阶段；禁止为了延长路线擅自增加录制、OCR、坐标、驱动输入等已排除功能。不得执行、覆盖或清理用户 `macros/`、`config/`。

Stage 14 新需求：用户提供 9 个外部 QuickInput JSON，要求转换为项目 Python 宏。已新增 8 个只使用点击、等待和固定循环的可运行宏；QuickInput 点击内建的随机 10–20ms 按住/释放间隔在 Python 版固定为稳定中值 15ms，所有 JSON 显式 `ms/ex` 和 `count=rand` 原样保留。新宏统一 `ENABLED=False`，避免与现有同侧键宏并发。

`1-取消深渊XX.json` 的首动作是案例 `QiType::image`（type 11）：在指定屏幕区域以 80% 相似度匹配内嵌图片，成功后等待 20ms 并按 Esc。本项目明确不支持图像识别，因此生成 `一_取消深渊XX_需要图像识别.py` 作为默认禁用、运行时报清楚错误的安全占位；禁止改成无条件按 Esc。

用户本地已经删除 `macros/666.py`、`goodbye.py`、`hello_world.py`、`invalid_missing_run.py`、`新宏6.py`，必须保留这些删除，不得恢复。Stage 14 的图像识别占位宏也已由用户删除，两个转换宏当前启用、其余按用户选择保留；测试已改为核对这些真实发布状态，未覆盖用户宏来追求全绿。

Stage 15 已新增 `src/ui/appearance.py`：设置页可独立选择“经典粉红/樱空花园”主题与“经典顶部标签/画册侧边导航”布局，保存时原子合并 `settings.json`，并提供“恢复经典外观”。新主题只提取用户图片的樱花粉、天空蓝、薄荷绿、淡桃橙、云白和柔光卡片感，没有把人物大图铺进操作区。`table_selection.py` 通过 delegate 让淡蓝选中背景保留红、绿、紫和普通文字原色，触发页与宏库均已安装。

Stage 15 初版针对性测试共运行 29 项：23 通过、6 项历史跳过；`compileall`、`git diff --check` 和正式 PyInstaller 文件夹式管理员 EXE 构建通过。全量共 130 项时，除 7 项历史跳过外有 6 项因上述用户宏状态差异失败，不属于 UI 回归。正式 EXE 能启动并显示经典主题；离屏实图确认樱空侧边布局及红绿状态色。Windows 控制工具连续两次无法激活自定义无边框窗口，因此主题/布局真实点击仍待用户按根 `CURRENT_ACCEPTANCE.md` 验收。本轮未提交、未推送。

Stage 15 精修：从用户第 2 张参考图只读裁出 `assets/sakura-gallery-avatar.png`，未上传或生成陌生角色；头像只显示在画册侧栏顶部。侧栏由 136px 收窄为 108px，标题和四个入口居中；画册初始宽度由 920px 收到 840px，并按可用屏幕上限夹取。主窗口不再固定宽度，新增上下左右与四角共八个拖动缩放区；经典最小宽 642px、画册最小宽 760px。触发名称列与宏库名称列自动扩展，宏库序号表头/数字居中。精修后针对性测试共运行 31 项：25 通过、6 项历史跳过；编译、差异检查和正式管理员 EXE 重建通过。当前用户配置选择的樱空花园/画册侧栏保持不变。

用户已明确反馈“这一轮很完美”，Stage 15 视为 Windows 验收通过。根 `README.md` 与 `SETUP_GUIDE.md` 已更新为当前功能和人类/AI 共用配置流程；旧 `CURRENT_ACCEPTANCE.md` 已按验收完成规则移除。完整程序内容已作为 `VV025-ui-gallery-release` 普通发布到默认主干 `master`，禁止强推。

VV025 发布前证据：全量运行 131 项，124 通过、7 项历史跳过，0 失败；`compileall` 与 `git diff --check` 通过。`SETUP_GUIDE.md` 中显式 `-PythonExe` 加一次性 `-ExecutionPolicy Bypass` 的构建命令已在当前 Windows 11/PowerShell 上真实执行成功，不修改永久执行策略；正式文件夹式管理员 EXE 已重建。案例源码、`build/`、`dist/` 和日志继续由 `.gitignore` 排除；公开文件未检出密钥。远端 `origin/master` 与本地发布基线同为 `5aff3fb`，远端/本地均不存在 `VV025-ui-gallery-release` 标签，可安全普通发布。

发布事实：版本提交 `912b873bbb6c281679465160a84d3608dc491c23`，注释标签 `VV025-ui-gallery-release` 解引用到同一提交；GitHub `origin/master` 已普通快进并实时核验到该提交。当前无既定未完成阶段；后续只响应用户新的明确需求。
