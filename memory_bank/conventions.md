# 通用编码原则

> 🔥 HOT — 每次对话必读。本文件定义项目代码规范，写任何代码前必须遵循。

## 核心原则


| 原则         | 含义                  | 反例                             |
| ---------- | ------------------- | ------------------------------ |
| **单一职责**   | 每个函数/组件/模块只做一件事     | 一个 300 行的函数同时处理校验、数据库查询和邮件发送   |
| **高内聚低耦合** | 相关逻辑放一起，模块间通过明确接口通信 | 模块 A 直接访问模块 B 的数据库表            |
| **先跑通再优化** | MVP 阶段不做过早抽象和过度优化   | 为"未来可能的需求"写了一套插件系统             |
| **约定优于配置** | 遵循项目现有模式，不要另起炉灶     | 已有 `useRequest` 封装却自己写原生 fetch |


## 代码质量控制

- **函数长度上限**：单个函数/方法不超过 80 行。超过则拆分。
- **文件长度上限**：单个文件不超过 500 行（组件文件和配置文件除外）。
- **复杂度控制**：不用嵌套三元表达式。不用超过三层嵌套的条件判断。
- **DRY 有度**：重复三次以上才抽离公共逻辑。不要为两次重复引入过度抽象。

---

# 命名约定

## 通用规则


| 场景       | 规范                                 | 示例                                     |
| -------- | ---------------------------------- | -------------------------------------- |
| 变量/函数    | camelCase                          | `userName`, `getOrderList()`           |
| 常量       | UPPER_SNAKE_CASE                   | `MAX_RETRY_COUNT`, `API_BASE_URL`      |
| 类/接口/类型  | PascalCase                         | `UserService`, `OrderCreateInput`      |
| 文件名      | kebab-case                         | `user-service.ts`, `order-detail.vue`  |
| 布尔变量     | `is` / `has` / `can` / `should` 前缀 | `isActive`, `hasPermission`, `canEdit` |
| 事件处理函数   | `handle` + 事件名                     | `handleSubmit`, `handleRowClick`       |
| 回调 props | `on` + 事件名                         | `@on-confirm`, `onUpdate:modelValue`   |


## 禁止命名

- 不用拼音。不用汉语拼音缩写。
- 不用无意义变量名：`data`, `info`, `temp`, `obj`, `arr`, `res`, `val`（除非在极短闭包内且含义自明）
- 不用单字母变量（`i`, `j` 作为循环计数器除外，`e` 作为事件对象除外）

---

# 文件组织

## 目录结构约定

每个功能模块按以下层次组织（根据实际技术栈调整）：

```
src/
├── components/          # 通用 UI 组件（跨模块复用）
│   └── [component]/
│       ├── index.vue    # 组件入口
│       ├── types.ts     # 组件专用类型
│       └── utils.ts     # 组件专用工具函数
├── views/               # 页面级组件（对应路由）
├── composables/         # Vue3 Composable / React Hook（状态逻辑复用）
├── services/            # API 请求层（与后端交互）
├── stores/              # 全局状态管理
├── utils/               # 纯函数工具
├── types/               # 全局类型定义
└── constants/           # 全局常量
```

## 文件关系规则

- `views/` 可以引用 `components/`、`composables/`、`services/`、`stores/`
- `components/` 不应引用 `views/`（通用组件不应依赖页面）
- `services/` 不应引用 `views/` 或 `components/`（数据层不应依赖 UI）
- `utils/` 不依赖项目的任何其他模块（纯函数）

---

# 前端规范

> 以下以 Vue 3 + TypeScript 为默认技术栈。如果你的项目使用 React / Svelte / 其他，替换本节内容。

## Vue 3 必须使用组合式 API

```vue
<script setup lang="ts">
// ✅ 必须：使用 <script setup> + Composition API
import { ref, computed, onMounted } from 'vue'

const count = ref(0)
const doubled = computed(() => count.value * 2)

onMounted(() => {
  // 初始化逻辑
})
</script>
```

## 禁止 Options API

```vue
<script>
// ❌ 禁止：Options API（除非维护遗留代码）
export default {
  data() { return { count: 0 } },
  computed: { doubled() { return this.count * 2 } },
  methods: { increment() { this.count++ } }
}
</script>
```

## 组件设计规则

- **Props 解构**：在 `<script setup>` 中使用 `defineProps` 配合 TypeScript 泛型
- **Emits 声明**：使用 `defineEmits` 明确声明所有事件，不用隐式 emit
- **双向绑定**：使用 `defineModel`（Vue 3.4+）或 `v-model` 规范，不用手动 prop + emit
- **组件拆分粒度**：当一个组件的 template 超过 150 行，考虑拆分子组件

## 状态管理规则

- 跨组件共享状态使用 Pinia store
- 页面内部状态放在组件自身的 `ref` / `reactive` 中，不要放进 store
- Store 中不存"计算得出"的数据，用 getter 代替

---

# 后端规范

> 以下以 Python FastAPI 为默认技术栈。如果你的项目使用其他后端框架，替换本节内容。

## FastAPI 路由组织

- 路由文件按资源命名：`users.py`、`orders.py`、`products.py`
- 每个路由文件包含该资源的所有 CRUD 端点
- 业务逻辑抽到 `services/` 层，路由层只做参数校验和响应格式化

## 依赖注入规则

```python
# ✅ 使用 FastAPI Depends 进行依赖注入
from fastapi import Depends

@router.get("/users/me")
async def get_current_user(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return current_user
```

## 错误处理规范

- 所有 API 端点统一返回格式（见 `data-contracts.md`）
- 业务异常抛出自定义异常类，由全局异常处理器捕获并转换为标准响应
- 不在路由中直接 `try-except` 大量业务逻辑，让异常向上冒泡到统一处理器

## 数据库操作规则

- 使用 ORM 的异步模式（如 SQLAlchemy async）
- 数据查询在 services 层封装，不在路由中直接写 SQL/ORM 查询
- 所有写操作包裹在事务中

---

# 类型安全

## TypeScript 规则

- 不用 `any`。特殊场景需要时加注释说明原因。
- 类型定义优先使用 `interface`（可扩展），其次 `type`（联合类型、映射类型等场景）
- Props、API 响应、Store 状态必须有明确类型定义
- 不在代码中硬编码类型断言 `as`，除非有充分理由

## Python 类型标注

- 所有函数参数和返回值必须有类型标注
- 使用 `Pydantic` 模型定义 API 的请求/响应 Schema
- 数据库模型字段使用 ORM 提供的类型系统

---

# Git 提交规范

## 提交信息格式

```
<type>(<scope>): <subject>

[optional body]
```


| Type       | 含义          | 示例                                      |
| ---------- | ----------- | --------------------------------------- |
| `feat`     | 新功能         | `feat(auth): add JWT login endpoint`    |
| `fix`      | Bug 修复      | `fix(order): correct total calculation` |
| `refactor` | 重构（不改变功能）   | `refactor(utils): extract date helpers` |
| `docs`     | 文档          | `docs(readme): update deployment guide` |
| `style`    | 格式（不影响代码运行） | `style: format with prettier`           |
| `test`     | 测试          | `test(order): add edge case coverage`   |
| `chore`    | 构建/工具/依赖    | `chore(deps): bump vite to 5.0`         |


## 分支命名

- `feat/<feature-name>` — 新功能分支
- `fix/<bug-name>` — Bug 修复分支
- `refactor/<scope>` — 重构分支

---

# 版本号规范

> 本项目遵循 [语义化版本控制 2.0.0 (SemVer)](https://semver.org/lang/zh-CN/)。
> 以下为操作摘要，完整规范见官网。

## 版本格式

```
主版本号 . 次版本号 . 修订号
MAJOR   . MINOR  . PATCH
```

- 三个数字均为非负整数，禁止前导零（`1.9.0` → `1.10.0`，不是 `1.09.0`）
- 先行版本号以 `-` 附加（如 `1.0.0-alpha.1`）
- 不强制使用 `v` 前缀（`git tag` 时按需添加）

## 递增规则（唯一需要记住的）


| 场景                 | 递增哪个      | 归零哪些            | 示例                |
| ------------------ | --------- | --------------- | ----------------- |
| 🐛 向下兼容的 bug 修复    | PATCH (Z) | 无               | `1.2.3` → `1.2.4` |
| ✨ 向下兼容的新功能、弃用旧 API | MINOR (Y) | PATCH 归零        | `1.2.3` → `1.3.0` |
| 💥 不兼容的 API 变更     | MAJOR (X) | MINOR、PATCH 均归零 | `1.2.3` → `2.0.0` |


## 额外规则

- **不可变性**：已发布的版本内容绝对不能改。任何修改必须发新版本号。
- **0.y.z 阶段**：主版本号为 0 表示开发初始阶段，API 不稳定。此阶段只递增 MINOR。
- **1.0.0 界定**：`1.0.0` 表示公共 API 已稳定。发布 1.0.0 后，所有版本号变更必须依据公开 API 的兼容性。
- **先行版本号**：`-alpha`（内部测试）、`-beta`（外部测试）、`-rc`（候选发布）。优先级：`1.0.0-alpha < 1.0.0-alpha.1 < 1.0.0-beta < 1.0.0-rc.1 < 1.0.0`。
- **编译信息**：以 `+` 附加（如 `1.0.0+20260101`），不影响版本优先级。

## Agent 行为约定

- 🔴 **Agent 无权自行决定升 MAJOR** — 不兼容的 API 变更必须先征求用户同意（与 `AGENT_RULES.md` 中 Plan Phase 的规则一致）
- 🟡 建议升 MINOR 或 PATCH 时，Agent 应在 Update Phase 告知用户，由用户确认
- 不得在同一个 commit 中同时做功能新增和不兼容变更（这两种变更应对应不同的版本号）
- 如果发现某个既存版本号不符合 SemVer，不要回溯修改已发布版本，报告给用户并在后续版本中纠正

### 主动版本管理（每次对话结束时评估）

Agent 在 Update Phase 必须根据本次修改的性质判断是否需要版本号递增：

| 修改类型 | 版本动作 | 判断依据 |
|----------|----------|----------|
| 纯文档/注释/格式修改 | 不升版本号 | 只改了 .md 或注释，无代码逻辑变更 |
| 🐛 Bug 修复（不改变 API） | 升 PATCH (Z) | 修复了错误行为，但 API 契约不变 |
| ✨ 新功能（向下兼容） | 升 MINOR (Y) | 新增了功能或模块，旧 API 仍可用 |
| 💥 不兼容的 API 变更 | 提议升 MAJOR (X)，等用户确认 | 改了已有接口签名、数据库 schema |

当版本号需要递增时，Agent 必须同时完成：
1. 更新根目录 `VERSION` 文件
2. 追加 `memory_bank/changelog.md`（按 Keep a Changelog 格式）
3. 在 `progress.md` 的本次会话摘要中记录版本号变更

> **为什么用 VERSION 文件而不是 git tag？** VERSION 文件是代码仓库内的唯一真实来源。Agent 可以直接读取它来确定当前版本。git tag 是发布时的操作，与日常开发中的版本评估是两个不同环节。Agent 评估版本 → 用户确认 → 合适的时机用户手动打 tag。

---

# 测试规范

## 测试原则

- 核心业务逻辑必须有单元测试
- API 端点必须有集成测试
- 修改已有代码时，先确保已有测试通过，再写新的测试
- 不要为了覆盖率而写无意义的测试（比如测试框架本身的功能）

## 测试文件放置

- 单元测试与源文件同目录或镜像目录
- 集成测试放在 `tests/` 目录下
- 测试文件命名：`*.test.ts` 或 `test_*.py`

---

# 代码审查清单

Agent 在提交代码前，自行检查以下项目：

- [ ] 函数/组件是否符合单一职责
- [ ] 是否有硬编码的魔法数字或字符串（应提取为常量）
- [ ] 错误处理是否完备（不是空 catch）
- [ ] 命名是否自解释（不需要注释就能理解意图）
- [ ] 是否引入了与当前任务无关的修改
- [ ] 是否违反了 `data-contracts.md` 中定义的 API 契约
- [ ] 如果是新增功能，是否更新了相关文档

---

# 协作模式约定

> 参见 `AGENT_RULES.md` 的四阶段工作流协议。

- Agent 修改数据模型或跨模块 API → **必须先征得用户同意**
- Agent 发现代码中的大泥球 → **先提议重构方案，不等会动手**
- Agent 对某个既有模块的逻辑不确定 → **不要猜测，要求提供更多上下文**
- 用户说"全自动" → Agent 可跳过确认步骤，直接执行
