# Stage 19 最终交付记录

> 用户已确认Stage 19D及此前全部功能验收通过。本文件用于核对最终源码、正式包和GitHub主干，不要求重新录制长视频。

## 交付总览

| 编号 | 交付项目 | 最终结果 |
|:---:|---|---|
| 1 | 原生开发连招 | 全屏滚动回放、全局按键时间线、外挂字幕、独立双音轨和历史浏览均已验收 |
| 2 | 正式便携包 | 管理员文件夹式EXE构建成功，随包包含原生录像核心 |
| 3 | 源码与许可 | Python/Rust源码、锁定依赖、MIT第三方许可和构建说明完整 |
| 4 | 发布隐私 | 本机录像路径、设备选择、窗口坐标、日志、视频和构建缓存均未进入提交或正式包 |
| 5 | GitHub | 使用一个发布提交正常推送默认主干`master`，不强推 |

## 第一项：正式包位置

```text
dist\MyAutoPlayer\MyAutoPlayer.exe
dist\MyAutoPlayer\native-replay\myautoplayer-native-replay.exe
```

普通用户只运行`MyAutoPlayer.exe`，不要双击`build_native_replay.ps1`。源码开发者的工具路径、构建和卸载方式见`native-replay\BUILDING.md`。

## 第二项：最终自动证据

| 检查 | 结果 |
|---|---|
| Python测试 | 200项运行，193项通过，7项环境跳过 |
| Rust测试 | 4/4通过 |
| `compileall` | 通过 |
| `git diff --check` | 通过，仅现有CRLF提示 |
| 正式EXE | 3,058,255字节 |
| 原生核心 | 718,336字节；SHA-256：`34EA839BCD953869C67CCA20FE58237BAFA0F2B2EA60E2C6DCA6A44CE1D4C45A` |
| 退出清理 | 主程序、录像核心、Cargo、Rustc进程均为0 |

## 第三项：发布包隐私核对

以下本机运行状态保留在用户源码目录，但被Git忽略，并在正式构建时排除：

| 文件 | 原因 | 正式包 |
|---|---|:---:|
| `config/replay_settings.json` | 可能包含录像保存绝对路径、麦克风和录制选项 | 不包含 |
| `config/key_monitor.json` | 包含按键窗口位置、大小和个人显示键 | 不包含 |
| `config/ai_prompt.complete.md` | 每次打开时实时生成 | 不包含 |

正式包仍包含可交付的`ai_prompt.md`、默认备份、共享键位、全局键和基础界面设置。

## 第四项：GitHub核对方法

发布后在仓库根目录运行：

```powershell
git status --short
git log -1 --oneline
git ls-remote --heads origin master
```

**正确结果：** 工作区没有未提交产品修改；本地`HEAD`与远端`refs/heads/master`使用同一个SHA。最终SHA以Git历史和本轮交付回复为准。

## 已知边界

- 用户已接受中文输入法下物理字母进入IME组合态的轻微现象；英文输入完全正确。
- 不生成`perfect.mp4`；最终视频交付始终是一份`raw.mp4`加ASS/SRT外挂字幕。
- 不调用OBS，不读取或注入游戏，不记录鼠标移动，不绕过反作弊。
- GitHub不包含正式EXE、录像、日志、构建缓存、案例源码和本机开发工具。

## 后续状态

Stage 19已完成并固化。当前没有自动开始的下一阶段，等待用户提出新的明确需求。
