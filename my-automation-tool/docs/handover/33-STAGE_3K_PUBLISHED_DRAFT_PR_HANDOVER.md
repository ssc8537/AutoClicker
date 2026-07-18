# Stage 3K 发布与草稿 PR 交接

日期：2026-07-18  
状态：已提交并推送；Stage 3K Windows 验收仍待用户确认  
分支：`codex/v021-ui-shell`  
远端：`origin` / `ssc8537/AutoClicker`

## 发布事实

- 用户明确授权提交当前整个工作区。
- `1e0428f`：`Stage 3K macro workflow and keybinds`，包含当前工作区 103 文件的累计 Stage 1–3K 内容。
- `3d903f2`：`Clarify keybind save timing`，修正共享键位保存提示：新映射会在下一次宏执行使用，重新按 F9 是最明确的触发方式。
- HTTPS Git 因 `github.com:443` 连接失败不能推送；本机 SSH 身份认证有效，但 Git 内嵌 SSH 会被 `~/.ssh/config` 的 UTF-8 BOM 阻断。发布时仅对命令使用 `ssh -F /dev/null` 绕过该配置，未修改用户 SSH 文件。
- SSH 远端 SHA 已核验为 `3d903f2ffe190a11cc275b99fec08ce243867e9b`。
- 草稿 PR：<https://github.com/ssc8537/AutoClicker/pull/3>，从 `codex/v021-ui-shell` 指向 `master`。

## 验证与后续

`python -m unittest discover -s tests -v` 52/52 通过；编译和差异检查通过。未启动真实 GUI、未发送真实输入。用户仍需按 `../test-plans/STAGE_3K_FEEDBACK_DELETE_ACTIVE_EDIT_MANUAL_TEST.md` 完成 Windows 验收；通过前只修复教程可复现问题，禁止进入鼠标、多宏并行、Stage 4T 或合并 PR。
