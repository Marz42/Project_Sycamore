# 项目约定

> HOT 知识。本文件定义 Sycamore 的代码、文档、数据和协作规范。写代码或修改数据契约前必须遵守。

---

# 核心工程原则

| 原则 | 含义 | 反例 |
|------|------|------|
| 单一职责 | 每个模块只承担一个明确职责。 | CLI 命令中直接拼 SQL、解析 Markdown、调用 LLM。 |
| Local First | 核心数据默认保存在本地，外部服务只作为可选增强。 | 查询 Cheatsheet 时必须联网。 |
| Plain Text First | 用户知识正文必须可被普通编辑器读取。 | 把 Mental Model 只存在数据库 JSON 字段中。 |
| 先跑通再优化 | MVP 先验证学习循环，不提前做 Web、插件、RAG。 | 第一版就搭完整 C/S 架构和插件系统。 |
| 用户主动编码 | 系统促使用户写自己的理解，不代替用户生成最终笔记。 | LLM 自动生成完整 Mental Model 并标记完成。 |

---

# 产品语义约定

## 节点必须尽量是能力断言

推荐：

- `我能用 Shell 管道快速处理日志`
- `我能解释 Docker volume 与 bind mount 的区别并做部署选择`

不推荐：

- `Shell`
- `Docker`
- `Nginx 笔记`

## 状态命名避免过度承诺

禁止使用 `verified`、`certified`、`truth` 等暗示事实已认证的状态名。

推荐使用：

- `not_reviewed`
- `challenged`
- `needs_revision`
- `accepted_by_user`

LLM 评审只能表示“理解经过挑战”，不能表示“事实被担保正确”。

## Cheatsheet 只保存低频细节

适合：

- 命令。
- 参数。
- 配置片段。
- 最小示例。
- 排错步骤。

不适合：

- 大段教程。
- 未筛选资料。
- 应该写入 Mental Model 的核心机制。

---

# 命名约定

## Python 代码

| 场景 | 规范 | 示例 |
|------|------|------|
| 包/模块文件 | `snake_case` | `node_service.py` |
| 函数/变量 | `snake_case` | `create_node()` |
| 类 | `PascalCase` | `NodeService` |
| 常量 | `UPPER_SNAKE_CASE` | `DEFAULT_SYCA_HOME` |
| 布尔变量 | `is_` / `has_` / `can_` / `should_` | `should_open_editor` |

## CLI 命名

| 场景 | 规范 | 示例 |
|------|------|------|
| 命令 | 短动词，kebab-case | `syca capture` |
| 选项 | kebab-case | `--review-status` |
| JSON 字段 | camelCase | `reviewStatus` |
| SQLite 字段 | snake_case | `review_status` |
| Markdown front matter | camelCase | `lastReviewedAt` |

## 文件命名

| 文件类型 | 规范 | 示例 |
|----------|------|------|
| Python 文件 | `snake_case.py` | `markdown_store.py` |
| Markdown 节点 | `kebab-case.md` | `shell-pipeline-log-processing.md` |
| 文档 | `kebab-case.md` | `testing-guide.md` |

禁止：

- 使用拼音或拼音缩写。
- 使用无意义命名，如 `data`、`info`、`temp`、`obj`，除非在极短局部作用域中含义自明。
- 对业务状态使用模糊名称，如 `done`、`ok`、`valid`。

---

# 目录组织约定

目标代码结构：

```text
sycamore/
├── cli/         # 命令行入口，只负责参数和展示
├── core/        # 用例和业务编排
├── models/      # 领域模型、枚举、类型
├── storage/     # SQLite、Markdown、资产存储
├── review/      # LLM Provider、Prompt、评审解析
└── utils/       # 纯工具函数
```

依赖方向：

- `cli` 可以依赖 `core`。
- `core` 可以依赖 `models`，通过接口调用 `storage` 和 `review`。
- `storage` 可以依赖 `models`，不依赖 `cli`。
- `review` 可以依赖 `models`，不依赖 `cli`。
- `utils` 不依赖项目业务模块。

禁止：

- CLI 直接写 SQL。
- CLI 直接解析 Markdown 区块。
- Storage 层调用 LLM。
- Review 层修改用户 Markdown 原文。

---

# Markdown 节点约定

节点文件必须包含：

- YAML Front Matter。
- `## Capability`
- `## Mental Model`
- `## Cheatsheet`
- `## Practice Log`
- `## Review Notes`
- `## References`

规则：

- 用户正文以 Markdown 为准。
- 数据库只保存索引、状态、路径和关系。
- 自动化工具只能追加明确区块，不应重写用户的 Mental Model。
- 如果需要修改用户正文，必须让用户确认或打开编辑器。

---

# LLM 评审约定

LLM 只做评审，不做最终答案作者。

Prompt 应要求模型输出：

- 事实疑点。
- 边界条件。
- 类比风险。
- 反例。
- 深度追问。
- 实践验证建议。

LLM 不应：

- 直接覆盖用户原文。
- 生成整篇替代笔记。
- 把结果标记为已验证。
- 在没有来源时做强断言。

---

# 错误处理约定

## CLI

默认输出给人阅读的错误信息：

- 说明发生了什么。
- 说明用户下一步可以做什么。
- 避免暴露冗长堆栈，除非开启 `--debug`。

## JSON

使用 `--json` 时遵循：

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

错误码建议：

| code | 含义 |
|------|------|
| 400 | 参数或输入不合法。 |
| 404 | 节点或资源不存在。 |
| 409 | slug、路径或关系冲突。 |
| 422 | Markdown 格式或数据契约校验失败。 |
| 500 | 未预期内部错误。 |

---

# 类型和质量控制

## Python

- 所有公开函数必须有类型标注。
- 领域模型优先使用 dataclass、Pydantic 或明确类型结构。
- 单个函数建议不超过 80 行。
- 单个文件建议不超过 500 行。
- 不使用超过三层嵌套的条件分支。
- 业务规则应放在 core 层，不分散在 CLI 或 storage 层。

## Markdown 解析

- 优先使用成熟 front matter 和 Markdown 解析库。
- 不用脆弱的字符串拼接处理复杂结构。
- 对节点区块缺失要给出可修复提示。

---

# 测试规范

必须优先覆盖：

- 节点创建和 slug 冲突。
- Markdown 模板生成。
- Front Matter 读写。
- Cheatsheet 区块提取。
- SQLite 与 Markdown 一致性检查。
- Capture/Inbox/Promote 的主要路径。
- P1 LLM 评审结果解析，使用 mock Provider。
- CLI 命令的主要成功和失败路径。

测试文件命名：

- `test_*.py`

测试目录：

```text
tests/
├── unit/
└── integration/
```

---

# Git 提交规范

提交信息格式：

```text
<type>(<scope>): <subject>
```

常用 type：

| Type | 含义 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat(cli): add capture command` |
| `fix` | Bug 修复 | `fix(storage): preserve markdown on index rebuild` |
| `refactor` | 重构 | `refactor(core): split review service` |
| `docs` | 文档 | `docs(memory): define capability node contract` |
| `test` | 测试 | `test(cli): cover cheat query` |
| `chore` | 工具和配置 | `chore(project): add pyproject` |

---

# 版本号规范

本项目遵循 SemVer，根目录 `VERSION` 是版本号真实来源。

## 递增规则

| 修改类型 | 版本动作 |
|----------|----------|
| 纯文档、注释、格式修改 | 不升版本号 |
| 向下兼容的 Bug 修复 | 升 PATCH |
| 向下兼容的新功能 | 升 MINOR |
| 不兼容的 API 或数据契约变更 | 提议升 MAJOR，等待用户确认 |

0.y.z 阶段表示项目仍处于初始开发期，公共 API 尚不稳定。即便如此，修改数据契约仍必须先更新 `data-contracts.md` 并告知用户。

当版本号需要递增时，必须同时：

1. 更新根目录 `VERSION`。
2. 更新 `memory_bank/changelog.md`。
3. 在 `memory_bank/progress.md` 记录版本变化。

---

# Agent 协作约定

- 每次对话开始读取 HOT memory bank 文档。
- 修改数据库结构、Markdown 节点格式、CLI 命令契约或跨模块 API 前，必须征求用户同意，除非用户已明确要求全自动执行。
- 不确定业务语义时，优先查 `glossary.md` 和 `decisions.md`。
- 发现项目方向和现有文档冲突时，先更新 memory bank，再写代码。
- 不随意删除用户知识内容或节点正文。
