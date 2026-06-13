# Sycamore

本地优先的能力校准与恢复 CLI。面向跨领域学习者：在真实工作中低摩擦捕获碎片，再逐步升格为可查询、可评审、可恢复的结构化能力节点。

**当前版本**：`0.11.1`  
**当前阶段**：P0 / P1 已交付，P2 核心命令已就绪，处于真实使用验证期。

## 产品闭环

```text
捕获 → 澄清 → 编码 → 挑战 → 实践 → 恢复
```

对应日常命令流：

```text
init → capture → inbox → promote → query --cheat → sync → doctor
     → practice / review / recover → link → graph / status
```

## 快速开始

### 环境要求

- Python 3.12+
- [uv](https://github.com/astral-sh/uv)（推荐）

### 安装与初始化

```bash
git clone <repo-url> Project_Sycamore
cd Project_Sycamore
uv sync

# 查看版本
uv run syca version

# 初始化本地数据目录（默认 ~/.sycamore/）
uv run syca init
```

可选：安装为可编辑包，直接使用 `syca` 命令：

```bash
uv pip install -e .
syca --help
```

### 最小使用示例

```bash
# 1. 捕获一条命令片段
uv run syca capture --cheat "ls -la"

# 2. 升格为正式能力节点
uv run syca promote --title "我能列出目录详情" --domain shell

# 3. 编辑 ~/.sycamore/nodes/<slug>.md，填写 Mental Model 的 ### Core Idea

# 4. 同步并检查一致性
uv run syca sync
uv run syca doctor

# 5. 查询 Cheatsheet
uv run syca query "ls" --cheat
```

### 独立数据目录（开发或验证用）

```bash
# PowerShell
$env:SYCA_HOME = "$env:TEMP\sycamore-dev"
uv run syca init

# Bash
export SYCA_HOME=/tmp/sycamore-dev
uv run syca init
```

## 命令一览

| 阶段 | 命令 | 说明 |
|------|------|------|
| **P0** | `syca init` | 初始化配置与 SQLite |
| | `syca capture --note\|--cheat\|--link` | 低摩擦捕获到 Inbox |
| | `syca inbox` | 查看待处理捕获项 |
| | `syca promote [--index\|--latest\|<id>]` | 升格为 Markdown 节点 |
| | `syca query <term> --cheat` | 搜索 Cheatsheet |
| | `syca sync` / `syca doctor` | 同步索引与一致性检查 |
| **P1** | `syca practice <node>` | 追加 Practice Log |
| | `syca level set <node> L1` | 更新声明等级 |
| | `syca status --stale` | 列出久未活动节点 |
| | `syca review <node> [--dry-run]` | LLM 批判性评审 |
| | `syca reviews list\|accept\|ignore\|revised` | 管理评审记录 |
| **P2** | `syca recover <node> [--pass\|--fail]` | 恢复演练 |
| | `syca link <src> <tgt> --type prerequisite` | 建立能力关系 |
| | `syca graph --domain shell` | 域内 ASCII 能力图 |
| | `syca status --domain shell` | 域内新鲜度视图 |

节点标识符支持：完整 UUID、唯一 UUID 前缀、或 slug。

## LLM 评审配置（可选）

默认使用 **DeepSeek**（`deepseek-v4-pro`）。未启用时 `review` 走 mock，不影响其他命令。

```bash
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY
```

编辑 `~/.sycamore/config.toml`：

```toml
[llm]
enabled = true
provider = "deepseek"
base_url = "https://api.deepseek.com"
model = "deepseek-v4-pro"
api_key_env = "DEEPSEEK_API_KEY"
```

## 数据目录

```text
~/.sycamore/
├── config.toml      # 用户配置
├── sycamore.db      # SQLite 索引、事件、关系
├── nodes/           # AbilityNode Markdown（权威正文）
└── reviews/         # ReviewRun 原始 JSON
```

Markdown 正文（Mental Model、Cheatsheet、Practice Log）以文件为准；SQLite 存索引与派生状态。

## 技术栈

| 层面 | 选型 |
|------|------|
| 语言 | Python 3.12+ |
| 包管理 | uv |
| CLI | Typer + Rich |
| 存储 | SQLite + Markdown Front Matter |
| 测试 | pytest + ruff |

刻意不引入：Web 服务、ORM、向量库、后台 daemon、插件系统。

## 文档

| 文档 | 说明 |
|------|------|
| [`memory_bank/manuals/real-world-validation-guide.md`](memory_bank/manuals/real-world-validation-guide.md) | **端到端真实使用验证指南**（推荐首次阅读） |
| [`memory_bank/roadmap.md`](memory_bank/roadmap.md) | 阶段路线与版本策略 |
| [`memory_bank/data-contracts.md`](memory_bank/data-contracts.md) | 数据模型与 CLI 契约 |
| [`memory_bank/manuals/deploy.md`](memory_bank/manuals/deploy.md) | 安装与数据备份 |
| [`memory_bank/manuals/testing-guide.md`](memory_bank/manuals/testing-guide.md) | 自动化测试说明 |
| [`memory_bank/changelog.md`](memory_bank/changelog.md) | 版本变更记录 |

项目上下文由 `memory_bank/` 维护，Agent 协同时按温度等级加载（见 `.cursor/rules/memory-bank-protocol.mdc`）。

## 开发与测试

```bash
uv run pytest
uv run ruff check .
```

测试使用临时 `SYCA_HOME` 隔离，不读写真实 `~/.sycamore/`。LLM 相关测试使用 mock Provider。

## 许可证

本仓库沿用 MPL 2.0。公开发布前如需调整许可证请另行评估。
