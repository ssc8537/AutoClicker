# 需求更新：音效功能参考（来源于 优秀案例1-Quickinput）

> 最后更新：2026-07-15 | 状态：已记录参考，待实现 | 操作者：Codex
>
> **注意**：本文件仅作参考，记录音效功能的设计思路。用户已表示"未来可能也要添加音效"。
> 当前阶段的重点先实现屏幕提示文本功能，音效功能留到后续阶段实现。

---

## 一、Quickinput 的音效系统

Quickinput 的 Pops（提示框）系统中，**每个事件类型都可以绑定一个音效文件**。

### 1.1 音效文件清单

项目路径：优秀案例1-Quickinput/Quickinput-main/source/res/sound/

| 文件名 | 大小 | 预期用途 |
|--------|------|---------|
| notify.wav | 412 KB | 通用通知音 |
| on.wav | 408 KB | 启用音 |
| off.wav | 408 KB | 禁用音 |
| run.wav | 353 KB | 运行音（脚本执行时） |
| stop.wav | 353 KB | 停止音（脚本结束时） |

### 1.2 音效与事件的绑定关系

在 PopsUi.cpp 中，每个事件同时绑定了文本和音效：

| 事件类型 | 音效变量 | 文本变量 | 说明 |
|---------|---------|---------|------|
| 启用 | qe.s | qe.t | 全局启用时播放 |
| 禁用 | qd.s | qd.t | 全局禁用时播放 |
| 窗口匹配成功 | we.s | we.t | 进入目标窗口时 |
| 窗口匹配失败 | wd.s | wd.t | 离开目标窗口时 |
| 点击模式开始 | qce.s | qce.t | 点击模式启动时 |
| 点击模式结束 | qcd.s | qcd.t | 点击模式停止时 |
| 切换模式开始 | swe.s | swe.t | 切换模式启动时 |
| 切换模式结束 | swd.s | swd.t | 切换模式停止时 |
| 按住模式开始 | dwe.s | dwe.t | 按住热键时 |
| 按住模式结束 | dwd.s | dwd.t | 松开热键时 |
| 松开模式开始 | upe.s | upe.t | 按下时 |
| 松开模式结束 | upd.s | upd.t | 松开时 |

### 1.3 音效播放函数

从 unc.h 提取：

`cpp
// 播放音效文件，sync=true 时同步播放（阻塞）
void SoundPlay(const QString& sound, bool sync);
`

调用示例（从 PopsUi.cpp 的 eventFilter 提取）：

`cpp
// 鼠标悬停在音效输入框上时试听
QiFn::SoundPlay(p->s, false);  // 异步播放
Sleep(10);
`

---

## 二、音效的触发时机分析

通过对 PopsUi.cpp 和 unc.h 的分析，音效的触发时机如下：

1. **事件触发时**：当宏/脚本被触发时，同时播放音效和显示文本
2. **设置预览时**：用户在设置界面悬停在音效输入框上时，立即播放预览
3. **不同事件不同音效**：开始和结束使用不同的音效（如 un.wav vs stop.wav）

---

## 三、本项目的音效实现建议（未来参考）

### 3.1 最小方案：使用 winsound（Python 内置）

`python
import winsound

def play_sound(sound_path: str, async_mode: bool = True):
    """播放音效文件。"""
    flags = winsound.SND_FILENAME | winsound.SND_NODEFAULT
    if async_mode:
        flags |= winsound.SND_ASYNC
    winsound.PlaySound(sound_path, flags)
`

### 3.2 增强方案：使用 pygame.mixer

`python
import pygame
pygame.mixer.init()
sound = pygame.mixer.Sound("sound/run.wav")
sound.play()
`

### 3.3 配置项（settings.json 扩展）

`json
{
  "sound_enabled": true,
  "sound_run": "sound/run.wav",
  "sound_stop": "sound/stop.wav",
  "sound_notify": "sound/notify.wav"
}
`

---

## 四、与屏幕提示文本的关系

音效和屏幕提示文本属于同一套系统（Quickinput 的 Pops 系统）。

**建议实现顺序**：
1. 先实现屏幕提示文本功能（当前需求）
2. 后续阶段再加入音效功能

两者共享相同的触发时机和配置管理。

---

**参考来源**：优秀案例1-Quickinput 的 PopsUi.cpp、unc.h、sound/*.wav

