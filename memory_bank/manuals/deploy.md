# 发布与本地运行指南

> COLD 知识。Sycamore 是本地优先 CLI 工具，本文件记录本地安装、发布和回滚思路，而不是传统服务器部署流程。

---

# 当前阶段

项目尚未初始化可安装包。当前没有线上环境、测试环境或生产服务器。

| 环境 | 形态 | 数据位置 | 备注 |
|------|------|----------|------|
| 开发 | 本地源码运行 | 临时 `SYCA_HOME` 或开发目录 | 用于实现和测试。 |
| 用户本地 | 本地 CLI 安装 | 默认 `~/.sycamore/` | MVP 目标形态。 |
| 线上服务 | 暂无 | 暂无 | Web/API 后置。 |

---

# 本地运行目标

代码骨架完成后，推荐支持：

```bash
syca --help
syca capture --cheat "awk '{print $1}' access.log | sort | uniq -c"
syca inbox
syca promote <capture-id>
syca query "awk" --cheat
```

开发时应允许指定独立数据目录：

```bash
SYCA_HOME=/tmp/sycamore-dev syca inbox
```

---

# 发布流程目标

正式形成 Python 包后，发布前应检查：

- `VERSION` 已更新且符合 SemVer。
- `memory_bank/changelog.md` 已追加版本记录。
- 核心测试通过。
- `syca doctor` 在示例数据目录中通过。
- README 或用户文档包含安装和首次使用说明。

推荐发布步骤待 `pyproject.toml` 创建后补充。

---

# 数据备份

用户核心数据在本地目录中，最低限度应能通过复制整个数据目录备份：

```text
~/.sycamore/
├── sycamore.db
├── nodes/
├── assets/
└── config.toml
```

后续可提供：

```bash
syca backup create
syca backup restore
```

这些命令不属于 P0。

---

# 回滚原则

在正式发布前，回滚主要依赖 Git。

未来发布后，必须注意：

- 不自动删除用户 Markdown 节点。
- 数据库 schema 迁移需要可追踪。
- 涉及不可逆迁移时必须先备份。
- 回滚版本不能破坏已有 Markdown 可读性。

---

# 当前限制

- 暂无服务器部署。
- 暂无 CI/CD。
- 暂无打包发布配置。
- 暂无数据库迁移工具。

这些都应在 CLI MVP 可运行后再补充。
