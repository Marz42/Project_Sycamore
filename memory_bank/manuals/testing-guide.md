# 测试指南

> COLD 知识。编写或运行自动化测试时读取。手工端到端验收见 [`real-world-validation-guide.md`](real-world-validation-guide.md)。

---

# 当前测试策略

**v0.11.1** — 64 passed, 1 skipped。覆盖 P0–P2 核心路径：

- Capture / Inbox / Promote（含 `--latest`、`--index`、UUID 前缀）
- Markdown 解析、sync、doctor、query
- ReviewRun、mock/DeepSeek Provider 工厂
- practice、freshness、level set
- recover、link、graph 文本渲染

---

# 工具链

| 层面 | 工具 | 说明 |
|------|------|------|
| 单元/集成 | pytest | `tests/` 目录 |
| Lint | ruff | `uv run ruff check .` |
| CLI | Typer `CliRunner` | 见 `tests/test_*_cli*`、`test_p2_recovery.py` |
| LLM | mock Provider | 单元测试不调用真实 API；DeepSeek 用 `urllib` mock |
| 隔离 | `tmp_path` + `SYCA_HOME` | 禁止读写真实 `~/.sycamore/` |

---

# 必测场景

## P0

- CaptureItem 保存 note/cheat/link 并出现在 Inbox
- Promote 生成 Markdown 节点与 SQLite 索引
- slug 冲突返回清晰错误
- Cheatsheet 区块提取与 query 匹配
- sync 刷新 hash；doctor 发现不一致

## P1

- practice 追加 Practice Log 与 `practice_logged` 事件
- stale 推导与 `status --stale`
- review dry-run / mock 写入 ReviewRun
- reviews list 的 outdated 检测
- `llmAllowed: false` 门控

## P2

- recover drill 展示与 `--pass`/`--fail` 事件
- link 建边与重复边报错
- graph ASCII 树渲染（含 `[prerequisite]` section）
- status `--domain` 新鲜度表

## Provider

- `tests/test_deepseek_provider.py`：mock `urlopen` 解析 JSON
- `tests/test_graph_render.py`：文本图格式

---

# 运行命令

```bash
uv run pytest
uv run pytest tests/test_promote.py -v
uv run ruff check .
```

---

# 测试约定

- 所有涉及数据目录的测试必须设置 `SYCA_HOME` fixture。  
- 不在测试文件或 CI 中保存真实 `DEEPSEEK_API_KEY`。  
- 样例节点标题使用明确能力断言（中文或英文均可）。  
- 真实 LLM 端到端验证属于手工验收，不纳入 pytest 默认套件。  

---

# 测试文件索引

| 文件 | 覆盖 |
|------|------|
| `test_init.py` / `test_init_cli.py` | init |
| `test_capture.py` / `test_cli.py` | capture、inbox |
| `test_promote.py` | promote |
| `test_markdown_parser.py` | Markdown 区块 |
| `test_sync_query_doctor.py` | sync、query、doctor |
| `test_review.py` / `test_review_p1.py` | review、reviews |
| `test_p1_freshness.py` | practice、level、stale |
| `test_deepseek_provider.py` | DeepSeek 工厂与解析 |
| `test_p2_recovery.py` | recover、link、graph CLI |
| `test_graph_render.py` | graph 文本渲染 |
