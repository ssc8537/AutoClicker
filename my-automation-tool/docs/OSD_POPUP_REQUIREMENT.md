# 需求更新：屏幕提示文本功能

> 最后更新：2026-07-15 | 状态：已记录需求，待实现

## 一、需求背景
用户在打游戏时，可能不小心按到了某个按键，自动化脚本就被触发了。
需要一个屏幕提示文本，在脚本执行时自动弹出到电脑最前面。

## 二、功能需求

### 2.1 提示文本触发条件
按下自动化按键脚本的绑定按键时触发。

### 2.2 提示内容
| 场景 | 显示文本 | 颜色 |
|------|---------|------|
| 脚本开始执行 | [脚本名] 脚本执行成功 | 绿色 |
| 脚本结束 / 松开按键 | [脚本名] 脚本结束 | 红色 |

### 2.3 显示样式
- 位置：屏幕顶部居中
- 形状：矩形浮层
- 层级：在所有窗口最前面（Always on Top）
- 自动消失：显示一段时间后自动淡出

### 2.4 自定义开关
用户可以打开或关闭这个屏幕提示功能。
默认状态：开启

## 三、实现参考（来源于优秀案例1-Quickinput）
Quickinput 的 PopsUi.cpp 实现了一套完整的提示框系统，
支持 12 种事件类型，每种可独立配置文本、音效、颜色。
底层使用 Qi::popText 全局 Overlay 窗口。

## 四、本项目的实现建议
使用 PySide6 创建一个无边框、透明背景、置顶的 QLabel 浮层窗口：
- Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
- Qt.WA_TranslucentBackground

### 配置项（settings.json 新增）
{
  "popup_enabled": true,
  "popup_position_x": 50,
  "popup_position_y": 10,
  "popup_size": 24,
  "popup_duration_ms": 2000,
  "popup_success_color": "#00FF00",
  "popup_end_color": "#FF0000"
}
