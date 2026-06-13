# 真实使用验证指南

> WARM 知识。面向 **v0.11.1** 的端到端手工验收手册。按场景逐步操作，验证 P0–P2 在日常工作流中是否可用。

---

# 文档目的

本指南不是 pytest 测试说明（见 `testing-guide.md`），而是帮助**真实用户**在本地 `~/.sycamore/` 上完成一次完整能力闭环：

```text
捕获 → 升格 → 编辑节点 → 查询/实践 → 评审 → 恢复演练 → 建关系 → 域视图
```

**建议耗时**：首次完整走通约 30–45 分钟（含手写 Mental Model 与一次真实 LLM review）。

---

# 0. 前置条件

## 0.1 环境

| 项 | 要求 |
|----|------|
| Python | 3.12+ |
| 包管理 | [uv](https://github.com/astral-sh/uv) |
| 项目目录 | 已 clone `Project_Sycamore` |
| 网络 | 仅 `syca review`（真实 LLM）需要；其余命令可离线 |

## 0.2 安装与入口

在项目根目录：

```bash
cd /path/to/Project_Sycamore
uv sync
uv run syca version
```

期望输出：`syca 0.11.1`（或更高兼容版本）。

全局命令（可选）：

```bash
uv pip install -e .
syca version
```

## 0.3 数据目录

默认数据目录：`~/.sycamore/`（Windows：`%USERPROFILE%\.sycamore\`）。

```bash
uv run syca init
```

首次运行应看到 `Created config.toml`、`Initialized SQLite schema`。已初始化则显示 `Already initialized`。

目录结构：

```text
~/.sycamore/
├── config.toml      # 用户配置
├── sycamore.db      # SQLite 索引与事件
├── nodes/           # AbilityNode Markdown（权威正文）
└── reviews/         # ReviewRun 原始 JSON 归档
```

指定独立目录（推荐首次验证时使用，避免污染已有数据）：

```bash
# PowerShell
$env:SYCA_HOME = "$env:TEMP\sycamore-validation"
uv run syca init

# Bash
export SYCA_HOME=/tmp/sycamore-validation
uv run syca init
```

后续同一会话中所有 `syca` 命令都会使用该目录。

## 0.4 LLM 配置（可选，验证 P1 review 时需要）

1. 复制环境变量模板：

```bash
cp .env.example .env
```

2. 编辑 `.env`，填入 `DEEPSEEK_API_KEY`。

3. 编辑 `~/.sycamore/config.toml`（或 `SYCA_HOME` 下的 `config.toml`）：

```toml
[llm]
enabled = true
provider = "deepseek"
base_url = "https://api.deepseek.com"
model = "deepseek-v4-pro"
api_key_env = "DEEPSEEK_API_KEY"
```

4. 在项目根目录执行 review 时，CLI 会自动加载 `.env`（不覆盖已有环境变量）。

**不启用 LLM 时**：`syca review` 仍可用，但走 mock Provider，适合验证流程而非评审质量。

## 0.5 新鲜度阈值

`config.toml` 默认：

```toml
[freshness]
stale_after_days = 30
```

验证 stale 行为时，可临时改为 `1`，走完流程后改回 `30`。

---

# 1. 场景概览：Shell 领域三角能力

本指南用三个相互关联的 shell 能力构成最小可验证图谱：

| 节点 | 能力断言 | 关系 |
|------|----------|------|
| A | 我能切换工作目录 | 基础 |
| B | 我能查看当前路径 | A → B（prerequisite） |
| C | 我能列出目录详情 | B → C（prerequisite） |

**领域标签**：统一使用 `shell`。

---

# 2. 阶段一：P0 捕获与升格

## 2.1 捕获碎片

**推荐节奏**：每条捕获后立即升格（见 2.3 方式 A）。若要先体验 Inbox 堆积，可一次性捕获多条：

```bash
uv run syca capture --cheat "cd /path/to/project"
uv run syca capture --cheat "pwd"
uv run syca capture --cheat "ls -la" --context "需要看权限和隐藏文件时"
```

可选补充一条 note：

```bash
uv run syca capture --note "cd 只改进程 cwd，不改脚本所在目录"
```

**验收**：每条命令应返回成功，无报错。

## 2.2 查看 Inbox

```bash
uv run syca inbox
```

**期望**：

- 表格含列 `#`、`ID`（8 位前缀）、`Kind`、`Preview`、`Created`
- 最新条目 `#` 为 1（或按时间排序的首行）
- 三条 `cheat` 均在列表中

## 2.3 升格为正式节点

**方式 A：捕获后立即升格**（推荐，符合日常习惯）：

```bash
uv run syca capture --cheat "cd /path/to/project"
uv run syca promote --title "我能切换工作目录" --domain shell

uv run syca capture --cheat "pwd"
uv run syca promote --title "我能查看当前路径" --domain shell

uv run syca capture --cheat "ls -la" --context "需要看权限和隐藏文件时"
uv run syca promote --title "我能列出目录详情" --domain shell
```

> `--context` 是 `capture` 的参数，不是 `promote` 的。

**方式 B：批量捕获后按序号升格**（配合 2.1 批量捕获）：

```bash
uv run syca inbox
# 假设从上到下 #1=ls, #2=pwd, #3=cd（最新在最上）
uv run syca promote --index 3 --title "我能切换工作目录" --domain shell
uv run syca promote --index 2 --title "我能查看当前路径" --domain shell
uv run syca promote --index 1 --title "我能列出目录详情" --domain shell
```

**方式 C：无参 / `--latest` 升格最新一条**：

```bash
uv run syca promote --title "我能列出目录详情" --domain shell
# 等价于
uv run syca promote --latest --title "我能列出目录详情" --domain shell
```

**方式 D：按 ID 前缀**：

```bash
uv run syca promote a1b2c3d4 --title "我能切换工作目录" --domain shell
```

**验收**：

- 输出 `Promoted ... -> <node-uuid>`
- 显示 `Node file: nodes/<slug>.md`
- `syca inbox` 中对应条目消失（状态变为 promoted）

记录三个节点的 **slug**（如 `node-xxxxxxxx`），后续命令可用 slug、完整 UUID 或唯一前缀指代。

---

# 3. 阶段二：编辑 Markdown 节点

升格后模板含占位内容，**必须手写**才能真正进入 P1/P2 验证。

用任意编辑器打开 `~/.sycamore/nodes/<slug>.md`（路径以 promote 输出为准）。

## 3.1 必填：Mental Model 的 Core Idea

将 `### Core Idea` 下占位句：

```markdown
用自己的话解释这个能力解决什么问题，以及背后的机制。
```

替换为真实理解，例如节点「我能切换工作目录」：

```markdown
### Core Idea

`cd` 改变当前 shell 进程的工作目录（cwd）。后续相对路径、部分工具的默认搜索路径都基于 cwd。`cd` 不移动文件，只改变「当前位置」这一进程级状态。

### Boundaries

- 适合：交互式 shell 中切换到项目目录。
- 不适合：在脚本中假设 cwd（应使用绝对路径或明确 `cd`）。
- 易踩坑：`cd -` 回到上次目录；子 shell 中的 `cd` 不影响父 shell。
```

**Cheatsheet** 升格时若来自 `--cheat` 捕获，通常已有命令，可微调。

**Capability** 标题应尽量是能力断言（promote 的 `--title` 已写入 H1，可再润色 `## Capability` 段）。

## 3.2 同步索引

编辑保存后：

```bash
uv run syca sync
uv run syca doctor
```

**验收**：

- `sync` 报告 `Synced N node(s)`
- `doctor` 输出 `No consistency issues found`

若 `doctor` 报 `content_hash_mismatch`，先 `sync` 再复查。

---

# 4. 阶段三：P0 查询

```bash
uv run syca query "ls" --cheat
uv run syca query "pwd" --cheat
```

**期望**：

- 命中对应节点标题与 slug
- 打印 `## Cheatsheet` 区块内容
- 查询会记录 `cheatsheet_queried` 事件（计入新鲜度）

无匹配时：

```text
No cheatsheet matches for '...'
```

---

# 5. 阶段四：P1 实践与等级

## 5.1 记录一次实践

```bash
uv run syca practice <cd-node-slug> \
  --scenario "打开新项目" \
  --action "cd ~/projects/demo && pwd" \
  --result "确认 cwd 正确" \
  --pitfall "路径有空格时需引号"
```

至少提供 `--note`、`--scenario`、`--action`、`--result`、`--pitfall` 之一。

**验收**：

- 节点 Markdown `## Practice Log` 顶部出现新时间戳条目
- `syca sync` 后 `doctor` 仍通过

## 5.2 调整声明等级

```bash
uv run syca level set <cd-node-slug> L1
```

**期望**：输出 `L0 -> L1`（或当前等级到新等级）。

等级含义：

| 等级 | 含义 |
|------|------|
| L0 | 接触过，不能独立使用 |
| L1 | 看 Cheatsheet 能完成简单任务 |
| L2 | 能解释原理并处理常见变化 |
| L3 | 能迁移场景、排查复杂问题或教别人 |

## 5.3 查看 stale 节点

```bash
uv run syca status --stale
```

**期望**：

- 长期无活动的节点出现在表中
- 刚 `practice` / `query` 的节点不应出现在 stale 列表（阈值内）

---

# 6. 阶段五：P1 LLM 评审

## 6.1 预览（不调用 API）

```bash
uv run syca review <cd-node-slug> --dry-run
```

**验收**：

- 显示 `Mental Model preview`（非占位文本）
- `Provider: deepseek (dry-run)` 或 `mock (dry-run)`（取决于 `enabled`）
- 若仍为占位，报错：`Mental Model is still placeholder text`

## 6.2 正式评审

```bash
uv run syca review <cd-node-slug>
```

**期望**（`enabled = true` 且 API Key 有效）：

- 约 10–30 秒返回
- 输出 `Review completed <review-uuid>`
- `Node status: challenged`
- 原始 JSON 路径：`~/.sycamore/reviews/<review-uuid>.json`

## 6.3 管理评审结论

```bash
uv run syca reviews list <cd-node-slug>
uv run syca reviews accept <review-uuid>
# 或
uv run syca reviews revised <review-uuid>
uv run syca reviews ignore <review-uuid>
```

| 命令 | 节点 reviewStatus |
|------|-------------------|
| `accept` | `accepted_by_user` |
| `revised` | `needs_revision` |
| `ignore` | 保持 `challenged` |

修改 Mental Model 后再次 `reviews list`，旧记录的 `Outdated` 应为 `yes`。

---

# 7. 阶段六：P2 恢复演练

## 7.1 查看 Recovery Drill

```bash
uv run syca recover <ls-node-slug>
```

**期望**：

- 显示节点标题、等级、新鲜度（Fresh / Stale）
- 打印完整 Mental Model
- 有 Cheatsheet 时一并展示
- 底部提示：`syca recover <node-id> --pass` 或 `--fail`

## 7.2 自评并记录

在终端外用自己的话解释 Mental Model，并按 Cheatsheet 完成一个小任务后：

```bash
uv run syca recover <ls-node-slug> --pass
# 或遇到困难时
uv run syca recover <ls-node-slug> --fail --note "记不清 -la 各列含义"
```

**验收**：

- 输出 `Recovery passed` 或 `Recovery failed`
- 该节点新鲜度刷新（`recovery_passed` 计入活动事件）

---

# 8. 阶段七：P2 关系与域视图

## 8.1 建立 prerequisite 链

使用 slug 或 UUID 前缀均可：

```bash
uv run syca link <cd-node-slug> <pwd-node-slug> --type prerequisite \
  --rationale "先知道 cd 才能理解 pwd 的语义"

uv run syca link <pwd-node-slug> <ls-node-slug> --type prerequisite \
  --rationale "先确认当前目录再列出内容"
```

可选横向关系：

```bash
uv run syca link <cd-node-slug> <ls-node-slug> --type related \
  --rationale "都是日常 shell 导航"
```

重复建同类型边会报错：`Link already exists`。

## 8.2 域内文本图

```bash
uv run syca graph --domain shell
```

**期望输出结构**：

```text
Domain: shell (3 nodes, 3 links)

[prerequisite]
我能切换工作目录 (node-...)
└── 我能查看当前路径 (node-...)
    └── 我能列出目录详情 (node-...)

[related]
  我能切换工作目录 ──related──> 我能列出目录详情
      ↳ 都是日常 shell 导航
```

若无边：

```text
No links yet. Unlinked nodes:
  • ...
```

**常见失败**：节点 `domain` 为空 → `No nodes found in domain 'shell'`。解决：编辑 Front Matter 加 `domain: shell` 后 `syca sync`，或升格时使用 `--domain shell`。

## 8.3 域内新鲜度

```bash
uv run syca status --domain shell
```

**期望**：表格含 `Title`、`Slug`、`Level`、`Freshness`（fresh / stale）、`Days`。

---

# 9. 已有数据迁移（针对老用户）

若你在 v0.11 之前已有节点（如仅有 `ls`、`ssh` 两条），按下列步骤补齐 P2 所需字段：

## 9.1 补 domain

编辑 `~/.sycamore/nodes/<slug>.md` Front Matter：

```yaml
---
domain: shell
---
```

保存后：

```bash
uv run syca sync
```

## 9.2 补 Mental Model

确保 `### Core Idea` 不是占位句，否则 `review` 与有意义的 `recover` 无法验证。

## 9.3 补关系

```bash
uv run syca link <source-slug> <target-slug> --type prerequisite
uv run syca graph --domain shell
```

---

# 10. 完整验收 Checklist

按顺序勾选，全部通过即视为 **P0–P2 真实使用验证完成**。

## P0 最小闭环

- [ ] `syca init` 成功
- [ ] `capture --cheat` / `--note` / `--link` 至少各测一种
- [ ] `inbox` 正确列出捕获项
- [ ] `promote`（无参 / `--index` / 前缀）至少测一种
- [ ] 升格时指定 `--domain`
- [ ] `query <term> --cheat` 能命中 Cheatsheet
- [ ] 手改 Markdown 后 `sync` + `doctor` 通过

## P1 能力校准

- [ ] `practice` 追加 Practice Log
- [ ] `level set` 更新 claimedLevel
- [ ] `status --stale` 能列出长期未活动节点
- [ ] `review --dry-run` 通过（非占位 Mental Model）
- [ ] `review` 生成 ReviewRun（mock 或 DeepSeek）
- [ ] `reviews list` / `accept` 或 `revised` 至少测一种

## P2 恢复与关系

- [ ] `recover` 展示 drill
- [ ] `recover --pass` 或 `--fail` 记录事件
- [ ] `link` 建立 prerequisite 链
- [ ] `graph --domain` 显示 ASCII 树
- [ ] `status --domain` 显示 fresh/stale

## 数据一致性

- [ ] 全流程结束后 `syca doctor` 无报错
- [ ] `~/.sycamore/nodes/` 中文件可用普通编辑器打开
- [ ] `reviews/*.json` 与 `reviews list` 条目一致

---

# 11. 推荐日常节奏

验证通过后，可按此节奏日常使用（不必每次跑全量）：

| 时机 | 命令 |
|------|------|
| 编码/排障中 | `syca capture --cheat "..."` |
| 收工前 2 分钟 | `syca inbox` → `syca promote --domain <域>` |
| 周末整理 | 编辑 Markdown → `syca sync` → `syca link` |
| 久未碰某能力 | `syca status --stale` → `syca recover <slug>` → `--pass` |
| 写完 Mental Model | `syca review <slug>` → `syca reviews accept` |
| 每周一览 | `syca graph --domain shell` + `syca status --domain shell` |

---

# 12. 常见问题

| 现象 | 原因 | 处理 |
|------|------|------|
| `Mental Model is still placeholder` | Core Idea 未填写 | 编辑 Markdown 后重试 |
| `No nodes found in domain 'shell'` | 节点无 `domain` 或拼写不一致 | Front Matter 加 `domain` 并 `sync` |
| `content_hash_mismatch` | 手改文件后未 sync | `syca sync` |
| `Missing API key DEEPSEEK_API_KEY` | `.env` 未配置 | 复制 `.env.example` 并填 Key |
| review 很快但内容是 mock | `config.toml` 中 `enabled = false` | 设 `enabled = true` |
| `Link already exists` | 重复同 source/target/type | 预期行为；换类型或删库边（暂无 CLI 删边） |
| `Node identifier matches multiple` | UUID 前缀歧义 | 用更长前缀或 slug |
| graph 中 `[prerequisite]` 不显示 | Rich 标记问题（v0.11.1 已修） | 升级到 0.11.1+ |
| promote 后标题不理想 | 默认从捕获内容生成 | 升格时加 `--title` 或事后改 Markdown |

---

# 13. 命令速查

```bash
# 基础
syca init | version | doctor | sync

# 捕获与升格
syca capture --note|--cheat|--link "..." [--context "..."]
syca inbox
syca promote [--latest|--index N|<id>] [--title "..."] [--domain "..."] [--claimed-level L0]

# 查询
syca query "<term>" --cheat

# P1 校准
syca practice <node> [--note|--scenario|--action|--result|--pitfall "..."]
syca level set <node> L0|L1|L2|L3
syca status --stale
syca review <node> [--dry-run]
syca reviews list|accept|ignore|revised <id>

# P2 恢复与关系
syca recover <node> [--pass|--fail] [--note "..."]
syca link <source> <target> [--type prerequisite|related|...] [--rationale "..."]
syca graph --domain <name>
syca status --domain <name>
```

**节点标识符**：完整 UUID、唯一 UUID 前缀、或 slug（如 `node-617eb5dd`）。

---

# 14. 相关文档

| 文档 | 用途 |
|------|------|
| `memory_bank/data-contracts.md` | 字段与 CLI 契约权威定义 |
| `memory_bank/roadmap.md` | 阶段目标与 P3 启动条件 |
| `memory_bank/manuals/testing-guide.md` | 自动化测试策略 |
| `memory_bank/manuals/deploy.md` | 安装与数据目录说明 |
| `.env.example` | DeepSeek 环境变量模板 |

---

# 15. 验证完成后的下一步

当第 10 节 Checklist 全部勾选：

1. **巩固习惯**：用真实工作碎片驱动 capture，而非为测试而测试。
2. **观察瓶颈**：若 `query --cheat` 不够快、Inbox 堆积、图谱难维护，再考虑 P3（备份、监听 sync、语义检索等）。
3. **反馈驱动**：记录 promote 摩擦、review 质量、recover 是否有帮助，作为下一版优先级输入。

P3 启动条件见 `roadmap.md`——核心标准是 P0/P1 已成为**每周使用**的工具，而非一次性验收。
