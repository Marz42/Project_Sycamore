# INIT_PROMPT.md — 会话启动模板

> **使用方式**：根据你的场景复制对应的模板，将 `{{PLACEHOLDER}}` 替换为实际内容后，粘贴到 IDE 对话框中。
>
> **前置条件**：确保已按照 README.md 完成步骤 1（获取基座、断开上游 git remote）。

---

## 模式 F：Project Setup & Bootstrap（一次性机械设置）

> **适用场景**：刚 clone 了 paradigma，还没有做任何初始化设置。让 Agent 帮你完成所有机械操作。

```
你好，我刚从这个项目模板创建了我的新项目。

【我的项目名】：{{项目名，例如 TodoTracker}}

请先阅读 README.md 的"如何使用"部分，理解完整的设置流程。然后帮我按以下步骤操作：

1. 激活 runtime 模板 — 将 memory_bank/ 下的所有 .template.md 复制为 .md：
   - progress.template.md → progress.md
   - decisions.template.md → decisions.md
   - known-issues.template.md → known-issues.md
   - glossary.template.md → glossary.md
   - changelog.template.md → changelog.md

2. **移除 .gitignore 中的 runtime 排除规则**（重要！否则远端开发记忆不同步）：
   - 打开 .gitignore，找到并删除以下 5 行：
     ```
     memory_bank/progress.md
     memory_bank/decisions.md
     memory_bank/known-issues.md
     memory_bank/glossary.md
     memory_bank/changelog.md
     ```
   - 这样你的 progress.md、decisions.md、changelog.md 等就能正常 git 跟踪，换机器不会丢失会话历史和版本记录

3. 修改项目标识：
   - 将 README.md 的标题从 "Project Paradigma" 改为 "{{项目名}}"
   - 将 README.md 的副标题从 "Vibe Coding 时代的项目开发基座" 改为适合我项目的简介
   - 将 .gitignore 中的 paradigma 注释改为通用内容

4. **处理 git remote**：
   - 先执行 `git remote -v` 检查当前 remote
   - 如果 remote 仍指向 Marz42/paradigma，执行 `git remote remove origin`
   - 然后告诉我你的 GitHub 仓库 URL，我帮你关联 `git remote add origin <你的仓库URL>`
   - 如果 remote 已经是你自己的仓库，跳过

5. 将所有更改做首次 commit：
   - 提交信息：chore: init from paradigma template
   - 如果 remote 已配置且与你的仓库关联，同时 push

6. 完成以上操作后，告诉我一切就绪，我们可以进入模式 A 填充项目文档，或者告诉我你想直接开始写代码。
```

---

## 模式 A：全新项目初始化（Agent 填充所有文档）

```
你好，我们将开始一个新项目。

【项目目标】
{{用1-2句话描述项目要解决什么问题，面向什么用户}}

【技术栈偏好】
{{例如：Vue3 + FastAPI + PostgreSQL，或其他}}

【核心卖点 / 差异化特性】
{{例如：支持自然语言输入记账}}

请按以下步骤操作：

1. 读取 memory-bank 目录下的所有文件模板，理解这套工作规范。
2. 作为架构师，帮我填充 project-brief.md（核心愿景、受众、功能边界）。
3. 草拟 architecture.md（整体技术栈、顶层目录结构、前后端交互宏观流程）。
4. 设计第一版 data-contracts.md（核心数据库表结构 ER 图、核心 API 的请求/响应格式）。
5. 对于暂时无法确定的字段（如仓库地址、文档站点等），标记为 `TODO` 而不是编造。
6. 完成这些文档的初始化后，告诉我，我们再开始写第一行代码。
```

---

## 模式 B：已有项目续接（Agent 读取已有文档并审查）

```
你好，这是一个已有项目。请按以下步骤操作：

1. 读取 memory-bank 目录下的所有文件（按照 AGENT_RULES.md 中定义的温度等级加载）。
2. 审查现有文档的完整性和一致性，告诉我：
   - 哪些文档信息不足或过时
   - architecture.md 与实际代码结构是否一致
   - data-contracts.md 的约束是否仍然有效
3. 阅读 progress.md，了解项目历史和当前状态。
4. 阅读 active-task.md，理解当前正在进行的任务。
5. 给出你的审查意见，然后我们继续推进 {{具体的下一步任务}}。
```

---

## 模式 C：单任务突击（跳过审查，直接执行）

```
你好，请按以下步骤操作：

1. 读取 memory-bank 的 HOT 文件（project-brief, architecture, data-contracts, conventions, active-task, progress）。
2. 理解当前项目状态后，直接开始执行任务：
   {{具体任务描述}}
3. 执行完成后，按照 AGENT_RULES.md 的 Update Phase 更新相关文档。
```

---

## 模式 D：架构决策讨论（聚焦决策层面）

```
你好，我们需要做一个架构决策。

【背景】
{{简要描述当前遇到的架构问题或需要决策的事项}}

请按以下步骤操作：

1. 读取 memory-bank 的 HOT 文件和 decisions.md，了解现有架构和已有决策。
2. 给出 2-3 个可行方案，并分析各自优缺点。
3. 给出你的推荐方案及理由。
4. 待我确认后，将最终决策追加到 decisions.md。
```

---

## 自定义提示

你可以根据实际需要，组合以上模板或自行编写 INIT_PROMPT。核心原则是：

- **始终让 Agent 先读 memory-bank**，无论是初始化还是续接
- **明确告诉 Agent 你期望的输出**，是填充文档还是写代码
- **约定好会话结束时的交付物**，让 Agent 知道什么时候算"完成"
