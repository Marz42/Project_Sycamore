# 发布与本地运行指南

> COLD 知识。Sycamore 是本地优先 CLI 工具，本文件记录本地安装、运行与数据备份，而非服务器部署。

---

# 当前阶段

**v0.11.1** — 可安装的 Python CLI 包，无线上服务。

| 环境 | 形态 | 数据位置 | 备注 |
|------|------|----------|------|
| 开发 | `uv run syca` 或 `uv pip install -e .` | 临时 `SYCA_HOME` | 推荐验证时隔离数据 |
| 用户本地 | 全局/虚拟环境安装 `syca` | 默认 `~/.sycamore/` | MVP 目标形态 |
| 线上服务 | 暂无 | — | Web/API 属 P3 候选 |

---

# 安装

## 从源码（推荐）

```bash
cd Project_Sycamore
uv sync
uv run syca version    # 应显示 0.11.1
uv run syca init
```

## 可编辑安装

```bash
uv pip install -e .
syca --help
```

---

# 首次使用

1. `syca init` — 创建 `config.toml` 与 SQLite schema  
2. `syca capture --cheat "..."` — 捕获一条碎片  
3. `syca promote --title "我能..." --domain shell` — 升格为节点  
4. 编辑 `~/.sycamore/nodes/<slug>.md`，填写 Mental Model  
5. `syca sync` && `syca doctor`

完整分步验收见 [`real-world-validation-guide.md`](real-world-validation-guide.md)。

---

# 环境变量

| 变量 | 说明 |
|------|------|
| `SYCA_HOME` | 覆盖默认数据目录（`~/.sycamore/`） |
| `DEEPSEEK_API_KEY` | DeepSeek API Key（通过项目根 `.env` 或 `SYCA_HOME/.env` 加载） |

```bash
# PowerShell
$env:SYCA_HOME = "$env:TEMP\sycamore-dev"

# Bash
export SYCA_HOME=/tmp/sycamore-dev
```

---

# LLM 评审

1. `cp .env.example .env`，填入 `DEEPSEEK_API_KEY`  
2. 编辑 `config.toml`：`[llm] enabled = true`  
3. `syca review <node-slug> --dry-run` 预览  
4. `syca review <node-slug>` 正式评审  

`enabled = false` 时 review 使用 mock Provider，无需网络。

---

# 发布前检查清单

- [ ] `VERSION` 与 `pyproject.toml` 版本一致  
- [ ] `memory_bank/changelog.md` 已更新  
- [ ] `uv run pytest` 通过  
- [ ] `uv run ruff check .` 通过  
- [ ] `syca doctor` 在示例数据目录无报错  
- [ ] `README.md` 反映当前命令与版本  

---

# 数据备份

用户核心数据在本地目录，最低限度备份整个目录即可：

```text
~/.sycamore/
├── config.toml
├── sycamore.db
├── nodes/
└── reviews/
```

```bash
# 示例：复制备份（自行选择目标路径）
cp -r ~/.sycamore ~/backups/sycamore-$(date +%Y%m%d)
```

后续 P3 候选：`syca backup create` / `restore`（尚未实现）。

---

# 回滚原则

- 代码回滚依赖 Git。  
- 不自动删除用户 Markdown 节点。  
- 数据库 schema 变更需可追踪（当前 `SCHEMA_VERSION = 1`）。  
- 涉及不可逆迁移前必须先备份。  

---

# 当前限制

- 无 CI/CD 与 PyPI 正式发布流程。  
- 无 `syca backup` 命令（需手动复制目录）。  
- 无数据库迁移工具（schema 变更需谨慎）。  
- Recover drill 为自评，不自动验证解释质量。  
