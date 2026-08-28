# 面向长生命周期 AI Agent 的会话存储：从线性日志到有向树的设计与实现

# Session Storage for Long-Lived AI Agents: From Linear Logs to a Directed Tree

---

## 摘要（Abstract）

随着 LLM 驱动的智能体（Agent）从单轮问答演进为长生命周期的连续交互系统，会话状态管理成为制约其可用性的核心瓶颈。传统线性消息日志在分支实验、上下文压缩、崩溃恢复、可解释审计等场景下暴露出**结构性缺陷**——破坏性删除破坏历史、复制整段历史导致分叉代价高、无结构化载体表达压缩、无操作日志承载崩溃恢复——这些问题的根因是抽象层级的不足：线性结构没有承载"分支、压缩、状态变更"等高级操作的语义原语。

本文介绍 Orion Smart Home 项目中设计与实现的一种**append-only 有向树形会话存储模型**。针对线性日志在六类典型场景下的局限，我们以"在树上追加节点 + 移动指针"为统一原子操作，将分支、压缩、状态变更等高级操作提升为一等公民；通过 6 条不变式在内存状态机层集中校验，使树在任何时刻都合法；通过"先持久化、后应用内存"的写入路径与 SQLite 事务，实现可证明的崩溃一致性；通过双路径 token 估算与公共祖先算法，实现长会话下的稳定压缩与零冗余分支摘要。

本文的核心贡献在于：（1）**问题—方案对照的工程论证**：逐项展示线性日志在六类场景下的具体失效模式，并给出有向树方案在每类问题上的针对性解法；（2）**抽象的提升**：将会话从一维时间线重构为有向树，把"导航、回退、压缩、分叉"统一为同一原子操作；（3）**崩溃一致性的可证性**：6 条不变式 + 共享 seq + 先持久化后应用内存，使崩溃恢复从工程承诺变成可验证的不变式；（4）**关键算法的精化**：双路径 token 估算、切割点算法、跨压缩文件操作累积、公共祖先计算等具体算法在长会话、长分支等场景下表现稳定。

**关键词**：会话存储、有向树、append-only 日志、上下文压缩、分支摘要、AI Agent

---

## 1 引言（Introduction）

### 1.1 问题的提出

LLM 驱动的智能体系统在自然语言理解、工具调用、任务规划等维度取得显著进展，但**会话状态管理**这一基础组件并未得到与模型能力相匹配的关注。在工业级 Agent 系统（智能家居、运维助手、代码助手等）中，"会话"已不再是简单的一问一答记录，而是承担了模型工作记忆、压缩与重放载体、审计与可解释性记录、多任务隔离边界等多重职责。

当前的工业实践大多沿用"消息列表"这一朴素抽象：以 Python `list[dict]`、JSONL 文件或关系型表 `messages(id, role, content, created_at)` 存储会话。这种线性抽象在简单场景下足够，但在长生命周期、强状态的真实业务中迅速遇到结构性瓶颈。

### 1.2 线性会话日志的六类失效模式

我们通过实际工程实践梳理出线性日志无法优雅解决的六类问题，下文 §3 将逐一给出针对性解法：

1. **上下文压缩**——线性结构没有"原内容"可指代，要么截断丢失，要么在另一处另存摘要，**结构与历史脱节**。
2. **回退与重试**——"回到第 5 轮"意味着破坏性地删除后续消息，**历史不可信**，审计与调试不可能。
3. **多方案实验**——必须复制整段历史开新会话，**分叉、合并不优雅**，且分叉后无法引用上游。
4. **崩溃恢复**——线性结构无法回答"上次执行到哪一步、调用了哪些工具、用了多少 token"，**没有可定位的检查点**。
5. **模型/思考等级切换**——没有任何"状态变更"的概念，只能在系统里另存一份，**与消息流脱钩**。
6. **多任务隔离**——审批中断时用户又发新消息，所有内容混在同一条时间线，**无法区分"前台会话"和"挂起任务"**。

### 1.3 本文的工作

本文以"问题—方案对照"为基本叙事结构：每节先呈现某类具体失效模式，再给出有向树方案在该问题上的针对性解法。

本文结构如下：第 2 节讨论相关工作；第 3 节按六类问题逐项展开系统设计；第 4 节深入实现细节；第 5 节讨论方案的工程意义与局限；第 6 节总结全文。

---

## 2 相关工作（Related Work）

### 2.1 LLM 框架中的会话存储

主流 LLM 框架（LangChain、LlamaIndex、Haystack 等）通常将会话历史以**消息列表**形式暴露给上层应用，由开发者自行选择持久化方式。LangGraph 引入了**检查点（checkpointer）**机制以支持 Agent 状态机的持久化与恢复，但其抽象目标是"Agent 状态"而非"对话历史"，二者关注点不同：checkpointer 关心状态机的迁移与恢复，会话树关心对话的可分支、可压缩与可审计。

**问题**：现有方案没有"对话历史"的一等抽象——它要么是 list，要么是 checkpointer 的一个字段，**没有分支、压缩、状态变更等语义原语**。

### 2.2 上下文压缩技术

针对 LLM 上下文窗口有限的问题，已有研究从三个方向切入：（1）**滑动窗口**（sliding window），保留最近 N 轮消息；（2）**摘要压缩**（summarization-based），用 LLM 把历史压缩为摘要；（3）**检索增强**（retrieval-augmented），用向量数据库按需检索。这些工作大多**以"消息列表"为输入**——压缩产物以独立的字段或键存储，与原消息流脱节，难以处理多次压缩的链式管理与历史溯源。

**问题**：压缩的"压缩"难以管理——多轮压缩后无法定位"哪些信息已被摘要"、"哪些信息仍在原文中"，更无法回滚到任一历史压缩版本。

### 2.3 可分支会话与版本化

Git 在代码领域证明了**有向无环图（DAG）+ 指针移动**相比线性日志的优越性。Pi（earendil-works 出品）将这一思想引入 AI Agent 的会话存储，提出**会话树形结构**。本文的工作即在 Pi 模型基础上完成 Python + SQLite 工程实现。

**问题**：将 Git 思想引入会话存储的关键难点在于——Git 操作的是文本 diff，可合并；而会话涉及语义连续性，简单的指针移动必须配合强不变式才能保证数据合法性。

### 2.4 事件溯源与 CQRS

事件溯源（Event Sourcing）思想在领域驱动设计（DDD）中被广泛讨论，在 CQRS 架构中作为写模型的实现基础。本文的 SQLite 持久化方案即采用此思想：状态不直接存储，而是存储导致状态变化的事件序列，加载时通过重放事件重建状态。

**问题**：典型事件溯源应用（订单、账户）的事件序列是**平面日志**。若直接套用到会话，会丢失"分支"、"父子关系"等结构信息——必须将事件序列设计为**树形语义**才能承载会话需求。

---

## 3 系统设计：以问题驱动方案

本节按六类失效模式逐项展开：每项先呈现"原有方式的问题"——具体失效模式、带来的工程痛点；再给出"我们的方案如何解决"——核心数据结构、关键算法、为什么这样设计。

### 3.1 问题一：上下文压缩与原历史脱节

#### 3.1.1 原有方式的问题

线性消息列表在压缩时面临两难：

- **若"截断旧消息"**——历史永久丢失，无法回滚，无法审计，无法回答"三小时前那次压缩前我们讨论到了哪里"。
- **若"另存摘要"**——摘要与原消息流在两个数据结构中维护，二者关系靠"时间戳"等隐式线索维系。一旦多次压缩，链式管理崩溃：
  - 无法定位"哪些原消息已被压缩、哪些未压缩"；
  - 无法在摘要与原消息之间做 diff；
  - 若摘要错了想重做，无法回退到"压缩前的原始状态"。

更深层的问题：**压缩破坏了"消息是同一类数据"这一假设**。在压缩后的会话中，消息与摘要属于不同语义层级，但线性结构迫使二者共享同一个 list，**没有结构化的载体表达"这段是摘要，那段是原文"**。

#### 3.1.2 我们的方案：压缩是树上的一个 `compaction` 节点

我们**将压缩重构为"在树上追加一个 `compaction` 节点"**，使压缩后的原文与摘要共存于同一持久化结构：

- `compaction` 节点携带 `summary`（LLM 摘要文本）、`retained_tail`（保留的最近若干条消息）、`tokens_before`（压缩前 token 数）、`details`（如文件操作清单）、`usage`（本次压缩自身消耗的 token）。
- 原文**不被删除**——它仍在树中，作为 `compaction` 节点的祖先。审计、调试、回滚都能找到原文。
- 投影层（`build_session_context`）默认找到最近一个 `compaction` 节点后，**只把 `[compaction, ...之后]` 送入 LLM 上下文**——压缩替换在投影阶段完成，不修改树本身。

**多轮压缩的链式管理自然解决**：会话树上**最新一个 `compaction` 节点**就是当前 LLM 看到的"历史"，其祖先的 `compaction` 节点是"历史的摘要"，最顶层的原始消息是"全量原历史"。**树形结构使"压缩的压缩"成为一棵树而非一串列表**。

**跨压缩的信息保留**：为避免多次压缩丢失关键事实，`prepare_compaction` 在做本次切割点计算时，**把上一次 `compaction` 节点的 `retained_tail` 映射为虚拟条目纳入计算**——`retained_tail` 在下一次压缩中"仍然在场"，与新消息一起被评估是否需纳入摘要。文件操作清单（`readFiles` / `modifiedFiles`）也通过 `details` 字段跨压缩累积。

#### 3.1.3 为什么这样设计

这一设计带来三个关键收益：

- **崩溃后可回退到任意历史**——因为原文未删除，删除"最近的 `compaction` 节点"即可回退到上一次压缩前的状态。
- **压缩的质量可独立审计**——比较 `compaction` 节点的 `summary` 与其祖先的实际消息，可量化"压缩丢失了多少信息"。
- **多轮压缩无需额外链式管理**——`compaction` 节点本身是树的一部分，沿 `parent_id` 自然形成压缩链。

### 3.2 问题二：回退与重试破坏历史

#### 3.2.1 原有方式的问题

模型选错方案时，"回到第 5 轮"在传统实现中意味着 `messages = messages[:5]`——**破坏性删除**。这带来三重问题：

- **历史不可信**：用户问"昨天你说的那个方案呢？"——系统答"已被删除"。
- **审计与调试不可能**：工程师无法复现"模型选错的中间过程"，因为中间过程已被抹去。
- **并发冲突**：如果用户同时在另一窗口看这条历史，删除会让"看到的消息数"产生不一致。

更深层的问题：**回退不是消息的反操作，而是"撤销一系列后续变更"**。线性结构无法表达"哪些消息属于同一回退单元"，回退粒度只能精确到单条消息或粗暴到全清。

#### 3.2.2 我们的方案：回退 = 移动车道指针

我们引入**车道（Lane）**机制：每个车道维护一个 `leaf_id` 指针，指向该车道当前所处的树节点。`create_lane(name, at)` 从 `at` 节点开新分支；`move_lane(name, to)` 把指针移到 `to`——**"导航"在底层就是一次指针移动**。

回退的实现：**"回到第 5 轮"等价于 `move_lane("main", entry_5.id)`**——不删除任何数据，只改变 main 车道指向的 leaf。历史仍然完整保留在树中。

**多任务隔离自然涌现**：审批中断时用户又发新消息，方案是：

- `main` 车道保持原 leaf 不动（挂起的任务仍在原位）；
- 新建 `interrupt` 车道，从 main 当前 leaf 之前的位置开新分支；
- 新消息写入 `interrupt`，新任务的 leaf 推进；
- 审批恢复时，**只需把 `main` 车道指针移回原 leaf**——不删除 `interrupt` 的任何内容。

`operation_started` / `operation_finished` 记录挂在车道上，**车道 + 记录共同表达"前台任务 / 后台任务"**。

#### 3.2.3 为什么这样设计

指针移动而非删除的历史观，在 Git 中已被证明有效（`git checkout` 不删除任何 commit）。在会话场景中，指针移动的成本是 O(1)（一次 mutation 写入），而删除 + 重建的方案是 O(n)。更重要的是，**指针移动保留了完整因果链**——任何"分支尝试"都可追溯、可回放、可对比。

### 3.3 问题三：多方案实验的分叉代价

#### 3.3.1 原有方式的问题

线性日志下，"同一对话尝试两种方案"意味着：

- **方案 A**：保留主消息列表，方案 A 的回复写进去；
- **方案 B**：复制整段历史开新会话，方案 B 的回复写进去。

**复制整段历史**带来三方面代价：

- **存储成本翻倍**：每次实验都复制上游历史，N 个实验需要 N 份上游历史。
- **同步问题**：上游某条消息被修改（哪怕是 typo 修正）时，所有下游分叉都需要重放——容易遗漏。
- **引用断裂**：分叉后的消息无法引用上游具体某条消息（"刚才你说的第 5 轮"），只能引用整个上游。

更深层的问题：**"分叉"应当是会话的一等公民**。在调试 agent、对比 prompt、对比模型时，**分叉不是偶发操作而是日常操作**——任何让分叉变贵的方案都会让这些工作流难以前进。

#### 3.3.2 我们的方案：会话内 Lane + 跨会话 Fork

我们提供**两层分叉机制**：

- **会话内 Lane 分叉**：`create_lane("experiment", at=entry_5.id)` 在原会话开新分支，**不复制任何数据**——`experiment` 车道从 entry_5 开始推进自己的 leaf，与 `main` 车道共享 entry_5 之前的所有节点。同一会话可有多条 lane 独立推进，**互不干扰**。
- **跨会话 Fork**：`repo.fork(source, ForkOptions(scope="branch", entry_id=at))` 在新会话中只复制从 target 开始的分支路径，**labels 随内容复制、records 不复制**（操作日志不应污染新会话）。Fork 在单一 SQLite 事务中完成，崩溃只留"空会话"，不出现半成品分叉。

**零冗余的分支合并**：当用户想"合并实验结果"时，方案 A 与方案 B 的共同祖先是 entry_5，**两份历史只差 entry_5 之后的节点**——把 B 的新节点引用进来即可，无需复制 entry_5 之前的内容。

#### 3.3.3 为什么这样设计

**Lane vs Fork 的边界**与会话内/跨会话的边界自然对应：

- Lane 适合"临时实验、不离开当前会话上下文"——调试 prompt、尝试工具参数。
- Fork 适合"独立产物、需要持久化"——对比不同模型基线、产出可分享的实验结果。

二者共享"只复制分支路径、不复制上游"的语义，**避免了上游修改的同步问题**——上游是引用而非拷贝。

### 3.4 问题四：崩溃恢复无检查点

#### 3.4.1 原有方式的问题

Agent 跑到一半崩溃（OOM、用户关闭浏览器、服务器重启）后，线性结构无法回答：

- 上次执行到哪一步？
- 调用了哪些工具、结果是什么？
- 消耗了多少 token？
- 当前消息列表是否完整？

传统方案是"定期落库整个消息列表"——但有两个问题：

- **落库间隔内的丢失**：落库间隔若为 5 分钟，则崩溃可能丢失 5 分钟工作。
- **并发写竞争**：落库时另一线程修改了列表，会得到不一致快照。

更深层的问题：**检查点不是"消息列表的副本"**——它是"操作的过程记录"。线性结构只能表达"消息有哪些"，无法表达"哪些工具被调用、结果如何、是否重试、错误码是什么"。

#### 3.4.2 我们的方案：append-only mutation 日志 + Record 链

**持久化层**：所有写操作（`append_entry` / `append_record` / `create_lane` / `move_lane` / `set_name` / `set_label`）通过统一的 `_append_mutation` 方法：

1. `_persist(mutation)`：INSERT row + flush（不 commit）。
2. `db.commit()`：真正落盘。
3. `apply_mutation(mutation)`：更新内存 `SessionState`。

关键不变量是**"内存状态永远不超前于磁盘"**——这一保证使崩溃后重放可得到与崩溃前完全一致的状态。

**操作日志**：每一次 `Record` 都是一颗时间胶囊，9 种类型覆盖完整生命周期：

```
operation_started → step_attempt → tool_started → ... → operation_finished
                                       ↓ (异常分支)
                              abort_requested → operation_finished (outcome=aborted)
```

`find_open_operations(lane)` 是恢复语义的入口：

| 同一 lane 的开放操作数 | 状态 | 启动策略 |
|----------------------|------|---------|
| 0 | 空闲 | 正常启动新操作 |
| 1 | 挂起 | 恢复上次操作（resume） |
| ≥ 2 | 数据损坏 | 抛错，提示人工介入 |

**同车道并发强制不允**：`append_record` 在写入 `operation_started` 前先调用 `find_open_operations(record.lane, 1)`，若返回非空立刻抛错——并发请求被存储层拒掉，免去外部加锁。

#### 3.4.3 为什么这样设计

**为什么用 append-only 而非就地更新**：

- **简单**：写入路径只有 `INSERT`，无需考虑 `UPDATE` 失败的恢复。
- **可重放**：崩溃后的状态 = 重放所有 mutation 行的结果，与崩溃前一致。
- **可审计**：mutation 日志本身就是审计日志。
- **模式演进无成本**：codec 处理 JSON 字段，字段调整无需数据库 migration。

**为什么用 Record 而非在 message 里附加元数据**：

- Record 不在树上，**不污染 LLM 看到的消息流**。
- Record 独立索引，按 `lane` / `run_id` / `type` / `operation_kind` 高效查询。
- Record 的 `usage` 累加公式独立于 message，**统计面板与对话历史解耦**。

### 3.5 问题五：状态变更无载体

#### 3.5.1 原有方式的问题

切换 provider / 调整 thinking level / 激活不同工具集——这些"状态变更"在线性结构中如何表达？

传统做法是"另存一份配置"——`session.model = "gpt-4"`、`session.thinking_level = "high"`。这带来：

- **历史不可追溯**：用户问"为什么中间用过 deepseek？"——因为 `session.model` 当前是 `gpt-4`，没有记录显示中间切到过 deepseek。
- **回放不可能**：调试 agent 时无法"重放到切模型前的状态"。
- **状态与消息脱钩**：消息流描述了对话内容，配置描述了系统状态——**二者关系靠时间戳维系**。

更深层的问题：**状态变更本身是会话内容的一部分**。在长生命周期 agent 中，状态变更往往与决策强相关（"因为这个原因切到 deepseek"），**没有载体的状态变更无法参与决策的因果链**。

#### 3.5.2 我们的方案：状态变更也是 Entry 节点

我们**把状态变更提升为树的节点**：

- `model_change(provider, model_id)` —— 切模型。
- `thinking_level_change(thinking_level)` —— 调整思考等级。
- `active_tools_change(active_tool_names)` —— 激活/停用工具集。

这些节点与 `message` 节点共享同一种抽象（都是 `Entry`），享有同一种不变式保证。`build_session_context` 沿路径取**最后一个**状态变更节点作为派生状态，**不进入消息流但影响 LLM 行为**。

**因果链自然涌现**：切模型之前发生了什么、为什么切、切之后发生了什么——`model_change` 节点的 `parent_id` 链完整保留因果关系。

**回放能力**：调试 agent 时可"重放到切模型前的状态"——`move_lane` 到 `model_change` 之前的节点即可，**所有状态变更在 LLM 看来"不存在"**。

#### 3.5.3 为什么这样设计

**统一抽象的力量**：消息、压缩、状态变更、分支摘要都是 `Entry` 节点的实例——**所有"会话内容"共享同一种抽象**。这意味着：

- 不变式只需为 `Entry` 设计一套（6 条），状态变更无需额外约束。
- 状态变更自然获得"崩溃一致 + 可重放 + 可分支"的全部能力。
- 派生状态的计算（取最后一个相关节点）极简——O(path length)。

### 3.6 问题六：多任务隔离混乱

#### 3.6.1 原有方式的问题

Agent 审批中断（高风险操作需用户确认）时，用户又发新消息——线性结构如何处理？

- **方案 A：阻塞**——等待审批，不响应新消息。用户等待，体验差。
- **方案 B：新开会话**——新消息归属新会话，与审批完全脱钩。用户问"刚才那个审批怎么样了？"时系统答"那是另一个会话"。
- **方案 C：插队**——新消息插到审批消息之后。审批结果回来时插到哪？中断语义模糊。

更深层的问题：**"会话"应当是用户与系统交互的完整轨迹**，而非"消息的容器"。审批、子任务、并发请求都是这一轨迹的不同侧面，**没有抽象能区分它们**——线性结构迫使"主对话 / 后台任务"混在一起。

#### 3.6.2 我们的方案：Lane + Record 双层隔离

我们用**双层机制**实现多任务隔离：

**Lane 层**（粗粒度）：每个独立任务占用一条 lane。
- 主对话走 `main` 车道。
- 审批中的写操作可在独立 lane 上挂起，记录状态变更。
- 用户的并发新消息可开 `interrupt` 车道，与 `main` 互不干扰。
- 任务结束后，**`move_lane` 把 `main` 重新对齐到完整历史**——主对话流重新连贯。

**Record 层**（细粒度）：每一次操作的完整生命周期被记录。
- `operation_started` 标识操作开始。
- `step_attempt` 标识重试。
- `tool_started` 标识工具调用起点。
- `operation_finished`（带 `run_id`）清理开放操作状态。

**同车道并发强制不允许**：`append_record` 在写入 `operation_started` 前先检查同 lane 已有开放操作——**并发请求被存储层拒掉**，免去外部加锁。这使"前台任务 / 后台任务"在数据层就有清晰边界。

#### 3.6.3 为什么这样设计

**Lane 与 Record 的职责分离**：

- **Lane 解决"哪些消息属于同一任务"**——任务边界通过 lane 指针表达。
- **Record 解决"任务执行到哪一步"**——执行状态通过 operation lifecycle 表达。

二者结合，**多任务场景下的恢复、并发、审计都能从结构化数据中直接得到**——无需在应用层维护额外的状态机。

---

## 4 实现细节：以算法落地问题

本节对 §3 的设计给出具体实现细节。每节先指明要解决的实现层面问题，再给出对应的算法与工程取舍。

### 4.1 内存状态机：6 条不变式保证树的合法性

#### 4.1.1 问题：如何让树在并发写、崩溃、人为篡改下始终合法

树形结构比线性结构复杂——它需要保证"每个新节点的父链合法"、"id 不重复"、"seq 连续"。若校验逻辑分散在各个写入点，容易遗漏；若校验依赖全局扫描，则成本高。

#### 4.1.2 方案：6 条不变式 + 集中校验

`SessionState.apply_mutation` 是**所有写入的必经路径**。6 条不变式在此集中校验：

1. `seq` 必须连续（`seq == self._sequence + 1`）。
2. `id` 全局唯一。
3. lane 必须存在。
4. 新节点的 `parent_id` 必须等于目标 lane 的当前 leaf。
5. 父节点必须存在。
6. record 的 lane 必须存在；`label` fact 的 `target_id` 必须存在。

**完全局部化**：每条规则仅依赖当前 mutation 与当前内存状态，无需回溯历史——校验 O(1)，适合流式应用。

**环检测**：`_walk_to_root` 用 `visited` 集合做环检测——手改过的会话文件若出现循环父链，会被 `SessionError("invalid_entry", f"Session branch contains a cycle at {current.id}")` 明确拒绝。

#### 4.1.3 实现要点

- **副作用同步**：`apply_mutation` 在校验通过后同步更新 `_sequence` / `_used_ids` / `_entries` / `_entries_by_id` / `_lanes` / `_log` / `_stats` / `_open_operations_by_lane` 等 9 类内部结构。
- **失败即抛错**：`apply_mutation(mutation, invalid=None)` 接受可选的 `invalid` 回调（仅测试使用），生产路径全部走 `raise SessionError("invalid_entry", ...)`。
- **`_open_operations_by_lane` 维护规则**：`operation_started` 写入、`operation_finished`（带 `run_id`）移除；`abort_requested` **不**移除——必须等 `operation_finished` 兜底，否则留下"挂死"的开放操作。

### 4.2 写入路径：先持久化后应用内存

#### 4.2.1 问题：如何保证"崩溃后状态 = 崩溃前状态"

若先更新内存再落盘，崩溃时内存有数据但磁盘没有——下次启动看不到。若先落盘再更新内存，崩溃时磁盘有数据但内存没有——下次启动可重放。

#### 4.2.2 方案：先持久化后应用内存

`_append_mutation` 的三步序列：

1. `_persist(mutation)`：INSERT row + flush。
2. `db.commit()`：真正落盘。
3. `apply_mutation(mutation)`：更新内存 `SessionState`。

**关键不变量**："内存状态永远不超前于磁盘"——若步骤 2 失败，rollback 不会留下半成品；步骤 3 失败（实际上几乎不会，因为只更新内存）不会影响下次重放。

#### 4.2.3 Fork 的特殊处理

Fork 在新会话下**先全部 `_persist`（不 commit），然后单次 `db.commit()`，最后再把 mutations 喂给内存**。中途崩溃只留"空的新会话 row"——不会出现半成品分叉。

### 4.3 双路径 token 估算：解决"模型偶发不返回 usage"

#### 4.3.1 问题：压缩阈值判定依赖 token 数，但 token 估算依赖 usage

LLM 调用可能不返回 `usage` 字段（第三方代理、错误响应、自定义模型）。若估算完全依赖 usage，则无 usage 时无法判定压缩阈值。

#### 4.3.2 方案：真实 usage 优先 + chars/4 兜底

`estimate_context_tokens` 算法：

1. 从最新 message 向前找第一个满足条件的 assistant 消息：`role == "assistant"`、`usage` 存在、`stop_reason ∉ {aborted, error}`、`usage` 是 dict 且 `calculate_context_tokens(usage) > 0`。
2. 找到 → `usage_tokens = calculate_context_tokens(usage)`，`trailing_tokens = Σ estimate_tokens(messages[i+1:])`，返回 `usage_tokens + trailing_tokens`。
3. 找不到 → `estimated = Σ estimate_tokens`，返回该值。

`calculate_context_tokens` 自身有 fallback：`totalTokens` 优先；否则 `input + output + cacheRead + cacheWrite`。

#### 4.3.3 单消息估算的分桶规则

按 `role` 分桶，`chars/4` 启发式作为兜底：

| role | 计算方式 |
|------|---------|
| `user` | `ceil(text + image_chars / 4)`；image block 按 4800 字符估算 |
| `assistant` | 累加 `text` / `thinking` / `toolCall(name + JSON.stringify(args))` 字符后 `ceil(/4)` |
| `bashExecution` | `ceil(len(command) + len(output) / 4)` |
| `branchSummary` / `compactionSummary` | `ceil(len(summary) / 4)` |

### 4.4 切割点算法：解决"绝不切碎工具结果"

#### 4.4.1 问题：朴素累积 token 可能在工具结果中间切割

若切割点位于 `toolResult` 消息中间，模型会看到"工具调用了但没结果"或"工具结果了但没调用"，破坏对话连续性。

#### 4.4.2 方案：白名单切割点 + 6 步算法

**允许作为切割点的角色**：`user`、`assistant`、`bashExecution`、`custom`、`branchSummary`、`compactionSummary`。**`toolResult` 不在白名单内**——任何 tool 消息之间的切割都会被跳过。

**6 步算法**：

1. 收集 `[start_index, end_index)` 范围内合法 cut points（按白名单）。
2. 若无 → 返回 `(start_index, -1, False)`，表示"无法切"。
3. 从 `end_index` 向前累积 token（仅对 message），直到累加 ≥ `keep_recent_tokens`。
4. 在累积达到阈值的位置 `i`，从 cut_points 中找第一个 ≥ `i` 的，作为 `cut_index`。
5. 如果 `cut_index` 之前的条目不是 `compaction/message`，回退到前一个合法点。
6. 判断 split turn：cut 是 user 消息 → 不 split；cut 是 assistant 消息 → 向前找 turn start（user 或 bashExecution 或 branch_summary）。

#### 4.4.3 split turn 产物

`prepare_compaction` 根据 `is_split_turn` 把输出分成三段：

- `messages_to_summarize`（history_end 之前，**不包含 split turn 的 turn prefix**）
- `turn_prefix_messages`（**仅 split turn 触发**，从 turn start 到 cut 的内容——通常是一条 user 消息，**留在压缩之外**，让模型知道"这一轮的开头是什么"）
- `retained_tail`（cut 之后到 end——**进入压缩节点作为 retained_tail**）

### 4.5 分支摘要：公共祖先算法实现零冗余合并

#### 4.5.1 问题：如何计算"两份历史的差异部分"

切换车道时，被抛弃的分支需要压缩为摘要挂到目标位置。朴素做法是"复制整个被抛弃分支"——但大部分内容与目标分支共享（公共祖先之前），冗余严重。

#### 4.5.2 方案：公共祖先 + 仅摘要差异部分

```
collect_entries_for_branch_summary(session, old_leaf_id, target_id):
    1. old_path = {entry.id for entry in find_entries_on_branch(start=old_leaf_id)}
    2. target_path = find_entries_on_branch(start=target_id)
    3. common_ancestor_id = first entry in target_path where entry.id ∈ old_path
    4. entries = []
       current = old_leaf_id
       while current and current != common_ancestor_id:
           entry = session.get_entry(current)
           entries.append(entry)
           current = entry.parent_id
       entries.reverse()
    5. return (entries, common_ancestor_id)
```

**时间复杂度**：O(depth_old + depth_target)——与会话总长度无关，仅与相关分支深度相关。

#### 4.5.3 token 预算下的截断

按**从尾到头**的顺序累加（最新消息优先），直到超 `token_budget`：

- 普通 message / compaction / branch_summary：累加并加入。
- 若超预算且当前是 `compaction` / `branch_summary`，**且**当前总量 `< token_budget * 0.9`，仍**加入**（摘要节点优先保留）。
- 否则 `break`（丢弃更早的消息）。

### 4.6 跨压缩文件操作累积

#### 4.6.1 问题：多次压缩后，模型动过哪些文件丢失

压缩把 assistant 消息的 `toolCall` 块摘要掉，原始文件路径也随之丢失。多次压缩后，模型不知道自己曾经读过/改过/写过哪些文件。

#### 4.6.2 方案：把文件操作清单存进 `compaction.details`

每次压缩时：

1. 若前一次 `compaction` 的 `details.readFiles` / `details.modifiedFiles` 存在，把它们预填进 `file_ops` 集合。
2. 扫描本次 `messages_to_summarize`（若 split turn，再加 `turn_prefix_messages`），按 `toolCall.name` 把 `read` / `write` / `edit` 的 `arguments.path` 加入相应集合。
3. 摘要文本追加 `<read-files>...</read-files>` 与 `<modified-files>...</modified-files>` 段。
4. `details` 字段存 `{"readFiles": [...], "modifiedFiles": [...]}`，供下次压缩累积。

`extract_file_ops_from_message` 扫描 assistant 消息的 `toolCall` 块，**set 自动去重**——同一路径多次出现在不同消息中只记一次。

### 4.7 上下文投影：派生状态 + 压缩替换

#### 4.7.1 问题：树不是直接喂给 LLM 的内容

会话树包含消息、压缩、状态变更、自定义条目——直接送入 LLM 会得到"模型看到了不该看的东西"或"模型没看到该看的东西"。

#### 4.7.2 方案：三步投影

```
build_session_context(path_entries):
    state = derive_session_context_state(path_entries)
    context_entries = build_context_entries(path_entries, entry_transforms)
    messages = []
    for entry in context_entries:
        messages.extend(session_entry_to_context_messages(entry, ...))
    return {**state, "messages": messages}
```

**派生状态**沿路径取最后一个相关节点（`thinkingLevel` / `model` / `activeToolNames`），不进入消息流但影响 LLM 行为。

**压缩替换**默认找到最近一个 `compaction` 节点，取 `[compaction, ...之后]`——压缩替换在投影阶段完成，不修改树本身。

**消息投影规则**：

| Entry 类型 | 投影结果 |
|-----------|---------|
| `message` | `[message]`；`stopReason == "deferred"` 时返回 `[]` |
| `compaction` | `[compactionSummary, *(retained_tail or [])]` |
| `branch_summary` | `[branchSummary]` |
| `custom` | `[]` 或 `entry_projectors[custom_type](...)` 的返回值 |
| 其他 | `[]` |

`stopReason == "deferred"` 的跳过是有意的——延迟响应的占位消息不应进入下一轮上下文。**但消息并未从树中删除**，审计与调试仍可查到。

### 4.8 与 LangGraph checkpointer 的职责分离

#### 4.8.1 问题：两套持久化系统如何不冲突

Agent 状态机的 checkpoint（LangGraph checkpointer）与会话树（对话历史 + 审计）关注点不同——若不分离，重复存储、数据不一致。

#### 4.8.2 方案：互补存在 + 接入层独立事务

接入层（`app.services.session_tree`）在 chat / Agent 流程的关键节点**额外**写入树（`mirror_user_message` / `mirror_assistant_message` / `mirror_subagent`），**不替代** checkpointer。

每个操作独立打开 / 关闭树会话（释放 ORM 连接），调用方完全不需要管生命周期。`get_or_create_tree_session` 处理"两个请求同时创建同一 chat_session 的树"的并发：先 `find_metadata`，找不到则 `create`，若 `create` 抛 `already_exists` 则重新 `open`。

---

## 5 讨论（Discussion）

### 5.1 工程意义

#### 5.1.1 把"对话"提升为一等公民

本文的核心主张是：**对话本身应当是一个有结构的、可被操作的数据结构，而非一个简单的列表**。这一提升带来的工程意义是多方面的：

- **可分支**使 A/B prompt、模型对比、agent 编排调试成为自然操作——无需额外的实验框架。
- **可压缩**使长会话管理从"定时清理"转向"持续可用"——压缩后的历史仍可审计、可回溯。
- **可审计**通过完整的 `Record` 链使任何工具调用、任何 token 消耗都可按 `run_id` 串联——满足金融、医疗等强可解释性需求。
- **可恢复**通过 SQLite 事务 + WAL + 重放机制，使"Agent 跑到一半崩溃"不再意味着"状态丢失"。

#### 5.1.2 与传统方案的兼容性

- **JSON 兼容字段**：`message` 是 LangChain 兼容字典，可直接送入 LLM 推理。
- **可拆解的 LLM 调用**：压缩的纯逻辑（`prepare_compaction`）与 LLM 摘要（`CompactionEngine`）解耦，可独立测试、替换供应商。
- **可选 SQLite**：`InMemorySessionStorage` 提供无持久化版本，用于测试与原型。

### 5.2 局限

#### 5.2.1 不适合的场景

会话树相比线性列表有更高的工程复杂度。对以下场景**过度设计**：

- 纯聊天、单轮问答、轻量客服：线性列表 + 定时清理已足够。
- 极短生命周期的会话：树的开销不带来可观的收益。

#### 5.2.2 已知工程限制

- **重放无增量**：每次 `open()` 都重放所有 mutation 行，深会话下首屏加载成本 = O(mutations)。目前没有 checkpoint 化重放。
- **`payload` JSON 字段过滤单向**：codec 丢弃**未声明**字段，但不剔除声明字段的"非预期类型"——靠反序列化端的字段类型注解 + 上层 `validate_target` 等做最终校验。
- **`build_context_messages` 不解析 `toolCall` 内容**：仅把 `compactionSummary` / `branchSummary` 转为带前缀的 `HumanMessage`，其他 role 透传。若 LLM 需要工具结果原文，需直接走 `find_entries` + 自定义投影。

### 5.3 未来工作

1. **压缩节点的版本化与差异比较**。当用户手动调整 `compaction.summary` 时，可像 Git diff 一样呈现与原 LLM 摘要的差异。
2. **跨会话的语义检索**。会话树天然按 `parent_session_key` 保留血统，可基于此构建跨会话的语义索引。
3. **压缩质量评估**。当前没有自动化的压缩质量评估——摘要可能丢失关键事实。引入 LLM-as-judge 或人工反馈机制可提升压缩可靠性。
4. **增量重放优化**。引入周期性 checkpoint（每 N 条 mutation 做一次状态快照）可显著提升加载性能。
5. **多 Agent 协作的会话视图**。扩展 Lane 语义可支持多 Agent 共享同一会话的不同 Lane 视图。

---

## 6 结论（Conclusion）

本文以"问题—方案对照"为基本叙事结构，针对线性会话日志在六类典型场景下的失效模式，给出有向树方案的针对性解法：

- **上下文压缩问题** → 压缩是树上的一个 `compaction` 节点，原文与摘要共存于同一持久化结构。
- **回退破坏历史问题** → 回退等价于 `move_lane`，指针移动而非删除。
- **多方案实验分叉代价问题** → Lane + Fork 两层分叉机制，上游以引用而非拷贝共享。
- **崩溃恢复无检查点问题** → append-only mutation 日志 + Record 操作链。
- **状态变更无载体问题** → 状态变更也是 Entry 节点，与消息共享同一抽象。
- **多任务隔离混乱问题** → Lane（粗粒度任务边界）+ Record（细粒度执行状态）双层隔离。

本文的核心贡献在于：（1）以"问题—方案对照"展开工程论证，展示每类问题的具体失效模式与针对性解法；（2）将"对话"从一维时间线重构为有向树，把分支、压缩、状态变更等高级操作提升为一等公民；（3）通过 6 条不变式 + 共享 seq + 先持久化后应用内存，使崩溃一致性从工程承诺变成可验证的不变式；（4）通过双路径 token 估算、6 步切割点算法、跨压缩文件操作累积、公共祖先计算等具体算法，使方案在长会话、长分支等场景下表现稳定。

我们相信，这一模型对长生命周期、强可解释性、多实验并存的 AI Agent 系统具有参考价值。该项目已开源，期待社区在实践中进一步验证与扩展。

---

## 参考文献（References）

[1] Pi Session Tree (TypeScript reference implementation). earendil-works.

[2] LangChain / LangGraph Documentation.

[3] SQLAlchemy 2.0 Documentation.

[4] Fowler, M. (2005). Event Sourcing. https://martinfowler.com/eaaDev/EventSourcing.html

[5] SQLite WAL Mode. https://www.sqlite.org/wal.html

---

## 附录 A：术语表

| 术语 | 含义 |
|------|------|
| **Entry** | 树上的一个节点。共 7 种类型。 |
| **Record** | 车道上的操作日志。共 9 种类型。 |
| **Fact** | 全局 set 语义的键值。`name` 与 `label`。 |
| **Lane** | 车道。树上的指针，指向某个 entry id。`main` 是默认车道。 |
| **Compaction** | 压缩。在树上追加一个 `compaction` 类型 entry，承载摘要与保留尾。 |
| **Branch Summary** | 分支摘要。切换车道时，被抛弃分支压缩为 `branch_summary` 挂到目标位置。 |
| **seq** | 全局单调递增序列号。Entry / Record / Lane / Fact 共享。 |
| **公共祖先** | 两个分支路径上**都存在**的最近节点。分支摘要的核心计算对象。 |
| **Hook** | 扩展点。`before_compact` / `after_compact` / `before_branch_summary` / `after_branch_summary`。 |
| **`stopReason`** | 助手消息的停止原因。`deferred` 消息在投影时被跳过。 |

## 附录 B：六类问题—方案对照速查

| 失效模式 | 原方案代价 | 本方案解法 | 关键机制 |
|---------|----------|----------|---------|
| 压缩与原历史脱节 | 摘要与原文在两处维护，多轮链式管理崩溃 | 压缩是树上的 `compaction` 节点 | 树形结构 + `retained_tail` 跨压缩累积 |
| 回退破坏历史 | `messages = messages[:5]` 不可逆 | `move_lane("main", entry_5.id)` | 指针移动而非删除 |
| 分叉代价高 | 复制整段历史，N 个实验需 N 份上游 | Lane 同会话内 / Fork 跨会话，只复制分支路径 | 引用而非拷贝 |
| 崩溃无检查点 | 定期落库完整快照，间隔内丢失 | append-only mutation 日志 + `Record` 链 | 先持久化后应用内存 |
| 状态变更无载体 | 另存 `session.model` 等配置，与消息脱钩 | 状态变更也是 `Entry` 节点 | 统一 Entry 抽象 |
| 多任务隔离混乱 | 阻塞/新开会话/插队各有缺陷 | Lane（粗粒度）+ Record（细粒度） | 双层隔离 + 同车道并发强制 |
