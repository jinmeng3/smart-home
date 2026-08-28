# 会话树与上下文压缩实现评价

> 本文对后端中「会话树存储（`app/session_tree`）」与「上下文压缩编排（`app/compaction`）」两套模块的实现做客观评价，覆盖架构、正确性、健壮性、测试与改进方向。评价基于当前代码（截至 2026-08），力求事实准确、问题分级明确。

## 目录

1. [概述](#1-概述)
2. [架构与分层](#2-架构与分层)
3. [模块逐项评价](#3-模块逐项评价)
4. [正确性与健壮性](#4-正确性与健壮性)
5. [优点总结](#5-优点总结)
6. [问题与风险](#6-问题与风险)
7. [测试覆盖评价](#7-测试覆盖评价)
8. [改进建议](#8-改进建议)

---

## 1. 概述

后端把 Pi 的「会话树形存储 + 上下文压缩」机制移植成了 Python + SQLAlchemy 实现，并按职责拆成四层：

| 层 | 包 | 职责 |
|----|----|----|
| 存储层 | `app/session_tree/session/` | 树 / 车道 / 事实的 append-only 存储（内存 + SQLite） |
| 纯逻辑层 | `app/session_tree/compaction/` | 切割点、token 估算、压缩/分支摘要准备（无副作用） |
| 编排层 | `app/compaction/` | LLM 摘要生成、提示词、序列化、事件/钩子、`CompactionEngine` |
| 接入层 | `app/services/session_tree.py` + `runner.py` | 把树绑定到 `ChatSession`、镜像消息、触发压缩 |

设计目标明确：**历史只增不改（append-only）、树可分支可恢复、上下文超限时把旧内容压成摘要**。整体移植忠实于 Pi 参考文档（`compaction-上下文压缩详解.md`）与本仓库的 `docs/session-tree-storage.md`，分层清晰。

---

## 2. 架构与分层

分层是本实现最突出的优点。核心计算（`prepare_compaction`、`find_cut_point`、`estimate_tokens`、`collect_entries_for_branch_summary`）被刻意做成**纯函数**，不碰 I/O 与 LLM；LLM 调用与落盘被推到编排层与接入层。这带来了两个直接好处：

- **可测试**：纯函数用内存仓库即可测，编排层用注入的 `Summarizer` 协议即可测，无需真实 LLM。
- **解耦**：`session_tree` 完全不依赖 `app.core.config`、`app.agents` 等业务模块，可独立复用。

依赖方向是单向的、健康的：

```
session_tree/compaction  ← 纯逻辑，无业务依赖
session_tree/session     ← 存储，仅依赖 errors/types
app/compaction           ← 编排，依赖 session_tree + config
app/services/session_tree ← 接入，依赖 app/compaction + session_tree + db
runner.py                ← 调用接入层
```

`Summarizer` 用 `Protocol` 定义，`CompactionEngine` 通过构造注入，是典型的依赖倒置，扩展（§10 钩子）也因此能完全接管摘要逻辑。

---

## 3. 模块逐项评价

### 3.1 存储层 `app/session_tree/session/`

**数据模型（`types.py`）**：7 种 `Entry`、9 种 `Record`、`LanePointer`、`SessionStats`、查询类型齐全，字段注释清楚。`Entry` 用「单 dataclass + 可选字段 + `type` 判别」而非继承，符合参考实现的判别联合体语义，也便于 JSON 序列化。👍

**状态机（`state.py`）**：`apply_mutation` 集中校验 6+1 条不变式（seq 连续、id 唯一、lane 存在、parent 链到 leaf、parent 存在、record lane 存在、fact target 存在），是整个实现正确性的基石。`walk_to_root` 带环检测（`visited` 集合），手改过的坏数据会被明确拒绝而非死循环。`create_fork_mutations` 复制条目时重编 seq、保留 name/labels、不复制 record，语义正确。👍

**门面与存储（`storage.py` / `sqlite.py` / `repo.py`）**：`SessionStorage` 协议让内存版与 SQLite 版共享同一接口；`append_entry` 由存储层分配 `parent_id`/`seq`/`timestamp`，杜绝写入方伪造父链；SQLite 版「先持久化、后应用内存」配合事务 + WAL，等价于 JSONL 的 torn-tail 修复。`Session.close()` 的补齐（本次接入新增）让上层能按操作释放 ORM 连接。👍

**上下文投影（`context.py`）**：`default_context_entry_transform` 只保留路径上最后一个 `compaction` 条目并拼接其后条目，`session_entry_to_context_messages` 把 `compaction` 投影为 `summary + retained_tail`，与文档 §6 一致。👍

### 3.2 纯逻辑层 `app/session_tree/compaction/`

**压缩准备（`compaction.py`）**：`find_cut_point` 从最新向最旧累积 token、`toolResult` 永不作为切割点、单轮超大时产出 split turn（历史 + 轮次前缀），逻辑与文档 §4 对齐。`prepare_compaction` 用「虚拟条目」把上次压缩的 `retained_tail` 重新纳入本次切割计算，实现迭代式压缩的边界回退，这是处理连续压缩不丢信息的关键设计。`estimate_context_tokens` 的「真实 usage 优先、chars/4 兜底」双路径也很扎实。👍

**分支摘要（`branch_summary.py`）**：`collect_entries_for_branch_summary` 找公共祖先并收集被抛弃分支；`prepare_branch_entries` 按预算从最新挑选、摘要条目有优先级保留、文件操作跨嵌套摘要累积。👍

**一个瑕疵**：`compute_file_lists` 返回 `{"read_files", "modified_files"}`（snake_case），而 `_extract_file_operations` / `prepare_branch_entries` 从 `details` 里读 `readFiles` / `modifiedFiles`（camelCase）。上层（`engine._compute_file_lists`）不得不手动做键名转换，命名风格不统一，容易踩坑。⚠️

### 3.3 编排层 `app/compaction/`

**`engine.py`**：`CompactionEngine` 的 `evaluate`（触发判定 + 跳过规则）、`compact`（非 split 一次摘要 / split 两次合并 + 文件标签追加 + 追加条目 + 重建上下文）、`generate_branch_summary` / `summarize_branch` 都实现完整。`_resolve_settings` 让显式传参优先、否则回退 `.env`，语义清晰。⚠️ 小问题：`compact()` 声明了 `context_window` 参数却未使用（实际只用 `settings.reserve_tokens` 决定摘要预算），是 API 冗余。

**`prompts.py`**：结构化摘要模板（Goal / Constraints / Progress / Key Decisions / Next Steps / Critical Context）与四种提示词（首次、更新式、轮次前缀、分支）齐全，反复强调保留精确文件路径、函数名、错误消息，符合文档 §8.1。👍

**`serialize.py`**：`serialize_conversation` 把消息投影成 `[Role]: ...` 纯文本，工具结果按 `tool_result_max_chars` 截断，防止摘要请求本身爆 token。⚠️ `convert_to_llm` 目前无调用点（接入层后来改用 `content_text` 直接投影），属未使用的工具函数；`_content_text` 与 `session_tree/messages.py` 的 `content_text` 功能重复。

**`summarize.py` / `usage.py`**：`complete_summarization` 的路由隔离（新 isolation id）+ 重试 + 协作式取消封装干净；`langchain_summarizer` 适配器把 `usage_metadata` 标准化为存储层 camelCase。👍

**`events.py`**：四类钩子（`before_compact` / `after_compact` / `before_branch_summary` / `after_branch_summary`）以可调用对象 + 轻量 dataclass 表达，扩展可取消或接管摘要，符合文档 §10。👍

### 3.4 接入层 `app/services/session_tree.py` + `runner.py`

`get_or_create_tree_session` 用 `chat:{id}` 作 `session_key` 绑定树会话；`mirror_user_message` / `mirror_assistant_message` 镜像消息；`compact_if_needed` 触发压缩。`runner.py` 在用户/助手消息落库后镜像、每轮末尾 `await asyncio.to_thread(...)` 触发压缩（本次审计已把同步 LLM 调用移出事件循环），全部 fail-safe（失败仅记日志）。👍

⚠️ 两个真实缺口（详见 §6）：
- **压缩摘要尚未真正进入 Agent 输入**：Agent 仍走 LangGraph checkpointer 的历史，`build_context_messages` 的产出未被消费，压缩目前是「存了但没喂回去」。
- **镜像消息不带 `usage`**：导致 `estimate_context_tokens` 在生产里始终走启发式兜底，双路径只用了后半段。

---

## 4. 正确性与健壮性

| 维度 | 评价 |
|------|------|
| append-only 与不变式 | 强。存储层分配关键字段 + `apply_mutation` 校验，树结构在任何时刻都合法 |
| 环检测 | 强。`walk_to_root` 对循环父链明确报错 |
| 崩溃一致性 | 强。SQLite 事务 + WAL，先持久化后应用内存 |
| token 估算 | 逻辑正确（双路径），但生产未喂 usage，实际只有启发式在跑 |
| 切割点算法 | 正确，已通过脚本验证非 split / split 两种边界 |
| 迭代式压缩 | 正确。虚拟条目 + `UPDATE_SUMMARIZATION_PROMPT` 保证旧信息不丢 |
| 上下文重建 | 正确。压缩后仅保留最后一个 compaction 条目 + retained_tail |
| 文件操作跟踪 | 逻辑正确（read/edited/written 三集合、modified 去重），但键名风格不统一 |
| 并发/取消 | 编排层有 `is_aborted` 协作式取消；接入层 fail-safe 不拖垮主流程 |
| 异常隔离 | 强。摘要请求与主对话隔离（独立 isolation id），接入层异常不影响 Agent |

---

## 5. 优点总结

1. **分层纯函数**：切割点 / 预算 / 估算无副作用，便于测试与复用。
2. **双路径 token 估算**：真实 usage 优先、启发式兜底，错误场景下压缩仍可用。
3. **迭代式摘要**：`UPDATE_SUMMARIZATION_PROMPT` 把新消息并入旧摘要，而非每次从零总结。
4. **append-only 树 + 指针**：分支 / 导航 / 压缩都是追加，历史永不改写，天然支持崩溃恢复。
5. **可扩展可观测**：钩子可接管摘要；usage 计入 `Entry.usage`，成本透明。
6. **接入层 fail-safe**：镜像/压缩失败只记日志，不中断 Agent 主流程。
7. **配置外置**：`enabled` / `reserve_tokens` / `keep_recent_tokens` 等通过 `.env` 配置。

---

## 6. 问题与风险

按影响分级。

### 🔴 严重（影响功能目标达成）

1. **压缩摘要未进入 Agent 上下文**
   - 现状：Agent 每轮的上下文仍来自 LangGraph checkpointer，`build_context_messages` 产出无人消费，压缩只写入树、不参与实际推理。
   - 影响：上下文超限后，Agent 仍会带着全量历史请求，压缩没有起到「释放上下文」的作用，成本/截断问题依然存在。
   - 建议：在 `_init_state` 用树上下文（压缩后）作为 `history_messages` 注入，或改造 checkpointer 的历史来源。

2. **会话树缺少 SQLite 存储的测试覆盖**
   - 现状：`tests/test_session_tree.py`（含 `test_conformance_sqlite`、`test_sqlite_persistence_roundtrip`）已不存在；当前测试只经 `InMemorySessionRepo` 间接覆盖，`SqliteSessionStorage` / `SqliteSessionRepo` 零覆盖。
   - 影响：持久化、重放、fork 等关键路径无回归保护。

### 🟡 一般（不一致 / 功能未用）

3. **镜像消息不带 `usage`**：`mirror_assistant_message` 未传 usage，树中消息无 `totalTokens`，`estimate_context_tokens` 只能启发式估算。应在 runner 落库时把 `input_tokens`/`output_tokens` 一并镜像。

4. **`Record`（车道操作日志）完全未接入**：存储层实现了 `append_record`、`find_open_operations`、`SessionStats` 累计，但接入层从不写 record，崩溃恢复 / 用量审计这一整块能力闲置。

5. **`resumer.py` 未接入**：审批恢复流程落库助手回复时不镜像到树，与主流程不一致，导致含审批的会话树不完整。

6. **键名风格不一致**：`compute_file_lists` 返回 snake_case，`details` 读写用 camelCase，需手动转换。

### 🟢 轻微（代码卫生）

7. `CompactionEngine.compact()` 的 `context_window` 参数未使用。
8. `convert_to_llm` 无调用点（未使用的工具函数），`_content_text` 与 `messages.content_text` 重复。
9. `get_or_create_tree_session` 用 `repo.list()` 全量扫描查找已存在会话（O(n)），会话量大时应改为按 `session_key` 直查。
10. 文档陈旧：`session_tree/__init__.py` 与 `docs/session-tree-storage.md` 引用了不存在的 `testing.py` / `testing/`。

---

## 7. 测试覆盖评价

| 测试文件 | 覆盖范围 | 状态 |
|----------|----------|------|
| `tests/test_compaction.py` | 序列化/截断、usage 合并、触发判定、压缩（非 split/split/迭代）、文件操作、分支摘要、钩子、重试/取消 | ✅ 23 例 |
| `tests/test_session_tree_service.py` | 镜像、上下文读取、压缩触发/跳过 | ✅ 4 例 |
| `tests/test_session_tree.py` | 会话树 conformance（内存/SQLite） | ❌ 已缺失 |

**结论**：编排层（`app/compaction`）覆盖较好；存储层（`app/session_tree`）尤其 SQLite 路径几乎无直接覆盖。建议优先补回 `test_session_tree.py`（或新增针对 `SqliteSessionStorage` 的持久化/重放/fork/close 测试）。

---

## 8. 改进建议（按优先级）

1. **接通压缩到 Agent 上下文**：让压缩真正影响推理，否则整个压缩链路是「半成品」。
2. **补 SQLite 存储测试**：恢复 conformance 测试，覆盖重放、fork、`close()`。
3. **镜像时带上 usage**：让双路径 token 估算在生产真正生效。
4. **统一文件操作键名**：`compute_file_lists` 直接返回 camelCase，或在纯逻辑层统一 snake_case 并集中转换。
5. **接入 `Record` 与 `resumer.py`**：补齐操作日志写入与审批恢复流程的镜像，形成完整闭环。
6. **清理卫生项**：删除未使用的 `convert_to_llm`、去重 `_content_text`、给 `compact()` 加注或移除冗余参数、优化 `get_or_create_tree_session` 查找、修正过时文档。
