# 测试指南

> COLD 知识。仅在编写或运行测试时读取。

---

# 当前测试策略

Sycamore 当前进入 P0 最小可信闭环构建阶段。测试优先覆盖“CaptureItem + Inbox + Promote + Markdown + SQLite + CLI”这条核心链路。

---

# 推荐测试框架

| 层面 | 工具 | 说明 |
|------|------|------|
| 单元测试 | pytest | 覆盖领域模型、Markdown 解析、SQLite 存储。 |
| CLI 测试 | pytest + Typer/Click testing utilities | 根据最终 CLI 框架选择对应测试工具。 |
| LLM 评审 | mock Provider | 不在单元测试中调用真实外部模型。 |
| 临时目录 | pytest `tmp_path` | 隔离 `SYCA_HOME`，避免污染真实用户数据。 |

---

# 必测场景

- AbilityNode 创建时生成稳定 ID、slug 和 Markdown 模板。
- slug 冲突时返回清晰错误，不覆盖已有文件。
- CaptureItem 能保存 note、cheat、link 并出现在 Inbox。
- Promote 能把 CaptureItem 升格为 AbilityNode。
- Markdown Front Matter 可读写。
- `Cheatsheet` 区块可被准确提取。
- SQLite 元数据和 Markdown 文件路径保持一致。
- `syca doctor` 能发现缺失文件、孤儿记录和无效关系。
- P1 LLM review 使用 mock Provider 返回结构化 `ReviewRun`。
- CLI 在 `--json` 模式下遵循统一输出格式。

---

# 测试数据约定

- 测试不得读写真实 `~/.sycamore/`。
- 测试必须设置临时 `SYCA_HOME`。
- 测试样例节点应使用明确的能力断言标题。
- 不在测试文件中保存真实 LLM API Key。

---

# 推荐命令

项目初始化后建议使用：

```bash
pytest
pytest tests/unit
pytest tests/integration
```

如果后续引入覆盖率工具，再补充：

```bash
pytest --cov=sycamore
```

---

# 当前状态

代码骨架尚未创建，因此本指南记录的是目标测试策略。初始化 `pyproject.toml` 后需要同步补充实际命令。
