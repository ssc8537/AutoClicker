# 项目结构

> 更新：v020.3 项目负责人和团队协作闭环。优秀案例目录仅本地参考，不纳入 Git。

```text
自动连点器/
├── .codex/agents/                    # 项目负责人 + 十一个专项角色规范
├── my-automation-tool/               # 可运行 Python 应用
│   ├── config/                       # 全局应用配置
│   ├── docs/
│   │   ├── handover/                 # 当前入口 + 不覆盖的编号历史交接
│   │   ├── reference/                # 案例索引、UI 规格和已许可参考截图
│   │   ├── team/                     # 团队使用说明与里程碑记录
│   │   └── test-plans/               # 当前阶段的自动/人工验收清单
│   ├── scripts/                      # 用户可信 Python 宏
│   ├── src/
│   │   ├── core/                     # 热键、输入、播放器、Python 宏加载
│   │   └── ui/                       # 当前 OSD；未来放主窗及页面
│   ├── tests/                        # 自动化测试
│   ├── 优秀案例1-Quickinput/         # 本地只读，Git 忽略
│   └── 优秀案例2-okww/               # 本地只读，Git 忽略
├── 项目管理/                          # 历史版本快照
├── PROJECT_OUTLINE.md                 # 项目总览
├── REVIEW_LOG.md                      # 审查和决策记录
├── STAGE_TEST_PLAN.md                 # 测试入口
└── README.md                          # 小白项目入口
```

## 未来目录边界

| 目录 | 未来职责 | 不应放入的内容 |
|---|---|---|
| `src/domain/` | `PythonScriptMetadata`、宏库和触发设置等纯数据模型 | Qt 控件、SendInput 调用 |
| `src/services/` | 脚本扫描、配置保存、OSD 协调 | 页面绘制、案例代码 |
| `src/ui/pages/` | 宏库、触发、功能、设置四页 | 真实输入循环 |
| `src/ui/dialogs/` | 新建、重命名、删除确认、热键捕获 | 业务持久化逻辑 |
| `src/ui/widgets/` | 可复用列表、表单行、状态徽标 | 全局单例状态 |

新增或移动自有文件后，DocUpdater 必须更新本文件。

## Agent 配置边界

`.codex/agents/1-project-lead.md` 是唯一项目总入口。其余配置保持单一职责并向项目负责人报告，不直接改变阶段范围。配置过长且职责混杂时，保留根入口文件，将详细资料拆入同功能子目录。
