# Sycamore

本地优先的能力训练系统。面向跨领域学习者：低摩擦捕获碎片，逐步升格为可理解、可恢复、可迁移的结构化能力节点网络。

**当前版本**：`0.17.0`  
**当前阶段**：P0–P4 全部交付，Phase 1A-0 ~ 4 完成。处于真实使用验证期。

## 产品闭环

```text
捕获 → 澄清 → 编码 → 挑战 → 实践 → 恢复 → 迁移
```

对应日常命令流：

```text
init → capture → inbox → clarify → promote → edit → check
     → sync → doctor
     → practice / review / recover → schedule
     → link → graph / path / status
     → transfer / challenge
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

uv run syca version   # 查看版本
uv run syca init      # 初始化 ~/.sycamore/
```

### 最小使用示例

```bash
# 捕获
uv run syca capture --cheat "ls -la"

# 升格
uv run syca promote --title "我能列出目录详情" --domain shell

# 编码
uv run syca edit <node-id>              # 逐块填写

# 复习
uv run syca recover <node-id>           # recall-first 回忆
uv run syca recover <node-id> --hard    # 评分

# 迁移
uv run syca challenge --domain shell    # 随机挑战

# 图谱
uv run syca link <a> <b> --type prerequisite
uv run syca graph --domain shell
```

## 命令一览

### 输入层

| 命令 | 说明 |
|:--|:--|
| `syca init` | 初始化数据目录与 SQLite |
| `syca capture --note\|--cheat\|--link` | 低摩擦捕获 |
| `syca inbox` | 查看待处理捕获项 |
| `syca clarify [<id>]` | 分析并建议 promote 参数 |
| `syca promote [--latest\|--index\|<id>] --type <type>` | 升格为节点 |

### 学习层

| 命令 | 说明 |
|:--|:--|
| `syca edit <node> [--block <name>] [--suggest]` | 逐块编辑 |
| `syca check <node>` | 检查完成度 |
| `syca query <term> --cheat` | 搜索 Cheatsheet |

### 复习层

| 命令 | 说明 |
|:--|:--|
| `syca recover <node> [--mode] [--pass\|--hard\|--easy\|--fail]` | 回忆训练 |
| `syca review <node> [--dry-run]` | LLM 评审 |
| `syca reviews list\|accept\|ignore\|revised` | 管理评审 |
| `syca practice <node>` | 追加实践记录 |
| `syca level set <node> L0-L3` | 更新等级 |
| `syca schedule [--domain]` | FSRS 到期复习 |

### 迁移层

| 命令 | 说明 |
|:--|:--|
| `syca transfer <node> --level A\|B\|C\|D` | 迁移场景 |
| `syca challenge [--domain]` | 随机挑战 |

### 图谱层

| 命令 | 说明 |
|:--|:--|
| `syca link <src> <tgt> --type prerequisite\|contrast\|composition\|diagnostic` | 建关系 |
| `syca graph --domain <name>` | ASCII 能力图 |
| `syca path --domain <name>` | 学习路径链 |

### 诊断

| 命令 | 说明 |
|:--|:--|
| `syca sync` | 同步索引 |
| `syca doctor` | 一致性检查 |
| `syca status --stale\|--domain\|--weak\|--completion\|--cluster-risk` | 状态视图 |

## 节点类型

| 类型 | 适用领域 | 核心区块 |
|:--|:--|:--|
| `capability` | IT、软件操作、外语 | Steps / Pitfalls / Cheatsheet |
| `concept` | 哲学、历史、经济学 | Core Thesis / Historical Context / Critique |
| `theorem` | 数学、物理、算法 | Formula / Intuition / Boundary Conditions |
| `process` | 化工、机械、生物 | Mechanism / Parameters / Disturbance Response |

## 完成度状态

| 状态 | 条件 |
|:--|:--|
| `draft` | 模板占位未替换 |
| `modeled` | Core Idea + Boundaries + Minimal Task 已填写 |
| `contrasted` | 含 Contrast 区块 |
| `reviewable` | modeled + contrasted + Cheatsheet 非空 |

## LLM 配置（可选）

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

未启用时所有命令仍可正常使用（mock 回退）。

## 数据目录

```text
~/.sycamore/
├── config.toml      # 用户配置
├── sycamore.db      # SQLite 索引、事件、关系、FSRS 状态
├── nodes/           # AbilityNode Markdown（权威正文）
└── reviews/         # ReviewRun 原始 JSON
```

Markdown 正文以文件为准；SQLite 存索引与派生状态。

## 技术栈

| 层面 | 选型 |
|:--|:--|
| 语言 | Python 3.12+ |
| 包管理 | uv |
| CLI | Typer + Rich |
| 存储 | SQLite + Markdown Front Matter |
| 调度 | FSRS-5（Anki 兼容） |
| 测试 | pytest + ruff |

## 文档

| 文档 | 说明 |
|:--|:--|
| [`memory_bank/manuals/usage-guide.md`](memory_bank/manuals/usage-guide.md) | **v0.17.0 完整使用指南**（推荐） |
| [`memory_bank/manuals/real-world-validation-guide.md`](memory_bank/manuals/real-world-validation-guide.md) | 端到端验证指南 |
| [`memory_bank/roadmap.md`](memory_bank/roadmap.md) | 阶段路线与版本策略 |
| [`memory_bank/data-contracts.md`](memory_bank/data-contracts.md) | 数据模型与 CLI 契约 |
| [`memory_bank/architecture.md`](memory_bank/architecture.md) | 架构总览 |
| [`memory_bank/conventions.md`](memory_bank/conventions.md) | 代码与命名规范 |

## 开发与测试

```bash
uv run pytest          # 195 测试，1 跳过
uv run ruff check .    # 零告警
```

测试使用临时 `SYCA_HOME` 隔离，不读写真实 `~/.sycamore/`。LLM 相关测试使用 mock Provider。

## 许可证

MPL 2.0
