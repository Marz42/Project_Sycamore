# 已知问题与调试心得

> COLD 知识。仅在排查问题、遇到行为冲突或需要理解历史坑位时读取。

---

## 问题记录

### memory bank 目录命名不一致

**症状**: 工作区规则中写的是 `memory-bank/`，实际仓库目录是 `memory_bank/`。  
**根因**: 项目初始化时目录命名与规则文档未完全同步。  
**解决方案**: 当前以实际存在的 `memory_bank/` 为准，已同步修改 `.cursor/rules/memory-bank-protocol.mdc` 和 `AGENT_RULES.md`。  
**发现日期**: 2026-06-11  
**关联 ADR**: 无

---

### LLM 评审状态容易误导为事实认证

**症状**: 如果使用 `verified` 或“已验证”作为节点状态，用户可能误以为 LLM 能担保知识正确。  
**根因**: LLM 评审只能提供批判性反馈，不能替代来源核查、实践验证和用户判断。  
**解决方案**: 状态命名改为 `challenged`、`needs_revision`、`accepted_by_user`。文档中禁止使用 `verified`。  
**发现日期**: 2026-06-11  
**关联 ADR**: ADR-003

---

### 产品容易退化为轻量 Obsidian

**症状**: 如果录入流程允许随意保存资料和大段教程，Sycamore 会变成普通知识库。  
**根因**: “个人外脑”概念容易鼓励囤积，而不是促使用户进行能力编码。  
**解决方案**: 节点以能力断言为中心，强制包含 Mental Model、Cheatsheet 和 Practice Log。  
**发现日期**: 2026-06-11  
**关联 ADR**: ADR-001

---

### 双存储架构会产生一致性风险

**症状**: SQLite 中的节点记录可能指向不存在的 Markdown 文件，或 Markdown Front Matter 与数据库状态不一致。  
**根因**: Markdown 和 SQLite 分别承担正文与索引职责，天然存在同步边界。  
**解决方案**: 以 Markdown 正文为准，提供 `syca doctor` 和 `syca index rebuild`。写入流程必须保证失败回滚。  
**发现日期**: 2026-06-11  
**关联 ADR**: ADR-004

---

### CLI-first 可能带来录入摩擦

**症状**: 如果创建节点需要填写太多字段，用户可能绕过系统或回到普通笔记。  
**根因**: 反囤积原则与低摩擦录入之间存在张力。  
**解决方案**: MVP 中只强制最小字段：能力断言、Mental Model 占位、Cheatsheet 占位、Practice Log 占位。其余字段可后补。  
**发现日期**: 2026-06-11  
**关联 ADR**: ADR-002

---

### promote 依赖完整 UUID，inbox 升格摩擦偏高

**症状**: `syca promote <capture-id>` 要求粘贴完整 UUID；`syca inbox` 展示的 ID 较长，端到端验收中升格步骤明显慢于 capture / query。  
**根因**: P0 优先保证标识唯一性与实现简单，未提供短 ID 或序号升格。  
**解决方案**: P0.7 计划增加 `--latest`、`--index <n>`、UUID 前缀匹配及可选交互式选择；详见 `data-contracts.md` promote 增强表。  
**发现日期**: 2026-06-11  
**关联 ADR**: ADR-007
