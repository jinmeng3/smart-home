# 第八届中国研究生人工智能创新大赛

## Orion Edge Smart Home —— 基于 1B 小模型与边缘部署的可审计长对话智能家居智能体

## 项目文档

V1.0

2026.08

**项目名称**：Orion Edge Smart Home　|　**版本**：V1.0　|　**日期**：2026.08　|　**团队名称**：[团队名称]　|　**参赛组别**：[参赛组别]

> **一句话核心叙事**：用「1B 小模型 + Jetson 边缘设备」跑起一个**安全、可长期对话、可审计**的智能家居智能体。
> 小模型意味着推理弱、上下文短、显存紧——而本项目系统化落地的「上下文压缩 + 会话树形存储 + 风险分级审批 + 大模型驱动的场景编排」恰好是这四个短板的解药，因此**这套基础设施在边缘场景下的价值被显著放大**，构成真正的差异化亮点。

---

## 目录

1 [项目概况](#1-项目概况)
1.1 [背景和基础](#11-背景和基础)
1.2 [场景和价值](#12-场景和价值)
1.3 [所需支持](#13-所需支持)

2 [项目规划](#2-项目规划)
2.1 [整体目标](#21-整体目标)
2.2 [技术创新点](#22-技术创新点)

3 [实施方案](#3-实施方案)
3.1 [技术可行性分析](#31-技术可行性分析)
3.2 [技术细节](#32-技术细节)
3.3 [计划和分工](#33-计划和分工)

4 [参考资料](#4-参考资料)

---

## 记录更改历史

| 序号 | 更改原因 | 版本 | 作者 | 更改日期 | 备注 |
| ---- | -------- | ---- | ---- | -------- | ---- |
| 1 | 首次提交 | V1.0 | [作者] | 2026.08 | 初稿 |
|   |          |      |      |          |      |
|   |          |      |      |          |      |

---

## 1 项目概况

### 1.1 背景和基础

#### 1.1.1 痛点：传统方案在「智能 + 隐私 + 可控」三角中难以兼得

智能家居在过去十年完成了从「遥控 App」到「语音助手 + 场景联动」的演进，但当前面向 C 端家庭的主流方案仍存在以下结构性问题：

1. **App / 表单式规则引擎门槛高**：典型智能家居 App 需要用户在 4–5 层菜单里寻找「回家模式」「睡眠模式」按钮；更复杂的「每周五 18:30 后若客厅有人就开氛围灯」自动化规则，往往要求用户手动配置触发器 + 条件 + 动作 + 冷却 + 优先级——绝大多数家庭用户难以独立完成。
2. **云端大模型方案存在三大顾虑**：
   - **数据隐私**：家庭摄像头、门锁、行为习惯等数据持续上云，长期存在被滥用或泄漏的风险；
   - **断网不可用**：智能家居对网络稳定性的容忍度极低（开门、开灯不能等几十秒重连），云端方案在弱网/断网场景下迅速退化为「哑设备」；
   - **长期 API 成本**：按 token 计费的大模型推理，对「每天与家居对话几十次」的家庭用户而言是显性、长期的财务支出。
3. **大模型能力与小型化路线的失衡**：云端 GPT/Claude 级别模型能解析复杂指令并规划多步操作，但其对家庭场景的部署并不友好；与之相对，1B 级小模型（MiniCPM、Phi-3.5-mini、Qwen-1.5B 等）已能在边缘设备（Jetson Orin Nano、Orin NX、Raspberry Pi 5 + 加速棒）上以可接受延迟运行，但需要补齐「上下文短」「推理弱」「易幻觉」三项配套基础设施才能成为合格的家庭智能体。

#### 1.1.2 机遇：1B 小模型 + Jetson 边缘 + 配套基础设施 = 「真本地智能体」窗口期

2024–2026 年是边缘端小型语言模型（SLM on device）从「技术演示」走向「产品可用」的关键节点：

- **模型侧**：MiniCPM 2/3/4 系列、Phi-3.5-mini、Qwen2.5-1.5B、Llama-3.2-1B 等 1B–3B 模型在指令理解、工具调用（function calling）、结构化输出（JSON）能力上已能满足「智能家居任务规划」需求。
- **硬件侧**：NVIDIA Jetson Orin Nano 8GB / Orin NX 16GB 等边缘设备内置 8–16GB 共享显存，配合 CUDA + TensorRT，可承载 1B 模型 INT4 量化（约 0.5–1GB 权重）+ KV cache 推理。
- **推理引擎侧**：llama.cpp（CUDA 后端）、vLLM（已支持 Jetson 移植）、Ollama、TensorRT-LLM 等本地推理服务都暴露了 **OpenAI 兼容的 HTTP 接口**（`/v1/chat/completions`），使得应用层切换本地/云端模型几乎「零改动」。

#### 1.1.3 切入：做「**本地边缘部署的大模型智能体**」——补齐四项配套基础设施

我们团队的切入路径是：以 **1B 小模型 + Jetson 边缘设备**为硬件基座，**系统化地补齐四项针对「小模型 + 边缘」场景的基础设施**，让小模型也能承担长期、安全的家庭智能体角色：

1. **上下文压缩**（边缘刚需）—— 让 8K–32K 上下文的小模型也能维持长对话；
2. **会话树形存储**（轻量可审计）—— 在存储/内存有限的边缘设备上实现可分支、可恢复、可审计的会话状态；
3. **风险分级与人工审批**（补偿小模型）—— 规则化风险策略 + 写操作强制人工确认，把安全兜底做在前面；
4. **大模型驱动的场景编排**（替代表单式引擎）—— 把自然语言直接转成结构化自动化规则。

#### 1.1.4 已有工作基础

本项目基于团队此前已完成的「Orion Smart Home」系统（详见仓库 `README.md`）迭代而来，已有可直接运行的原型与可量化的工程基线：

- **后端**：FastAPI + LangGraph + SQLAlchemy + SQLite + LangChain；约 30+ 业务模块，**完整可运行的单 Agent 工作流**已通过单元测试与手测；
- **会话存储与压缩**：**完整移植了开源智能体 Pi（pi-mono）的会话树形存储与上下文压缩设计**，对应本仓库 `app/session_tree/`、`app/compaction/`，配套设计文档 `docs/session-tree-storage.md`、`docs/session-tree-compaction-review.md`；
- **风险分级与审批**：基于 LangGraph 状态机实现 `risk_check → approval_interrupt → write_tool` 闭环，写操作审计链 + 写操作租约互斥（`app/agents/risk/`、`app/agents/audit/`、`app/agents/agent_service/lease.py`）；
- **前端**：Vue 3 + Vite + TypeScript + Pinia，审批卡片、SSE 流式解析、Chat UI 已就绪（`smarthome-web/src/components/chat/AgentConfirmationCard.vue`、`useHomeChat.ts`）；
- **模型接入层**：基于 `app/agents/providers/openai_compatible.py` 实现的 OpenAI 兼容适配器，可零改动切换到任意 OpenAI 兼容端点（vLLM / llama.cpp / Ollama / DeepSeek / OpenAI），**这是「无改动接入本地 Jetson 模型」的关键**；
- **设计文档**：`docs/funnel-routing-architecture.md`（漏斗式分层路由）、`docs/session-tree-compaction-review.md`（会话压缩实现评价）、`docs/sub-agent-design.md`（多 Agent 编排设计）。

#### 1.1.5 团队构成

| 方向 | 人数 | 主要职责 |
| ---- | ---- | -------- |
| 大模型 / Agent | 2 | 模型适配、Agent 工作流、压缩、风险分级、子 Agent 设计 |
| 后端工程 | 2 | FastAPI、SQLAlchemy、LangGraph、SSE 流式、数据库、鉴权、审计 |
| 前端工程 | 1 | Vue 3、TypeScript、Pinia、SSE 解析、审批 UI、Chat UI |
| 边缘部署 / 硬件 | 1 | Jetson 适配、模型量化（INT4/INT8）、推理引擎（llama.cpp / TensorRT-LLM / vLLM）、性能评测 |

---

### 1.2 场景和价值

#### 1.2.1 应用场景

Orion Edge Smart Home 面向**家庭场景**的智能体，覆盖以下典型任务：

- **日常设备控制**：自然语言指令控制灯、空调、窗帘、新风、扫地机器人等家电；支持模糊表达（"有点暗"→ 自动调亮）；
- **一键场景执行**：把多设备组合成命名场景（"回家模式""影院模式""睡眠模式"），用一句话触发；
- **自动化规则创建与管理**：自然语言生成自动化（"每周五 18:30 后若客厅有人就开氛围灯"），系统自动转成结构化规则入库；
- **状态查询与诊断**：跨设备查询（"今天家里哪些灯还开着？""这个月最费电的是哪台？"），用自然语言获得聚合答案；
- **跨域复合任务**：能拆解并执行复合意图（"看一下客厅摄像头，如果没人在家就把空调关了"），需要场景感知 + 设备控制 + 条件判断的串行/并行；
- **适老化无障碍控制**：对老人/视障用户友好——只需开口，不必操作层层菜单。

#### 1.2.2 潜在社会价值

| 价值点 | 落地表现 |
| ------ | -------- |
| **隐私保护** | 家庭对话、设备状态、自动化配置等数据全程本地处理，不上云，从根本上解决家庭数据出域顾虑 |
| **离线可用** | 断网场景下系统完全可用；这在租房、独居老人、农村/弱网地区家庭尤其重要 |
| **降低长期成本** | 一次硬件投入（Jetson Orin Nano 8GB 约 3000–5000 元）+ 一次性部署，长期零 API 费 |
| **降低使用门槛** | 把"点击 5 层菜单"和"填自动化表单"变成"说一句"，老人/儿童/视障用户均能使用 |
| **降低误操作风险** | 高风险设备（门锁、摄像头、安防、警报）写操作强制人工审批并完整审计；这是把"敢让 AI 控制门锁"做成的关键 |
| **可审计 / 可追责** | 每次写操作生成完整审计链（参数 + 审批决定 + 执行结果 + 错误码 + run_id 串联），事后可复盘 |
| **节能与普惠** | 减少无效照明/空调用电；同时让"AI 智能体"这一形态从云端奢侈品走向家庭常驻品 |

#### 1.2.3 对比分析

| 维度 | 传统 App | 表单式规则引擎 | **云端大模型方案** | **本项目（Orion Edge）** |
| ---- | -------- | -------------- | ------------------ | ------------------------ |
| 交互方式 | 多层菜单点击 | 填写触发器/条件/动作表单 | 自然语言对话 | 自然语言对话 |
| 复杂任务理解 | ❌ 不支持 | ⚠️ 需手动配置 | ✅ | ✅（LLM 规划 + 工具调用） |
| 自主决策 | ❌ | ❌ | ✅ | ✅ |
| 隐私（数据出域） | ✅ 本地 | ✅ 本地 | ❌ 上云 | ✅ **本地** |
| 离线可用 | ✅ | ✅ | ❌ 强依赖网络 | ✅ **本地** |
| 长期成本 | ✅ 零 | ✅ 零 | ❌ 按 token 计费，长期显著 | ✅ 一次性硬件 + 零运营 |
| 写操作安全 | ⚠️ 用户自己点 | ⚠️ 规则自动执行 | ⚠️ 取决于护栏 | ✅ **规则化风险分级 + 强制审批** |
| 长对话记忆 | ⚠️ 通常仅缓存最近 N 句 | — | ⚠️ 受限于云端上下文窗口 | ✅ **会话树 + 压缩**（无限历史） |
| 可审计 | ❌ 黑盒 | ⚠️ 日志 | ⚠️ 云端日志，事后不可控 | ✅ **本地审计链 + 会话树** |
| 部署门槛 | 低 | 低 | 低 | ⚠️ 需边缘硬件（一次投入） |

**核心差异**：在「**云端大模型方案**」的强项（任务理解、自主决策）上，本项目通过小模型 + 配套基础设施达到接近水平；而在「**云端大模型方案**」的弱项（隐私、离线、成本、长记忆、可审计）上，本项目具备显著优势。

---

### 1.3 所需支持

#### 1.3.1 硬件

| 类别 | 具体型号 / 参数 | 用途 | 是否可替代 |
| ---- | --------------- | ---- | ---------- |
| **边缘推理主设备** | NVIDIA Jetson Orin Nano 8GB（推荐）或 Jetson Orin NX 16GB | 承载本地 1B 模型推理（INT4 量化）与 FastAPI 后端服务 | 理论上可替换为 Raspberry Pi 5 + AI 加速棒（如 Coral TPU），但需重新评估推理延迟 |
| 主机内存 | 8GB 起步 / 16GB 推荐 | 运行后端服务、SQLite、SSE 流式 | — |
| 存储 | 64GB+ NVMe / SD | 操作系统、模型权重（~2GB）、SQLite 数据库、审计日志 | — |
| 可选 | 真实智能家居设备（智能灯、空调伴侣、门锁传感器等） | 真实场景联调（仿真器已能覆盖 80% 功能） | 否，但可分阶段接入 |
| 可选 | NVIDIA RTX 桌面 GPU | 训练 / 微调 / 量化模型；评测阶段使用 | 否，但日常使用无需 |

#### 1.3.2 模型

| 类别 | 具体型号 / 量化 | 用途 | 备注 |
| ---- | --------------- | ---- | ---- |
| **主推理模型** | MiniCPM-2.6-1B（INT4 量化，约 0.5–1GB 权重）或同级别 1B 小模型 | 对话理解、指令解析、工具调用、压缩摘要 | 需具备 function calling 能力；备选 Phi-3.5-mini-instruct、Qwen2.5-1.5B-Instruct |
| 嵌入模型 | bge-small-en-v1.5 / bge-small-zh-v1.5（可选） | 自动化冲突检测、相似指令检索 | 可选，纯本地推理 |

#### 1.3.3 数据 / 知识

- **设备状态与执行结果**：由内置模拟器（`app/services/device.py`）生成，结构自定义、规模可控；
- **风险策略库**：内置 4 级风险（read_only / low / high / unknown）+ 高风险设备类型表（门锁 / 摄像头 / 安防 / 警报），无需大规模训练数据；
- **场景模式与设备类型**：智能家居行业公开常识，已整理到系统提示词（`app/agents/prompts.py`）中。

#### 1.3.4 其他支持

- **边缘推理优化培训**：TensorRT / llama.cpp / vLLM-on-Jetson 部署与调优文档；
- **真实设备接入支持**：智能家居生态（米家、Aqara、Apple Home、Matter）协议适配；
- **评测与压测工具**：长对话压测脚本、并发审批压测、离线运行验证。

---

## 2 项目规划

### 2.1 整体目标

#### 2.1.1 交付目标（可衡量）

| 维度 | 目标 | 验证方式 |
| ---- | ---- | -------- |
| **边缘可运行原型** | 在 Jetson Orin Nano 8GB 上本地运行 1B 小模型（INT4 量化），完成自然语言控制设备 / 场景 / 自动化、多轮对话、风险审批、SSE 流式输出、长对话压缩全流程 | 现场演示 + 实测指标 |
| **长对话维持** | 持续对话 ≥ 200 轮不出现「上下文溢出/截断/历史丢失」 | 自动化压测脚本（`tests/test_session_tree_service.py` + 自研长对话脚本） |
| **指令解析准确率** | 简单控制指令 ≥ 95%；复合意图 ≥ 80% | 内部测试集（≥ 100 条样本） |
| **写操作安全** | 高风险写操作误执行率 = 0；所有写操作留有完整审计链 | 自动化用例 + 审计文件人工抽检 |
| **离线可用** | 断开外网后系统全部功能（控制、对话、审批、压缩、审计）正常 | 物理断网测试 |
| **并发安全** | 同一会话并发请求不串写 checkpoint / 审批状态 | 压测脚本（`tests/test_compaction.py`） |
| **边缘推理指标** | 首次 token 延迟 < 1.5s；持续生成 ≥ 8 tokens/s；显存峰值 < 4GB | Jetson 实测（`scripts/bench_edge.py`） |

#### 2.1.2 验证目标

- 在模拟器 + 至少 2 类真实设备上完成功能与安全评测；
- 产出 **《边缘推理性能与安全性评测报告》**，包含延迟、显存、吞吐、误执行率、长对话维持时间、并发安全 6 项核心指标；
- 形成 1 篇技术报告（本文档）+ 1 套开源代码 + 1 份评测报告 + 1 段 5–8 分钟演示视频。

---

### 2.2 技术创新点

> **整体定位**：本项目不是「又一个 ChatGPT 控制家居」项目，而是**为「小模型 + 边缘设备」这一新部署形态系统化补齐四项配套基础设施**。每项创新都直面「小模型 / 边缘场景下的具体短板」，并已在代码层实现完整闭环。
>
> **展示约定**：每个创新点按 **「背景与痛点 → 完整技术细节（代码证据）→ 展示过程（一步步画面描述）→ 与现有方案差异」** 四步法展开。

---

#### 创新点 1：上下文压缩 —— 边缘刚需，让 1B 模型「带着记忆」工作

##### ① 背景与痛点

**为什么是边缘刚需**：
1B 小模型的上下文窗口通常为 **8K–32K tokens**（如 MiniCPM-2.6-1B 默认 4K，可扩到 32K），相对 128K–200K 级别的云端模型，**压缩从「锦上添花」变成「能不能用长对话」的关键**。在 32K 窗口下，一次中等规模的家务对话（40 轮 + 10 次工具调用）就可能逼近上限；不压缩，几小时后模型就开始「忘记早晨说过的话」。

云端大模型方案对压缩的需求弱（窗口足够大、推理便宜），所以 LangChain / LlamaIndex 等的压缩实现多以「单路径 + 单次摘要」为主，不适合边缘。

##### ② 完整技术细节

**总体架构（4 层）**：

```
┌────────────────────────────────────────────────────┐
│  编排层  app/compaction/                            │
│  - CompactionEngine.evaluate / compact / summarize  │
│  - prompts (4 种)  serialize  summarize  events    │
├────────────────────────────────────────────────────┤
│  纯逻辑层  app/session_tree/compaction/             │
│  - find_cut_point / prepare_compaction             │
│  - estimate_context_tokens / extract_file_ops      │
│  - collect_entries_for_branch_summary              │
├────────────────────────────────────────────────────┤
│  存储层  app/session_tree/session/                  │
│  - Entry / Record / Fact + 6+1 不变式 + WAL        │
├────────────────────────────────────────────────────┤
│  接入层  app/services/session_tree.py              │
│  - mirror_user/assistant_message                   │
│  - build_context_messages  compact_if_needed      │
└────────────────────────────────────────────────────┘
```

**关键 1：触发判定**（`app/compaction/engine.py`）：

```python
def evaluate(self, session, *, context_window, settings=None, last_assistant_message=None, lane="main"):
    if not settings.enabled:                                return decision("disabled", 0)
    if path and path[-1].type == "compaction":             return decision("already_compacted", 0)
    if not messages:                                        return decision("nothing_to_compact", 0)
    if last_assistant_message and last_assistant_message.get("stopReason") == "aborted":
                                                              return decision("aborted", 0)
    tokens = estimate_context_tokens(messages)["tokens"]
    if should_compact(tokens, context_window, settings):    return decision("threshold", tokens)
    return decision("ok", tokens)
```

**触发来源**有三种：
- `reason="threshold"`：每轮 Agent 推理结束后（`runner._maybe_compact_tree`）触发 token 估算；
- `reason="overflow"`：模型返回 `stopReason="length"` 时由调用方触发，**压缩后自动重试一次**（`will_retry=True`）；
- `reason="manual"`：用户输入 `/compact` 命令触发。

**跳过规则**保证：已压缩过 / 消息被中止 / 无内容 / 压缩未启用 → 不重复压缩。

**关键 2：双路径 token 估算**（`app/session_tree/compaction/compaction.py`）：

```python
def estimate_context_tokens(messages: list[Message]) -> dict[str, Any]:
    # 路径 1：真实 usage
    usage_info = None
    for i in range(len(messages) - 1, -1, -1):
        usage = _get_assistant_usage(messages[i])     # 跳过 stopReason in (aborted, error)
        if usage is not None:
            usage_info = {"usage": usage, "index": i}; break

    if usage_info is None:
        # 路径 2：启发式（chars/4）
        estimated = sum(estimate_tokens(message) for message in messages)
        return {"tokens": estimated, "usage_tokens": 0, "trailing_tokens": estimated, ...}

    usage_tokens = calculate_context_tokens(usage_info["usage"])   # totalTokens || input+output+cacheRead+cacheWrite
    trailing_tokens = sum(estimate_tokens(messages[i]) for i in range(usage_info["index"] + 1, len(messages)))
    return {"tokens": usage_tokens + trailing_tokens, ...}
```

**为什么对边缘重要**：本地 1B 推理偶发返回异常 usage（量化模型的 token 统计偏差）；单路径方案会「卡死」压缩，**双路径让「即使 usage 全错也能压缩」**。

**关键 3：切割点算法**（`find_cut_point`）：

```python
def _find_valid_cut_points(entries, start_index, end_index) -> list[int]:
    cut_points = []
    for i in range(start_index, end_index):
        entry = entries[i]
        if entry.type == "message":
            role = (entry.message or {}).get("role")
            # 关键：toolResult 永远不在合法切点上
            if role in ("bashExecution", "custom", "branchSummary", "compactionSummary", "user", "assistant"):
                cut_points.append(i)
        if entry.type == "branch_summary":
            cut_points.append(i)
    return cut_points
```

**核心不变量**：**`toolResult` 永远不能作为切割点**——避免把工具结果切断丢失上下文；只能切在 `user` / `assistant` / `bashExecution` / `custom` / `branchSummary` / `compactionSummary` 这 6 种角色上。

**算法步骤**：
1. 从 `end_index-1` 向 `start_index` 累积 token；
2. 当累积 ≥ `keep_recent_tokens` 时，**回退**找到该位置之后的第一个合法 cut_point（保证保留尾巴够长）；
3. 若 cut point 是 user 消息 → `turn_start_index = -1`（不需要 split）；
4. 若 cut point 是 assistant / toolCall / bashExecution → 向前找 user / branchSummary 起始点，构成 **split turn**：history 末尾 + turn 前缀 + 当前轮继续。

**关键 4：迭代式摘要**（`app/compaction/prompts.py`）：

```python
UPDATE_SUMMARIZATION_PROMPT = """You are updating an existing session summary by merging newer conversation turns into it.

Requirements:
- Preserve ALL information already in the previous summary unless it has been superseded or is obsolete.
- Move completed "In Progress" items to "Done".
- Update "Next Steps" to reflect the current state.
- Remove information that is no longer relevant.
- Preserve exact file paths, function/class names, identifiers, commands, and error messages verbatim.
- Output ONLY the merged structured summary, nothing else.

Format:
## Goal / ## Constraints & Preferences / ## Progress / ## Key Decisions / ## Next Steps / ## Critical Context
"""
```

**配合虚拟条目**（`prepare_compaction`）：把上次压缩的 `retained_tail` 重新映射为虚拟 message entry，纳入下次切割点计算——**实现「压缩后的消息也算历史」**。

**关键 5：分支摘要**（`app/session_tree/compaction/branch_summary.py`）：

```python
def collect_entries_for_branch_summary(session, old_leaf_id, target_id):
    """计算旧 leaf 与目标节点的公共祖先，收集被抛弃分支上的条目。"""
    old_path = {entry.id for entry in session.find_entries_on_branch(EntryQuery(start=old_leaf_id))}
    target_path = session.find_entries_on_branch(EntryQuery(start=target_id))
    common_ancestor_id = next((e.id for e in target_path if e.id in old_path), None)

    entries = []
    current = old_leaf_id
    while current and current != common_ancestor_id:
        entry = session.get_entry(current)
        entries.append(entry); current = entry.parent_id
    entries.reverse()
    return CollectEntriesResult(entries=entries, common_ancestor_id=common_ancestor_id)
```

**关键 6：文件操作跟踪**（`extract_file_ops_from_message`）：

```python
def extract_file_ops_from_message(message, file_ops):
    if message.get("role") != "assistant": return
    for block in message.get("content", []):
        if block.get("type") != "toolCall": continue
        name, args = block.get("name"), block.get("arguments")
        path = args.get("path") if isinstance(args, dict) else None
        if not isinstance(path, str) or not path: continue
        if name == "read":   file_ops.read.add(path)
        elif name == "write":  file_ops.written.add(path)
        elif name == "edit":   file_ops.edited.add(path)
```

**累积语义**：从上次压缩的 `details.readFiles` / `details.modifiedFiles` 取历史集合，叠加本次新增，**跨多次压缩不丢**；作为 `<read-files>` / `<modified-files>` XML 块注入摘要。

**关键 7：路由隔离 + 协作式取消**（`complete_summarization`）：

```python
def complete_summarization(summarizer, system, user, *, max_tokens=None, retry_attempts=0, isolation_id=None, is_aborted=None):
    isolation_id = isolation_id or uuid4().hex   # 每次摘要一个新隔离 id
    while True:
        if is_aborted is not None and is_aborted(): raise SummarizationAborted()
        try:
            return summarizer(system, user, max_tokens=max_tokens, isolation_id=isolation_id)
        except SummarizationAborted: raise
        except Exception:
            if attempts >= retry_attempts: raise
            attempts += 1
```

**关键 8：摘要回注 Agent**（`app/services/session_tree.py`）：

```python
def _maybe_compact_tree(context: AgentContext, model_config: AIModel) -> None:
    try:
        settings = get_settings()
        if not settings.compaction_enabled: return
        context_window = model_config.context_window or settings.session_tree_context_window
        model = get_model_cache().get(model_config)
        summarizer = langchain_summarizer(model)
        compact_if_needed(context.session_id, summarizer=summarizer, context_window=context_window)
    except Exception:
        logger.warning("上下文压缩失败，已忽略", exc_info=True)

async def _load_tree_history(session_id, thread_id):
    history = build_context_messages(session_id)        # 摘要 + retained_tail
    saver = await get_checkpointer()
    await saver.adelete_thread(thread_id)              # 清空 checkpointer 旧历史
    return history
```

**关键差异**：常见做法只把摘要「存起来」，下一轮 Agent 仍走 LangGraph checkpointer 全量历史；本项目**摘要真正回注到下一轮输入**，并清空 checkpointer 旧历史。

##### ③ 展示过程（一步步画面描述）

| # | 演示画面 | 关键证据 / 数值 |
| - | -------- | --------------- |
| 1 | **演示前 0 分钟**：在 Jetson Orin Nano 上启动后端（`uvicorn app.main:app`），启动 `ollama serve` + `ollama pull minicpm-1b:int4`；登录前端；左下角「模型」显示「minicpm-1b (本地边缘 · INT4)」 | 终端 `nvidia-smi` 显示显存占用 ≈ 2.3GB |
| 2 | **对话启动**：用户输入「帮我把客厅灯调成暖色 60%」→ 模型调用 `set_device_power(暖色, 60%)` → 灯亮起 | 响应时间 ≈ 1.2s |
| 3 | **长对话触发压缩**：自动测试脚本连续发 200 轮混合指令（设备控制 / 状态查询 / 场景 / 闲聊） | 压缩前 token 估算 ≈ 28K；用户「压缩」按钮可见 |
| 4 | **压缩执行**：第 153 轮时 `should_compact=True`，触发 `compact(reason="threshold")`；UI 顶部出现黄色提示条「正在压缩历史上下文…」 | 压缩耗时 ≈ 3s（摘要请求 1 次） |
| 5 | **压缩完成**：会话树新增一条 `compaction` 节点（type=compaction, summary="<结构化 6 段>"），后续轮数 context 投影为「`[Compaction summary]\n{summary}` + retained_tail」 | token 估算降至 ≈ 9K（节省 68%） |
| 6 | **继续对话不丢记忆**：用户问「我今天早上让你看过哪些灯还开着？」→ 模型从摘要的「Critical Context」节中准确答出「客厅吊灯、厨房筒灯」 | 答案正确（验证摘要保真度） |
| 7 | **分支摘要演示**：用户用 `/tree` 切到上午的一个分支「试试回家模式 A」对话 5 轮 → 切回主线 → 提示「已对抛弃分支生成分支摘要」 | 会话树新增 `branchSummary` 节点 |
| 8 | **文件操作跟踪演示**：在自动化任务中连续 5 次 `read / edit / write` 文件 → 压缩后摘要末尾的 `<read-files>` / `<modified-files>` 列出全部路径 | 验证累积机制 |
| 9 | **中断重试演示**：在压缩进行中点击「取消」→ `is_aborted=True` → 下一轮 LLM 请求前抛 `SummarizationAborted` | UI 立即回退，无残留节点 |
| 10 | **极端长对话**：压测脚本跑到 500 轮 → 系统中压缩 ≥ 8 次；查询「一周前我说过什么」→ 答案正确（迭代式摘要的累积结果） | 验证「1B 模型也能维持超长记忆」 |

**演示重点**：「压缩不是只存起来——摘要真的进入了下一轮模型输入，并且通过迭代式 + 双路径 + split turn + 分支 + 文件跟踪 5 项机制，让 8K–32K 窗口的 1B 模型也能维持数百轮长对话」。

##### ④ 与现有方案差异

| 维度 | 常见方案（LangChain / LlamaIndex / MemGPT） | 本项目 |
| ---- | ------------------------------------------- | ------ |
| 目标窗口 | 100K+（云端） | 8K–32K（边缘 1B 模型） |
| token 估算 | 单路径（真实 usage） | **双路径**（真实 usage 优先 + chars/4 兜底） |
| 切割粒度 | 消息级 | **6 种合法 cut point + split turn + toolResult 禁切** |
| 多次压缩语义 | 每次从零总结 | **迭代式 + 虚拟条目**（旧信息不丢） |
| 分支切换 | 不支持 / 需自实现 | **原生**（公共祖先 + 分支摘要自动注入） |
| 文件操作 | 不跟踪 | **跨次压缩累积 read/edited/written 集合** |
| 摘要回注 | 部分支持 | **真回注 + 清空 checkpointer 旧历史** |
| 取消 | 一般支持 | **协作式 is_aborted + 路由隔离** |
| 边缘可运行 | 依赖云端 | **完整本地 + 量化友好** |

---

#### 创新点 2：会话树形存储 —— 轻量可审计，边缘设备上的可分支可恢复

##### ① 背景与痛点

**为什么是边缘刚需**：
边缘设备存储 / 内存有限（相比云端数据库集群），无法承受「传统线性消息列表 + 全文索引」式的存储开销；又因为**长对话需要持续运行数天 / 数周**，崩溃 / 断电 / 升级过程中的数据丢失是真实痛点。同时，家庭场景对「事后能复盘上次 AI 干了什么」的可审计性要求高。

云端方案的 LangGraph SqliteSaver、MemGPT 等虽然成熟，但**线性 checkpoint** 难以支撑「回看 3 天前那次误操作怎么发生的」「试试当时如果选另一条路会怎样」这类家庭场景典型需求。

##### ② 完整技术细节

**三类数据统一模型**（`app/session_tree/session/types.py`）：

| 类型 | 数量 | 用途 | 关键字段 |
| ---- | ---- | ---- | -------- |
| **Entry** | 7 种 | 会话内容树节点 | `id` / `parent_id` / `seq` / `message` / `summary` / `retained_tail` / `tokens_before` / `details` / `usage` / `from_id` … |
| **Record** | 9 种 | 车道操作日志 | `lane` / `run_id` / `operation_started` / `operation_finished` / `step_attempt` / `tool_started` / `queue_enqueued` / `write_deferred` / `usage` |
| **Fact** | 2 种 | 全局事实 | `name`（会话名） / `label`（条目标签） |
| **Lane** | 多个 | 树上的指针 | `lane_name` / `leaf_id` |

**三者共享同一个全局单调递增 `seq` 序列号**，使得任意时刻能从 `seq` 重放、合并、回放。

**Entry 七种类型语义**：

```python
EntryType = Literal[
    "message",              # 普通消息（user / assistant / toolResult / custom / bashExecution / branchSummary / compactionSummary）
    "model_change",         # 用户切换模型（provider + model_id）
    "thinking_level_change",# 切换思考等级
    "active_tools_change",  # 启用 / 停用工具
    "compaction",           # 压缩摘要节点（summary + retained_tail + tokens_before + details + usage）
    "branch_summary",       # 分支摘要节点（from_id + summary + details + usage）
    "custom",               # 自定义类型（subagent 审计节点等，build_context_messages 会跳过）
]
```

**Record 九种类型语义**：

```python
RecordType = Literal[
    "operation_started",    # 操作启动（source_leaf_id + intent）
    "abort_requested",      # 中止请求
    "operation_finished",   # 操作完成（outcome + error）
    "step_attempt",         # 步骤重试（run_id + step + attempt + result_entry_id + compaction_reason）
    "tool_started",         # 工具执行开始（assistant_entry_id + tool_index + tool_call_id + tool_name + effective_args）
    "queue_enqueued",       # 队列入队
    "queue_cancelled",      # 队列取消
    "write_deferred",       # 写操作延迟
    "usage",                # 用量（usage + cause + run_id + entry_id + stop_reason + tool_call_id + details）
]
```

**6+1 条不变式**（`SessionState.apply_mutation`）：

```python
# 1. seq 连续：seq == self._sequence + 1
# 2. id 唯一：entry.id in self._used_ids → fail
# 3. 写入 lane 必须存在
# 4. entry.parent_id 必须链到该 lane 的 leaf
# 5. entry.parent_id 必须存在（除非根节点）
# 6. record.lane 必须存在
# 7. (fact='label' 时) target_id 必须存在
```

**环检测**：`walk_to_root` 用 `visited` 集合防止手改过的坏数据导致死循环。

**Append-only + 存储层分配关键字段**：

```python
def append_entry(self, entry: Entry, lane: str) -> Entry:
    parent_id = self._state.require_lane(lane)
    self._state.validate_unused_id(entry.id)
    entry.parent_id = parent_id        # 存储层分配
    entry.seq = self._state.next_sequence  # 存储层分配
    entry.timestamp = now_ms()         # 存储层分配
    self._state.apply_mutation({"kind": "entry", "lane": lane, "entry": entry})
    return copy.deepcopy(entry)
```

**关键不变量**：`parent_id` / `seq` / `timestamp` **由存储层分配**，杜绝写入方伪造父链或序号。

**持久化（SQLite WAL）**（`app/session_tree/session/sqlite.py`）：

- **三表设计**：`session_tree_sessions` / `session_tree_entries` / `session_tree_records`；
- **写入路径**：「先持久化、后应用内存」+ 事务 + WAL，**等价于 JSONL 的 torn-tail 修复**；
- **加载与重放**：按 `seq` 升序回放所有 mutation，重新构建 `SessionState`；
- **原子发布（fork）**：整段 fork mutation 在单事务内提交。

**车道（Lane）与分支（Fork）**：

```python
def create_lane(self, lane: str, at: str | None) -> None: ...   # 在 entry 处创建车道
def move_lane(self, lane: str, to: str | None) -> None: ...     # 移动车道指针
def fork(self, metadata: SessionMetadata, options: ForkOptions) -> InMemorySessionStorage:
    storage = InMemorySessionStorage(metadata)
    for mutation in self._state.create_fork_mutations(options):  # 复制条目 + 重编 seq
        storage._state.apply_mutation(mutation)
    return storage
```

**create_fork_mutations 语义**：复制条目时重编 seq、保留 name/labels、**不复制 record**（record 属运行时操作日志，不是会话内容）。

**上下文投影**（`app/session_tree/session/context.py` + `app/services/session_tree.py`）：

```python
def default_context_entry_transform(entries: list[Entry]) -> list[Entry]:
    """只保留路径上最后一个 compaction 节点 + 其后所有 entry。"""
    last_compaction_index = max(
        (i for i, e in enumerate(entries) if e.type == "compaction"), default=-1
    )
    return entries[last_compaction_index:]   # 之后包含 retained_tail

def build_context_messages(chat_session_id: int) -> list:
    """把会话树的（压缩后）上下文投影为 LangChain 消息列表。"""
    path = session.find_entries_on_branch(EntryQuery(start=session.get_leaf_id(), order="oldestFirst"))
    context = build_session_context(path)        # Entry → Message（compaction 投影为 summary + retained_tail）
    messages = []
    for message in context["messages"]:
        role = message.get("role")
        if role == "assistant": messages.append(AIMessage(content=content_text(...)))
        elif role == "user":    messages.append(HumanMessage(content=content_text(...)))
        elif role == "compactionSummary": messages.append(HumanMessage(f"[Compaction summary]\n{summary}"))
        elif role == "branchSummary":   messages.append(HumanMessage(f"[Branch summary]\n{summary}"))
        # toolResult / bashExecution / custom → 跳过
    return messages
```

**关键设计**：`compactionSummary` 注入为「带标签的人类消息」，让模型明确知道「这是历史摘要，不是新指令」——**避免摘要被当成新指令执行**。

**接入层 fail-safe**（`app/services/session_tree.py`）：

```python
def _append_message(chat_session_id, message):
    session = get_or_create_tree_session(chat_session_id)
    try: return session.append_message(message)
    finally: session.close()                    # 每个操作独立关闭 ORM 连接

def mirror_user_message(chat_session_id, text) -> str: return _append_message(chat_session_id, _user_message(text))
def mirror_assistant_message(chat_session_id, text, *, usage=None) -> str: return _append_message(chat_session_id, _assistant_message(text, usage))
```

##### ③ 展示过程（一步步画面描述）

| # | 演示画面 | 关键证据 / 数值 |
| - | -------- | --------------- |
| 1 | **空树初始化**：新建一个 chat session → 树中只有 1 个 `lane=main` 指针（leaf_id=None） | 树深度 0；seq=0 |
| 2 | **首次对话**：用户发"你好" → `mirror_user_message` → 树中追加 1 个 `type=message, role=user` entry | 树深度 1；seq=1 |
| 3 | **助手回复**：模型答"你好" → `mirror_assistant_message` 携带 `usage` → 树中追加 1 个 `type=message, role=assistant, usage={input,output,totalTokens}` | 树深度 2；seq=2；双路径 token 估算可用 |
| 4 | **分支演示**：在第 5 轮用户用 `/tree fork at-entry-3` 创建分支 `experiment` → 车道指针从 main 切到新分支 → 在分支上对话 8 轮 | 树结构可视化：main 与 experiment 在 entry-3 处分叉；seq 继续递增 |
| 5 | **切回主线**：用户用 `/tree main` 切回 → 触发**分支摘要**：`collect_entries_for_branch_summary(experiment_leaf, main_leaf)` → 找出公共祖先 entry-3 → 收集被抛弃的 8 条 entry → 压缩为 1 条 `type=branch_summary, from_id=experiment_leaf_id` 注入到 main | main 树 +1 条 `branchSummary` 节点；experiment 树完整保留 |
| 6 | **压缩演示**：在主线长对话到 200 轮 → 触发压缩 → 树中追加 1 条 `type=compaction, summary="<结构化 6 段>", retained_tail=[…最后 5 条…], tokens_before=28000, details={readFiles, modifiedFiles}` | 树节点数：200 → 196（合并 + 摘要） |
| 7 | **崩溃恢复演示**：在第 100 轮时**人为 kill -9** 后端进程 → 重启后端 → `SqliteSessionStorage._load` 按 `seq` 重放 100 条 mutation → 重建 `SessionState` | 重启后用户问「刚才我们聊到哪了」→ 答案正确 |
| 8 | **不变式校验演示**：手动 SQL 把某条 entry 的 `parent_id` 改成不存在的 id → 重启后端 → 加载时报 `SessionError("invalid_entry")`，明确指出错误位置 | 不死循环 / 不静默吞错 |
| 9 | **审计演示**：在第 50 轮触发门锁开锁 → 树中除 message entry 外，还追加多条 `type=record, type='operation_started'/'tool_started'/'usage'/'operation_finished'` | 用 `find_records(query=RecordQuery(lane='main', run_id='run-xxx'))` 可拉出整个 run 的操作链 |
| 10 | **容量演示**：连续 30 天模拟每天 100 轮对话 → 数据库大小仅 ≈ 12MB（每条 entry 平均 200B 紧凑 JSON） | 验证「轻量、适合边缘」 |

**演示重点**：「树不只是一棵持久化的消息列表——它是可分支、可回滚、可审计、可压缩的『会话操作系统』，而边缘设备上 12MB/30天 的存储成本可承受」。

##### ④ 与现有方案差异

| 维度 | LangGraph SqliteSaver | MemGPT | 本项目 |
| ---- | -------------------- | ------ | ------ |
| 数据结构 | 线性 checkpoint | 分层（main + external + archival） | **append-only 树 + 车道 + 操作日志** |
| 分支 | 不支持 | 不支持 | **原生 fork / lane / 公共祖先导航** |
| 压缩 | 不内置 | 上下文分层 | **完整压缩链路（4 层 + 7 大机制）** |
| 操作日志 | 无 | 无 | **9 种 Record，按 lane + run_id 查询** |
| 不变式 | 无 | 无 | **6+1 条集中校验 + 环检测** |
| WAL 持久化 | 有 | 不适用 | **有（SQLite + WAL + torn-tail 修复）** |
| 接入 | LangGraph 内置 | 独立 SDK | **OpenAI 兼容，独立于模型供应商** |
| 边缘友好 | 一般 | 重 | **紧凑 JSON + 轻量 + 4 层解耦** |

---

#### 创新点 3：风险分级与人工审批 —— 补偿小模型，把安全兜底做在前面

##### ① 背景与痛点

**为什么是边缘刚需**：
1B 小模型**推理能力弱、易幻觉**——面对「帮我开一下门锁」「把摄像头关掉」这类高风险指令，模型有可能误判、误执行；又因为**完全本地、无人值守**（无云端 guardrail），必须把安全兜底做在「代码层 + UI 层」。本项目用**规则化风险分级 + 写操作强制人工确认**双保险兜底。

云端 guardrail（OpenAI Moderation、Anthropic Constitutional AI）依赖外部 API，与「完全本地」的目标相悖；本项目**把风险分级做在代码层（规则）而非模型层**——小模型再弱，也只是生成「执行什么」的工具调用，**而工具是否执行由分类器与状态机决定**。

##### ② 完整技术细节

**4 级风险分类**（`app/agents/risk/policy.py` + `classifier.py`）：

```python
class RiskLevel(StrEnum):
    READ_ONLY = "read_only"   # 只读工具，永远自动执行
    LOW = "low"               # 普通设备/灯/空调/窗帘
    HIGH = "high"             # 门锁/摄像头/安防/警报 → 永远强制审批
    UNKNOWN = "unknown"       # 设备不存在/跨家庭/未知名 → 永远强制审批

HIGH_RISK_DEVICE_TYPES = {"lock", "door_lock", "camera", "security", "alarm"}
HIGH_RISK_KEYWORDS = {"lock", "camera", "security", "alarm", "门锁", "摄像头", "安防", "警报"}

def _is_high_risk_device(device) -> bool:
    values = (device.device_id.lower(), device.name.lower(), device.type.lower())
    return device.type.lower() in HIGH_RISK_DEVICE_TYPES or any(
        keyword in value for keyword in HIGH_RISK_KEYWORDS for value in values
    )
```

**双重判定**：① device.type 是否在高风险类型表 ② device_id / name / type 是否含高风险关键词（中英双语）。

**requires_approval 决策**：

```python
requires_approval = (
    level in {RiskLevel.HIGH, RiskLevel.UNKNOWN}    # 高风险/未知永远审批
    or not context.auto_execute_low_risk            # 低风险且用户偏好为"不自动"
)
```

**关键不变量**（`policy.py` 注释）：
> 安全策略不允许绕过高风险审批。`confirm_high_risk` 仅用于前端 UI 展示，不影响后端判定。**`auto_execute_low_risk=True` 仅在「低风险」时自动批准；高风险/未知始终需要审批**。

**场景引用递归展开**（`classify_automation_operation`）：

```python
scene_refs = [a for a in (actions or []) if a.get("scene_id")]
if scene_refs:
    # 1. 校验所有 scene 都在当前家庭
    scene_rows = db.scalars(select(Scene).where(
        Scene.household_id == context.household_id,
        Scene.id.in_({str(a["scene_id"]) for a in scene_refs}),
    )).all()
    if len(scene_rows) != len({str(a["scene_id"]) for a in scene_refs}):
        requested_device_ids.add(-1)  # 标记缺失，触发 UNKNOWN
    else:
        # 2. 展开场景内所有步骤设备
        steps = db.scalars(select(SceneStep).where(
            SceneStep.scene_id.in_([s.id for s in scene_rows])
        )).all()
        expanded_scene_device_ids = {int(step.device_id) for step in steps ...}
        requested_device_ids.update(expanded_scene_device_ids)
```

**关键作用**：避免「用场景包装门锁」绕过——`create_automation(actions=[{scene_id: 'home_with_lock'}])` 也必须按门锁判定为高风险。

**自动化冲突检测**（`detect_automation_conflicts`）：

```python
if operation in ("create_automation", "update_automation") and args:
    try:
        conflicts = detect_automation_conflicts(
            db=db, context=context, automation_id=automation_id,
            proposed_triggers=args.get("triggers"),
            proposed_actions=args.get("actions"),
        )
        if conflicts: preview["conflicts"] = conflicts
    except Exception:
        logging.getLogger(__name__).warning("冲突检测失败", exc_info=True)
```

**检测维度**：① 同一触发时间窗口 ② 同一动作设备 → 纳入 preview 让审批 UI 提示。

**审批状态机**（`app/agents/graph/`）：

```
START → load_context → model ──(should_continue)──┬─ read_tool ──→ model
                                                  ├─ risk_check ──→ ...
                                                  └─ finalize ──→ END

risk_check ──(route_after_risk)──┬─ model            （低风险 + 自动执行）
                                 ├─ write_tool        （已批准）
                                 └─ approval_interrupt（高风险/未知/手动）

approval_interrupt ──(route_after_approval)──┬─ write_tool（approve）
                                             └─ reject_tool（reject）
```

**关键不变量**：写工具路径**只能**从 `approval_interrupt(approve)` 或 `low_risk_auto` 出来——**写工具路径上没有任何旁路**。

**每轮单写约束**（`risk_node.py`）：

```python
if len(write_calls) != 1 or len(last.tool_calls) != 1:
    return _tool_error(state, last.tool_calls, "每轮只能请求一个写操作，且不能混合只读和写操作")
```

**关键作用**：防止模型「开锁 + 读设备状态」一起做——一次只审一个高风险操作。

**会话租约互斥**（`app/agents/agent_service/lease.py`）：

```python
def acquire_run_lease(db, *, user_id, household_id, session_id, run_id, thread_id) -> bool:
    """已持有有效租约 → 返回 False（409）。
    无租约或租约超时 → 删除旧租约并写入新租约，返回 True。"""
    lease = db.scalar(select(AgentRunLease).where(
        AgentRunLease.user_id == user_id,
        AgentRunLease.household_id == household_id,
        AgentRunLease.session_id == session_id,
    ))
    if lease is not None:
        if now - created < ttl: return False   # 有效租约 → 拒绝
        db.execute(delete(AgentRunLease).where(AgentRunLease.id == lease.id))  # 超时清理
    db.add(AgentRunLease(user_id, household_id, session_id, run_id, thread_id))
    try: db.commit(); return True
    except IntegrityError: return False        # 并发竞争 → 拒绝
```

**机制**：以 `user_id + household_id + session_id` 为唯一约束；TTL 30 秒（`agent_lease_ttl_seconds`）自动处理崩溃；并发请求返回 `AGENT_CONCURRENT_RUN` 错误事件（HTTP 409 语义）。

**待审批有效期 + 主动取消**（`app/agents/agent_service/pending.py`）：

```python
def make_pending(state: dict) -> dict:
    now = datetime.now(timezone.utc)
    state["created_at"] = now.isoformat()
    state["expires_at"] = now.timestamp() + get_settings().approval_ttl_seconds  # 30 分钟
    return state

def is_pending_expired(pending: dict | None) -> bool:
    if pending is None: return True
    expires_at = pending.get("expires_at")
    if expires_at is None: return False   # 旧记录向后兼容
    return datetime.now(timezone.utc).timestamp() > float(expires_at)

async def cancel_pending_approval(saver, thread_id, *, context, pending) -> None:
    # 1. 记录审计：approval_decision { decision: 'cancelled' }
    # 2. 记录 run 结束：status='cancelled'
    # 3. adelete_thread(thread_id) 清理 pending 状态
    ...
```

**模型固定**：`pending` 中保存 `model_name` / `model_id`（`risk_node.py`），恢复时 `resume_agent` 沿用——避免「审批时是模型 A、恢复时切到模型 B」。

**写操作完整审计链**（`app/agents/audit/recorder.py`）：

```python
def record_run_start(context, run_id): ...
def record_approval_required(*, run_id, approval_id, tool, risk_level, reasons): ...
def record_approval_decision(*, run_id, approval_id, decision, automatic=False): ...
def record_tool_call(*, run_id, call_id, tool, args, result, ok=True, duration_ms,
                    approval_id=None, approval_decision=None, automatic=None, error_code=None): ...
def record_run_end(run_id, status="completed", message=""): ...
```

**事件流**（按 `run_id` 串联）：

```
run_start
  ↓
[可选 N 轮 model + read_tool]
  ↓
approval_required { tool, risk_level, reasons }   ← 触发审批
  ↓
approval_decision { decision: approve/reject/cancelled/auto, automatic }   ← 审批结果
  ↓
tool_completed / tool_failed { args (redacted), result, error_code, duration_ms, approval_id, approval_decision }
  ↓
run_end { status: completed/failed/cancelled/disconnected }
```

**文件存储**：按小时轮转写入 `agent_audit/audit_YYYYMMDD_HH.json`，**线程内锁**防止并发写交错。

**敏感信息脱敏**（`app/agents/redaction.py`）：

```python
_SENSITIVE_PATTERNS = [
    re.compile(r"(sk-[A-Za-z0-9_\-]{6,})"),       # API Key
    re.compile(r"(Bearer\s+[A-Za-z0-9_\-\.=]{8,})", re.IGNORECASE),  # Bearer Token
    re.compile(r"(\beyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-\.]{8,})"),  # JWT
]
_MASK = "<redacted>"

def redact_fields(data):
    sensitive_keys = {"api_key", "apiKey", "token", "access_token", "refresh_token", "password", "secret", "authorization"}
    # 递归屏蔽容器中的敏感字段和值
    ...
```

**统一 SSE 事件**（`app/agents/events/stream_tracker.py`）：

- 首次运行（`run_agent`）与审批恢复（`resume_agent`）**复用同一 `StreamTracker.emit_stream_chunk`**；
- 工具去重（`seen_calls` set）+ 阶段状态（`submitted` / `running` / `verified` / `failed`）；
- 前端只需解析这一种事件流，**审批前后 UI 展示完全一致**。

##### ③ 展示过程（一步步画面描述）

| # | 演示画面 | 关键证据 / 数值 |
| - | -------- | --------------- |
| 1 | **低风险自动执行**：用户说"把客厅灯调暗到 40%" → 立即执行，UI 出现绿色 toast「已调暗客厅灯」 | 审计：`approval_decision { automatic: true, decision: 'approve' }` |
| 2 | **高风险弹审批**：用户说"把门锁打开" → 立即弹出红色审批卡 `AgentConfirmationCard`：标题「开锁 - 大门门锁」+ 风险等级 HIGH + 理由 "设备「大门口锁」属于高风险设备类型" + 涉及设备列表 | UI 等待用户点击「确认」/「拒绝」 |
| 3 | **场景包装演示**：用户说"执行回家模式"（场景中含门锁开锁 + 灯开 + 空调开）→ 弹出审批卡，**风险等级 = HIGH**（不是 LOW） | 验证「场景引用递归展开」 |
| 4 | **审批确认**：用户点击「确认」→ 卡片变为「执行中…」→ `tracker.emit_execution_status(status='running')` → 工具完成后 `status='verified'` | 审计：`tool_completed { approval_id, approval_decision: 'approve' }` |
| 5 | **审批拒绝**：再次尝试"开锁"→ 弹审批卡 → 用户点击「拒绝」→ 卡片消失，聊天窗口出现「已拒绝：开锁大门口锁」 | 审计：`approval_decision { decision: 'reject' }` |
| 6 | **过期自动拒绝**：审批卡 30 分钟未操作 → 自动消失，聊天窗口出现「待审批操作已过期，请重新发起」 | 后端 `is_pending_expired` 返回 True |
| 7 | **主动取消**：审批卡存在时，用户点击「取消」→ 卡片消失，聊天窗口出现「你取消了待审批操作」 | 审计：`approval_decision { decision: 'cancelled' }` |
| 8 | **并发保护演示**：用 curl 模拟同一 session 两次并发 `POST /agent/runs` → 第一次成功，第二次立即返回 `AGENT_CONCURRENT_RUN` 错误 | SSE 错误事件 `code: 'AGENT_CONCURRENT_RUN'` |
| 9 | **未知名强制审批**：用户上传一张图片让模型操作"打开那个灯"（模型无法识别 device_id）→ 弹审批卡，**风险等级 = UNKNOWN** + 理由 "设备不存在或不属于当前家庭" | 验证「unknown 不可绕行」 |
| 10 | **审计链展示**：打开 `agent_audit/audit_20260815_14.json` → 用 `jq` 过滤某 `run_id` → 看到完整事件流 `run_start → approval_required → approval_decision → tool_completed → run_end` | 敏感字段已脱敏为 `<redacted>` |

**演示重点**：「风险分级不是模型决定，而是代码层规则 + 状态机强制 + 完整审计——即使 1B 模型『想』执行高风险操作，**没有用户人工确认，状态机不会放行**」。

##### ④ 与现有方案差异

| 维度 | 常见方案（LangChain tool guard / OpenAI Moderation） | 本项目 |
| ---- | ----------------------------------------------- | ------ |
| 判定主体 | 依赖 LLM 自评 / 外部 API | **代码层规则**（设备类型 + 关键词 + 场景展开） |
| 高风险保障 | 取决于护栏强度 | **强制不可绕行**（状态机路径唯一） |
| 混合操作 | 允许一次多个 | **每轮单写 + 不可混读混写** |
| 过期机制 | 一般无 | **30 分钟 TTL + 主动取消 + 过期自动拒绝** |
| 并发保护 | 需自实现 | **租约互斥（DB 唯一约束 + TTL）** |
| 模型切换 | 审批时切模型可能执行不同逻辑 | **审批记录原 model_id，恢复时强制沿用** |
| 审计 | 一般仅有日志 | **6 类事件按 run_id 串联 + 小时桶 JSON + 脱敏** |
| 边缘友好 | 强依赖外部 | **完全本地** |

---

#### 创新点 4：大模型驱动的场景编排 —— 自然语言直接转结构化自动化规则

##### ① 背景与痛点

**为什么是边缘刚需**：
小模型推理弱，但「**自然语言 → 结构化规则**」恰好是 1B 模型可胜任的窄任务（领域集中、模板少、输入短），把这条路径打通，可让用户**完全跳过表单**。

边缘家庭用户对「复杂条件 + 定时 + 设备状态触发」的自动化需求真实存在，但「**填 4 层表单**」的门槛把绝大多数人挡在门外。本项目让用户**用一句话描述自动化意图**，系统在后台完成「意图解析 → 工具调用 → 风险分级 → 冲突检测 → 审批 UI → 落库」全链路。

##### ② 完整技术细节

**用户输入 → 工具调用**：

```
用户："每周五 18:30 后若客厅有人就开氛围灯"
       ↓ (LLM function calling)
{
  "name": "create_automation",
  "args": {
    "name": "周五晚归家氛围灯",
    "triggers": [{"type": "schedule", "cron": "30 18 * * 5"}],
    "conditions": [{"type": "device_state", "device_id": 42, "state": "motion_detected", "equals": true}],
    "actions": [{"type": "set_device_power", "device_id": 17, "power": "on", "brightness": 60}],
    "priority": 5,
    "cooldown_seconds": 300
  }
}
```

**结构化产出**：`create_automation` / `update_automation` / `delete_automation` / `set_automation_enabled` 四个写工具，参数结构固定为 `name + triggers + conditions + actions + priority + cooldown_seconds + delay_seconds`。

**风险分级**（`classify_automation_operation`）：

```python
elif operation in ("create_automation", "update_automation"):
    action_devices = []
    requested_device_ids = {a.get("device_id") for a in (actions or []) if a.get("device_id") is not None}
    # 递归展开场景引用设备
    expanded_scene_device_ids: set[int] = set()
    scene_refs = [a for a in (actions or []) if a.get("scene_id")]
    if scene_refs:
        scene_rows = db.scalars(select(Scene).where(...)).all()
        if len(scene_rows) != len({str(a["scene_id"]) for a in scene_refs}):
            requested_device_ids.add(-1)  # 缺失场景 → UNKNOWN
        else:
            steps = db.scalars(select(SceneStep).where(SceneStep.scene_id.in_([s.id for s in scene_rows]))).all()
            expanded_scene_device_ids = {int(step.device_id) for step in steps ...}
            requested_device_ids.update(expanded_scene_device_ids)

    if requested_device_ids:
        action_devices = list(db.scalars(select(Device).where(...)).all())

    found_device_ids = {device.id for device in action_devices}
    missing_device_ids = requested_device_ids - found_device_ids
    high_risk_devices = [d for d in action_devices if _is_high_risk_device(d)]

    if missing_device_ids:
        level = RiskLevel.UNKNOWN
        reasons.append("动作包含不存在或不属于当前家庭的设备或场景")
    elif high_risk_devices:
        level = RiskLevel.HIGH
        reasons.append("包含高风险设备：" + "、".join(d.name for d in high_risk_devices))
    else:
        level = RiskLevel.LOW
        reasons.append("仅包含已识别的普通家居设备操作")
```

**删除与启停的特殊规则**：

```python
if operation == "delete_automation":
    level = RiskLevel.HIGH
    reasons.append("删除自动化规则可能影响家庭自动化流程")
elif operation == "set_automation_enabled":
    level = RiskLevel.LOW
    reasons.append("仅切换自动化规则的启用状态")
```

**冲突检测**（`detect_automation_conflicts`）：

```python
if operation in ("create_automation", "update_automation") and args:
    try:
        conflicts = detect_automation_conflicts(
            db=db, context=context, automation_id=automation_id,
            proposed_triggers=args.get("triggers"),
            proposed_actions=args.get("actions"),
        )
        if conflicts: preview["conflicts"] = conflicts
    except Exception:
        logging.getLogger(__name__).warning("冲突检测失败", exc_info=True)
```

**检测维度**：① 同一触发时间窗口 ② 同一动作设备 → 纳入 preview 让审批 UI 提示「这条规则与 X 冲突」。

**预览信息**（`preview` dict）：

```python
preview = {
    "kind": "create_automation",
    "operation": "create_automation",
    "automation_name": "周五晚归家氛围灯",
    "trigger_count": 1,
    "condition_count": 1,
    "action_count": 1,
    "summary": "创建自动化规则：周五晚归家氛围灯",
    "affected_device_names": ["客厅氛围灯", "客厅人体传感器"],
    "conflicts": [...],  # 可选
    "risk_level": "low",
}
```

**完整闭环**：

```
用户："每周五 18:30 后若客厅有人就开氛围灯"
  ↓
LLM：function_call(create_automation, {...})   ← 1B 模型 narrow task
  ↓
risk_check → 低风险（氛围灯）
  ↓
若 auto_execute_low_risk=True：直接进 write_tool
若 False：弹出审批卡片（展示 preview 含触发器/条件/动作/冲突）
  ↓
write_tool → 数据库 + 会话树（custom 节点含自动化 ID）
  ↓
审计：run_start → approval_required → approval_decision → tool_completed → run_end
```

**子 Agent 委派**（`app/agents/subagents/`）：

```python
DOMAIN_KEYWORDS = {
    "device": {"设备", "灯", "空调", "温度", "离线", "告警", "状态", "插座", "开关"},
    "scene":  {"场景", "模式", "回家", "离家", "观影", "睡眠", "起床"},
    "automation": {"自动化", "定时", "每天", "每周", "如果", "当", "触发", "规则"},
    "energy": {"能耗", "用电", "费电", "电量", "节能", "电费", "功率", "账单"},
    "comfort": {"舒适", "舒适度", "湿度", "通风", "太热", "太冷", "太干"},
    "security": {"门锁", "摄像头", "安防", "警报", "监控", "布防", "撤防", "入侵", "锁", "门铃", "报警"},
}

def resolve_delegated_domain(message: str) -> str | None:
    """仅当路由结果恰好命中单个可委托领域时才委托；
    复合意图、general 一律返回 None 走主图。"""
    tags = route_intent(message)
    if len(tags) == 1 and tags[0] in DELEGATABLE_DOMAINS: return tags[0]
    return None
```

**子 Agent 价值**：每个领域子 Agent 工具数 ≤ 8、提示词精简，**1B 模型在窄任务上选错工具的概率显著降低**。

##### ③ 展示过程（一步步画面描述）

| # | 演示画面 | 关键证据 / 数值 |
| - | -------- | --------------- |
| 1 | **用户输入**："每周五 18:30 后若客厅有人就开氛围灯" | UI 显示用户消息 |
| 2 | **模型解析**：流式输出「我来帮你创建这条自动化…」→ 1B 模型调用 `create_automation` | Tool 名称 = `create_automation`；耗时 ≈ 1.5s |
| 3 | **风险分级**：后端 `classify_automation_operation` → LOW（氛围灯为普通设备） | `risk_level=low` |
| 4 | **冲突检测**：后端检索「同一时间窗口 + 同一动作设备」的现有规则 → 找到 1 条「周五 19:00 关氛围灯」 | `preview.conflicts=[{...}]` |
| 5 | **审批 UI**：弹出审批卡，标题「创建自动化规则：周五晚归家氛围灯」+ 触发器/条件/动作摘要 + 冲突提示「与"周五 19:00 关氛围灯"动作设备冲突，是否继续？」 | 等待用户决策 |
| 6 | **执行**：用户点击「确认」→ 自动化落库 + 会话树追加 custom 节点 | `tool_completed { ok: true }` |
| 7 | **对话确认**：「已为你创建自动化规则：周五晚归家氛围灯」 | 助手消息 |
| 8 | **删除演示**：用户说"把那条周五的规则删掉" → 风险等级 = HIGH → 弹审批卡 | `risk_level=high` + 理由"删除自动化规则可能影响家庭自动化流程" |
| 9 | **场景包装演示**：用户说"如果我不在家时有人按门铃就开灯报警"（含场景引用）→ 风险分级展开场景设备 | preview `expanded_scene_device_names` 列出 |
| 10 | **子 Agent 委派**：用户说"今天哪些灯还开着" → `resolve_delegated_domain` 命中 `device` → 委派给 device 只读子 Agent | `thread_id="...:subagent:device"`，主图不参与 |

**演示重点**：「用自然语言描述规则，系统替你完成『解析 + 风险 + 冲突 + 审批 + 落库 + 审计』全链路；1B 模型虽弱，**但只承担它擅长的窄任务（自然语言 → JSON）**，其他环节由代码层 + 子 Agent + 风险分类器接管」。

##### ④ 与现有方案差异

| 维度 | Home Assistant YAML | 米家 IF-THEN 表单 | **本项目** |
| ---- | ------------------- | ----------------- | ---------- |
| 输入方式 | 手写 YAML | 填表单 | **自然语言** |
| 工具调用 | 人工调用 service | 人工 | **1B 模型 function calling** |
| 风险分级 | 无 | 无 | **代码层规则 + 场景递归展开** |
| 冲突检测 | 无 | 无 | **触发器 + 动作双重检测** |
| 审批 UI | 无 | 无 | **高风险/未知强制审批** |
| 审计 | HA 日志 | 云端日志 | **本地 6 类事件按 run_id 串联** |
| 边缘友好 | 强但需本地 HA 服务 | 弱 | **完全本地** |
| 1B 模型可承载 | — | — | **✅（窄任务）** |

---

## 3 实施方案

### 3.1 技术可行性分析

#### 3.1.1 数据采集与标注

| 类别 | 来源 | 规模 | 说明 |
| ---- | ---- | ---- | ---- |
| 设备状态 | 模拟器（`app/services/device.py`） | 自定义 | 100+ 虚拟设备覆盖主流类型 |
| 工具调用结果 | 模拟器 | 自定义 | 完整 JSON 化，覆盖成功/失败/超时 |
| 自动化规则样本 | 行业常识 + 内部生成 | 50+ 条 | 覆盖：定时 / 条件 / 状态变化 / 场景 |
| 长对话压测 | 自动化脚本 | 200+ 轮 | 验证压缩、令牌估算、迭代式摘要 |
| 风险用例 | 内部构建 | 30+ 条 | 覆盖 read_only / low / high / unknown |

**结论**：本项目数据需求量小、形态可控，**完全无外部数据依赖**，适合在赛期内构建高质量评测集。

#### 3.1.2 行业知识获取

- **设备类型与场景模式**：智能家居行业公开常识，已整理到系统提示词（`app/agents/prompts.py`）与风险策略表（`app/agents/risk/classifier.py`）；
- **高风险设备类型表**：`lock / door_lock / camera / security / alarm`，配合中文关键词（门锁/摄像头/安防/警报）双重判定；
- **场景模式表**：「回家模式 / 影院模式 / 睡眠模式 / 离家模式」等十余种，按设备组合区分；
- **风险策略库**：4 级风险 + 4 类高风险设备 + 场景展开 + 冲突检测，无需大规模训练数据。

**结论**：行业知识靠**公开常识 + 工程化策略表**即可覆盖，**无需大规模训练**。

#### 3.1.3 算力硬件可行性论证（核心）

| 维度 | 论证 |
| ---- | ---- |
| **模型大小** | MiniCPM-2.6-1B / Phi-3.5-mini / Qwen2.5-1.5B 等 1B 模型 **INT4 量化后权重约 0.5–1GB** |
| **推理时显存** | 权重 + KV cache + 框架开销，预计 2–4GB |
| **边缘设备** | Jetson Orin Nano 8GB / Orin NX 16GB，内置 CUDA + TensorRT |
| **推理引擎** | llama.cpp（CUDA 后端）/ vLLM / Ollama / TensorRT-LLM 均可承载 |
| **接口** | 所有引擎都暴露 OpenAI 兼容 HTTP 接口 |
| **接入** | `app/agents/providers/openai_compatible.py` 已支持 OpenAI 兼容协议，`api_endpoint` 指向本地即可 |
| **延迟预期** | 首次 token 延迟 < 1.5s；持续生成 ≥ 8 tokens/s（**实测后填具体值**） |
| **并发** | 单会话串行；多会话通过 OS 进程级调度，1B 模型在 Orin Nano 上可同时服务 2–3 个对话 |

**结论**：1B 模型 + 边缘设备的技术路线**完全可行**，且已通过前期 `app/agents/providers/openai_compatible.py` 的接入验证（仅需在 `.env` 中修改 `api_endpoint` 即可切换本地/云端）。

#### 3.1.4 总体可行性结论

| 维度 | 结论 |
| ---- | ---- |
| 数据 | ✅ 完全可控，模拟器生成 |
| 知识 | ✅ 行业常识 + 策略表，无需训练 |
| 算力 | ✅ 1B 模型 + INT4 量化在 Jetson 8GB 上可运行 |
| 工程基础 | ✅ 已有可运行原型 + 完整测试 + 设计文档 |
| 时间 | ✅ 赛期与里程碑匹配（见 §3.3） |

**最终结论**：技术路线可行，工程实现路径明确，赛期内可交付。

---

### 3.2 技术细节

> 本节为文档核心：按「总体架构 → 模型部署 → 各核心模块 → 预期指标」展开，每个模块落到代码证据 + 论证。

#### 3.2.1 总体架构

```
┌──────────────────────────────────────────────────────────┐
│  浏览器（Vue 3 + SSE）                                    │
│  - Chat UI / 审批卡片 / 自动化管理 / 设备控制台            │
└────────────────────────┬─────────────────────────────────┘
                         │ HTTPS / SSE
┌────────────────────────▼─────────────────────────────────┐
│  FastAPI + LangGraph 后端（部署在 Jetson Orin Nano）      │
│  ┌──────────────────────────────────────────────────┐    │
│  │  API 层（FastAPI）                                │    │
│  │  - 鉴权（JWT）+ 多家庭隔离 + 限流                 │    │
│  │  - SSE 流式响应（useHomeChat.ts / stream_tracker）│    │
│  └────────────┬─────────────────────────────────────┘    │
│               │                                           │
│  ┌────────────▼─────────────────────────────────────┐    │
│  │  Agent 编排层（LangGraph StateGraph）             │    │
│  │  load_context → model → {read_tool, risk_check}   │    │
│  │               → {auto, write, approval_interrupt} │    │
│  │  + sub-agent 委派 + 并发租约 + 审计               │    │
│  └────────────┬─────────────────────────────────────┘    │
│               │                                           │
│  ┌────────────▼─────────────────────────────────────┐    │
│  │  会话与压缩层                                     │    │
│  │  - 会话树（append-only / SQLite / WAL）           │    │
│  │  - 上下文压缩（双路径估算 + 切割点 + 迭代摘要）   │    │
│  │  - 分支摘要 + 文件操作跟踪                        │    │
│  └────────────┬─────────────────────────────────────┘    │
│               │                                           │
│  ┌────────────▼─────────────────────────────────────┐    │
│  │  模型接入层（OpenAI 兼容）                        │    │
│  │  - ChatOpenAI → 本地 vLLM/llama.cpp/Ollama        │    │
│  └────────────┬─────────────────────────────────────┘    │
└───────────────┼──────────────────────────────────────────┘
                │ OpenAI 兼容 HTTP
┌───────────────▼──────────────────────────────────────────┐
│  本地模型服务（运行在 Jetson）                            │
│  - llama.cpp server (CUDA) / vLLM / TensorRT-LLM         │
│  - 模型：MiniCPM-2.6-1B INT4 量化                         │
└──────────────────────────────────────────────────────────┘
                │
┌───────────────▼──────────────────────────────────────────┐
│  存储（SQLite WAL）                                       │
│  - 业务表（users / households / devices / scenes / ...） │
│  - 会话树（session_tree_entries / session_tree_records）  │
│  - LangGraph checkpointer（langgraph_checkpoints）        │
│  - 审计（hourly JSONL files in agent_audit/）             │
└──────────────────────────────────────────────────────────┘
```

**关键设计原则**：
- **接入层 OpenAI 兼容**：让本地推理服务（vLLM / llama.cpp / Ollama）和云端服务（DeepSeek / OpenAI）走同一适配器，**本地 ↔ 云端切换零代码改动**；
- **存储与逻辑分离**：业务表与会话树 / 审计 / checkpointer 共用 SQLite 但 schema 独立，便于备份与迁移；
- **fail-safe 默认**：所有外部依赖失败（LLM / DB / SSE）只记日志，**不中断用户主对话**。

---

#### 3.2.2 模型本地部署与推理优化（边缘重点）

##### 3.2.2.1 推理引擎选型

| 引擎 | 优势 | 适用场景 | 部署方式 |
| ---- | ---- | -------- | -------- |
| **llama.cpp server (CUDA)** | 成熟、C++ 实现、显存友好、支持多种量化 | 通用首选 | `llama-server -m model.gguf -ngl 99 --host 0.0.0.0` |
| **vLLM** | 高吞吐、continuous batching | 多会话并发 | `vllm serve model-path --port 8000` |
| **Ollama** | 一键拉取、模型管理 | 开发与体验 | `ollama serve` + `ollama pull` |
| **TensorRT-LLM** | NVIDIA 官方、极致优化 | 生产极致性能 | 需先用 `trtllm-build` 编译 engine |

**本项目推荐**：开发期用 **Ollama / llama.cpp server**（零编译成本），生产期用 **vLLM 或 TensorRT-LLM**（高吞吐）。

##### 3.2.2.2 量化方案

- **INT4（GPTQ / AWQ / GGUF Q4_K_M）**：权重从 FP16 2GB → INT4 0.5–1GB，**推荐用于 1B 模型在 8GB 显存**；精度损失 < 2%（智能家居任务中不敏感）；
- **INT8（GPTQ / AWQ / GGUF Q8_0）**：保留更多精度，权重约 1–1.5GB，**用于 16GB 显存**或精度敏感场景；
- **FP16（基线）**：未量化，仅作对照。

**预期显存占用（1B 模型）**：

| 量化 | 权重 | KV cache + 框架 | 峰值 | 适配 |
| ---- | ---- | --------------- | ---- | ---- |
| INT4 | 0.5–1GB | 1–2GB | 2–3GB | Jetson Orin Nano 8GB |
| INT8 | 1–1.5GB | 1.5–2.5GB | 2.5–4GB | Jetson Orin Nano 8GB / NX 16GB |
| FP16 | 2GB | 2–3GB | 4–5GB | Jetson Orin NX 16GB |

##### 3.2.2.3 OpenAI 兼容接入

**代码证据**（`smarthome-api/app/agents/providers/openai_compatible.py`）：

```python
class OpenAICompatibleProvider(Provider):
    def build(self, cfg: AIModel, client: dict) -> BaseChatModel:
        return ChatOpenAI(
            model=cfg.name,
            api_key=client["api_key"],
            base_url=client["base_url"],   # ← 改这一行指向本地
            temperature=cfg.temperature,
            max_tokens=cfg.max_tokens,
            timeout=self._settings.model_timeout_seconds,
            max_retries=self._settings.model_max_retries,
            stream_usage=True,             # ← 让 usage 流式返回
        )
```

**接入方式**：
- 部署本地推理服务（Ollama / llama.cpp server / vLLM）后，在前端「模型设置」中新增「本地边缘模型」条目，`api_endpoint` 填 `http://localhost:11434/v1`（Ollama）或 `http://localhost:8080/v1`（llama.cpp）；
- 切换模型时，**整个应用代码无任何改动**——这正是「OpenAI 兼容协议」的红利。

##### 3.2.2.4 工具调用能力校验

**代码证据**（`smarthome-api/app/agents/graph/__init__.py`）：

```python
try:
    bound_model = model.bind_tools(active_tools)
except Exception as exc:
    raise ModelToolCallingUnsupported(
        "当前模型不支持工具调用，无法作为 Agent 模型使用"
    ) from exc
```

**为什么关键**：不是所有小模型都支持 function calling；运行前通过 `bind_tools` 校验，**不支持的模型立即失败**（而不是在用户问「帮我关灯」时中途崩溃），保护体验。

---

#### 3.2.3 Agent 编排与自主决策

##### 3.2.3.1 LangGraph 状态机

**代码证据**（`app/agents/graph/__init__.py`）：

```
START → load_context → model ──(should_continue)──┬─ read_tool ──→ model
                                                  ├─ risk_check ──→ ...
                                                  └─ finalize ──→ END

risk_check ──(route_after_risk)──┬─ model            （低风险 + 自动执行）
                                 ├─ write_tool        （已批准）
                                 └─ approval_interrupt（高风险/未知/手动）

approval_interrupt ──(route_after_approval)──┬─ write_tool（approve）
                                             └─ reject_tool（reject）
```

**节点职责**：
- `load_context`：从会话树加载（压缩后）历史，**清空 LangGraph checkpointer 旧历史**（避免重复）——见 `runner._load_tree_history`；
- `model`：模型推理节点，输出文本 / 工具调用 / 思维链；
- `read_tool`：只读工具执行（list_devices / get_device / list_automations …）；
- `risk_check`：风险分级 + 审批构造（见 §3.2.5）；
- `approval_interrupt`：高风险 / 未知 / 手动模式时中断，向前端推送 `approval_required` SSE 事件；
- `write_tool`：写工具执行（受审批保护）；
- `reject_tool`：用户拒绝后给模型一个工具结果拒绝说明；
- `finalize`：汇总结果，触发压缩。

##### 3.2.3.2 子 Agent 委派（领域隔离）

**代码证据**（`app/agents/subagents/router.py`）：

```python
DOMAIN_KEYWORDS = {
    "device":     {"设备", "灯", "空调", "温度", "离线", "告警", "状态", "插座", "开关"},
    "scene":      {"场景", "模式", "回家", "离家", "观影", "睡眠", "起床"},
    "automation": {"自动化", "定时", "每天", "每周", "如果", "当", "触发", "规则"},
    "energy":     {"能耗", "用电", "费电", "电量", "节能", "电费", "功率", "账单"},
    "comfort":    {"舒适", "舒适度", "湿度", "通风", "太热", "太冷", "太干"},
    "security":   {"门锁", "摄像头", "安防", "警报", "监控", "布防", "撤防", "入侵", "锁", "门铃", "报警"},
}

def resolve_delegated_domain(message: str) -> str | None:
    """仅当路由结果恰好命中单个可委托领域时才委托；
    复合意图、general 一律返回 None 走主图。"""
    tags = route_intent(message)
    if len(tags) == 1 and tags[0] in DELEGATABLE_DOMAINS: return tags[0]
    return None
```

**集成点**（`runner._run_agent_body`）：

```python
domain = resolve_delegated_domain(message)
include_write = is_write_domain(domain)
# ...
if domain is not None and not include_write:
    # 只读子 Agent：单轮查询，不加载会话树历史，并使用独立 thread 隔离 checkpoint
    thread_id = f"{base_thread_id}:subagent:{domain}"
else:
    # 主图 或 写能力域子 Agent：共用 thread_id，保证审批状态可被 resume_agent 找到
    thread_id = base_thread_id
```

**优势**：
- 1B 模型在窄任务（单领域）上的工具选择准确率显著高于宽任务（19 个工具混杂）；
- 只读子 Agent 用独立 `thread_id` 隔离 checkpoint，不污染主图；
- 写能力子 Agent 仍走主图的 `risk_check → approval_interrupt` 闭环。

##### 3.2.3.3 会话租约（防止并发串线）

**代码证据**（`app/agents/agent_service/lease.py`）：

```python
def acquire_run_lease(db, *, user_id, household_id, session_id, run_id, thread_id) -> bool:
    """已持有有效租约 → 返回 False（409，避免并发写入同一 thread_id）。
    无租约或租约超时 → 删除旧租约并写入新租约，返回 True。"""
```

**机制**：
- 在 `run_agent` 真正开始流式前**先**获取租约；
- 租约以 `user_id + household_id + session_id` 为唯一约束；
- 租约 TTL 默认 30 秒（`agent_lease_ttl_seconds`），进程崩溃后能自动恢复；
- 并发请求返回 `AGENT_CONCURRENT_RUN` 错误事件（HTTP 409 语义），**不串写 checkpoint / 审批状态**。

##### 3.2.3.4 待审批管理

**代码证据**（`app/agents/agent_service/pending.py`）：

```python
def make_pending(state: dict) -> dict:
    now = datetime.now(timezone.utc)
    state["created_at"] = now.isoformat()
    state["expires_at"] = now.timestamp() + get_settings().approval_ttl_seconds
    return state

def is_pending_expired(pending: dict | None) -> bool:
    if pending is None: return True
    expires_at = pending.get("expires_at")
    if expires_at is None: return False  # 旧记录，向后兼容
    return datetime.now(timezone.utc).timestamp() > float(expires_at)

async def cancel_pending_approval(saver, thread_id, *, context, pending) -> None:
    # 1. 记录审计
    # 2. 删除 checkpoint 线程，清理 pending 状态
    ...
```

**关键设计**：
- **有效期**：默认 30 分钟（`approval_ttl_seconds`），过期自动拒绝；
- **主动取消**：用户可调用 `cancel_pending_approval` 立即拒绝并清理；
- **恢复时校验**：`resume_agent` 读取 pending 时若已过期，直接返回 `AGENT_APPROVAL_EXPIRED` 错误事件，**不让「过期审批」执行**；
- **模型固定**：`pending` 中保存 `model_name` / `model_id`，恢复时沿用，避免「审批时是模型 A、恢复时切到模型 B」；
- **清理机制**：`adelete_thread` 删除整个 checkpoint 线程（消息历史由会话树管理，不丢失）。

##### 3.2.3.5 统一 SSE 事件

**代码证据**（`app/agents/events/stream_tracker.py`，`resumer.py`）：

- 首次运行（`run_agent`）与审批恢复（`resume_agent`）**复用同一 `StreamTracker` 事件转换器**；
- 流式消息经 `tracker.emit_stream_chunk(message, node)` 转为标准化 SSE 事件：`agent_text` / `tool_started` / `tool_completed` / `approval_required` / `run_completed` / `error`；
- 工具去重（`seen_calls` set）+ 阶段状态（`submitted` / `running` / `verified` / `failed`）；
- 前端（`useHomeChat.ts`）只需解析这一种事件流，**审批前后 UI 展示完全一致**。

---

#### 3.2.4 会话树形存储（核心技术细节）

> 本节在 §2.2 创新点 2 中已给出完整细节（含 6+1 不变式、append-only、SQLite WAL、上下文投影、fail-safe 接入层）。本节补充与压缩/Agent 的集成点。

**与压缩的集成**：

- `find_cut_point` / `prepare_compaction` 在树路径上工作，从 `path_entries[-1].type == "compaction"` 判定「已压缩过」；
- 虚拟条目机制：把上次压缩的 `retained_tail` 重新映射为虚拟 message entry 纳入下次切割点计算；
- 压缩完成后追加 1 条 `type=compaction` 节点，**`default_context_entry_transform` 只保留最后一个 compaction + 其后所有 entry**。

**与 Agent 的集成**（`runner._load_tree_history`）：

```python
async def _load_tree_history(session_id, thread_id):
    history = build_context_messages(session_id)   # 摘要 + retained_tail 投影为 LangChain 消息
    saver = await get_checkpointer()
    await saver.adelete_thread(thread_id)          # 清空 checkpointer 旧历史
    return history
```

**关键**：压缩后下一轮 Agent 走「树上下文（摘要 + retained_tail）」，**不**走 LangGraph checkpointer 旧历史——**「压缩后旧历史被丢弃，新历史带摘要继续」**。

**与风险的集成**（通过子 Agent 审计）：

```python
def mirror_subagent(chat_session_id, domain, task, summary, *, data=None, usage=None) -> str:
    """把一次子 Agent 运行镜像为 custom 节点（供审计，不进对话历史）。"""
    session = get_or_create_tree_session(chat_session_id)
    try:
        return session.append_custom_entry("subagent", {
            "domain": domain, "task": task, "summary": summary,
            "data": data or {}, "usage": usage or {},
        })
    finally: session.close()
```

**关键**：`build_context_messages` 会跳过 `custom` 节点，**不会污染 Agent 上下文**；但该节点保留在树中供审计与后续压缩钩子使用。

---

#### 3.2.5 上下文压缩（核心技术细节）

> 完整细节见 §2.2 创新点 1。本节补充工程集成。

**触发点**（`runner.py`）：

```python
# 每轮 Agent 推理结束、助手消息落库后
_sync_session_tree(context.session_id, lambda: mirror_assistant_message(
    context.session_id, tracker.collected.strip(),
    usage={"input": last_input_tokens, "output": last_output_tokens,
           "totalTokens": last_input_tokens + last_output_tokens},
))
await asyncio.to_thread(_maybe_compact_tree, context, model_config)
```

**关键**：
- 压缩在**独立线程**执行（`asyncio.to_thread`），避免同步 LLM 调用阻塞事件循环；
- 任何失败仅记录日志，**不中断主流程**；
- 助手消息带 `usage` 镜像到树，让双路径 token 估算在生产中真正生效。

**压缩参数与配置**（`.env`）：

```bash
COMPACTION_ENABLED=true                       # 是否启用压缩
COMPACTION_RESERVE_TOKENS=16384               # 预留 token（用于生成响应）
COMPACTION_KEEP_RECENT_TOKENS=20000           # 保留尾巴 token
COMPACTION_RETRY_ATTEMPTS=2                   # 瞬时错误重试次数
COMPACTION_MAX_TOKENS=4096                    # 摘要响应最大 token
COMPACTION_BRANCH_SUMMARY_MAX_TOKENS=2048     # 分支摘要最大 token
COMPACTION_TOOL_RESULT_MAX_CHARS=2000         # 摘要请求中工具结果截断
SESSION_TREE_CONTEXT_WINDOW=32768             # 树上下文窗口（按模型覆盖）
```

---

#### 3.2.6 风险分级与人工审批（核心技术细节）

> 完整细节见 §2.2 创新点 3。本节补充审计的工程集成。

**审计配置**（`.env`）：

```bash
AGENT_AUDIT_ENABLED=true
AGENT_AUDIT_PATH=./agent_audit             # 小时桶 JSONL 文件目录
APPROVAL_TTL_SECONDS=1800                  # 审批有效期（30 分钟）
AGENT_LEASE_TTL_SECONDS=30                 # 租约 TTL
```

**审计事件 schema**（`audit_YYYYMMDD_HH.json` 每行一条 JSON）：

```json
{"event":"run_start","run_id":"run-abc","user_id":1,"household_id":1,"session_id":42,"ts":"2026-08-15T14:23:01Z"}
{"event":"approval_required","run_id":"run-abc","approval_id":"run-abc:call-1","tool":"set_device_power","risk_level":"high","reasons":["设备『大门门锁』属于高风险设备类型"]}
{"event":"approval_decision","run_id":"run-abc","approval_id":"run-abc:call-1","decision":"approve","automatic":false}
{"event":"tool_completed","run_id":"run-abc","call_id":"call-1","tool":"set_device_power","args":{"device_id":7,"power":"on"},"result":"{\"ok\":true}","duration_ms":312,"approval_id":"run-abc:call-1","approval_decision":"approve","ts":"2026-08-15T14:23:45Z"}
{"event":"run_end","run_id":"run-abc","status":"completed","ts":"2026-08-15T14:23:46Z"}
```

**用 jq 按 run_id 串联**：

```bash
cat agent_audit/audit_20260815_14.json | jq -c "select(.run_id==\"run-abc\")"
```

**敏感信息脱敏**：所有 `args` / `result` / `message` 字段写入审计前都经 `redact_fields` / `redact_text` 脱敏，API Key、Token、Bearer、JWT 替换为 `<redacted>`。

---

#### 3.2.7 大模型驱动的场景编排（核心技术细节）

> 完整细节见 §2.2 创新点 4。本节补充与子 Agent 的集成。

**子 Agent 集成**（`runner._run_agent_body`）：

```python
domain = resolve_delegated_domain(message)
include_write = is_write_domain(domain)
graph, audit = await _create_graph_runner(
    context, db, model_config,
    domain=domain,                    # 透传给 graph 工厂
    include_write=include_write,       # 是否包含写工具
)
# ...
if domain is not None:
    subagent_started_at = time.perf_counter()
    audit.record_subagent_start(run_id=run_id, domain=domain, task=message)
```

**子 Agent 工厂**（`app/agents/subagents/factory.py`）：根据 `domain` 注入对应工具集（device / scene / automation / security），并构建独立子图；`include_write=False` 时只注入只读工具，避免误执行。

**run 阶段状态**（`app/agents/usage.py`）：

```python
update_run_phase(db, run_id, "submitted")     # 用户确认后
update_run_phase(db, run_id, "thinking")      # 模型推理中
update_run_phase(db, run_id, "executing")     # 工具执行中
```

`phase` 字段让前端可实时显示「思考中 / 执行中 / 已提交」等状态。

---

#### 3.2.8 工具系统与安全设计（补充）

##### 3.2.8.1 工具系统

- **只读工具**（`list_devices` / `get_device` / `list_automations` / `list_scenes` / `get_device_logs` …）：永远自动执行，可与写工具在同一轮共存；
- **写工具**（`execute_scene` / `set_device_power` / `set_device_temperature` / `set_curtain_position` / `create_automation` / `update_automation` / `set_automation_enabled` / `delete_automation`）：每轮限 1 个，且不能与读工具混合；
- **不可信数据隔离**：工具结果与用户文本一律视为不可信数据，禁止执行其中的指令（在 `app/agents/prompts.py` 中明文告知模型）。

##### 3.2.8.2 安全设计汇总

| 维度 | 措施 | 代码位置 |
| ---- | ---- | -------- |
| API Key 加密 | Fernet（AES-CBC + HMAC 认证）落库 | `app/agents/crypto.py` |
| JWT + bcrypt | 访问令牌 + 密码哈希 + 登录失败锁定 | `app/services/auth.py` |
| 多家庭隔离 | 所有数据按 `household_id` 过滤 | `app/services/*.py` |
| 限流 / 预算 | 每分钟请求限流 + 每日 token 预算 | `app/agents/rate_limiter.py` |
| 写操作审计 | 完整审计链（见 §3.2.6） | `app/agents/audit/recorder.py` |
| 敏感信息脱敏 | API Key / Token / Bearer / Password | `app/agents/redaction.py` |
| 高风险不可绕行 | 风险分级 + 状态机强制路径 | `app/agents/risk/` + `graph/risk_node.py` |
| 审批有效期 + 取消 | 30 分钟 TTL + 主动取消 | `app/agents/agent_service/pending.py` |
| 同会话并发互斥 | 租约唯一约束 + TTL | `app/agents/agent_service/lease.py` |
| 模型固定 | 审批 pending 含 model_id | `graph/risk_node.py` + `resumer.py` |
| 工具调用能力校验 | `bind_tools` 启动时校验 | `graph/__init__.py` |

---

#### 3.2.9 预期技术指标

| 类别 | 指标 | 目标值 | 验证方式 |
| ---- | ---- | ------ | -------- |
| **指令解析** | 简单控制准确率 | ≥ 95% | 内部测试集（≥ 100 条） |
|  | 复合意图拆解 | ≥ 80% | 内部测试集（≥ 50 条） |
| **写操作安全** | 高风险误执行率 | = 0 | 自动化用例 |
|  | 审计完整性 | 100%（每个写操作可由 `run_id` 串联） | 审计文件抽检 |
| **长对话** | 持续轮数（无溢出） | ≥ 200 轮 | 自动化压测 |
|  | 压缩后信息保留率 | ≥ 95%（人评） | 摘要-原文对比 |
| **边缘推理** | 首次 token 延迟 | < 1.5s | `scripts/bench_edge.py` |
|  | 持续生成速度 | ≥ 8 tokens/s | 同上 |
|  | 显存占用 | < 4GB（INT4） | `nvidia-smi` |
|  | 模型启动时间 | < 30s | 冷启动计时 |
| **离线可用** | 断外网后所有功能 | 100% 可用 | 物理断网测试 |
| **并发安全** | 同一会话并发请求 | 100% 拒绝 / 排队 | 并发压测 |
| **多家庭隔离** | 跨家庭数据访问 | 0 泄漏 | 自动化用例 |
| **审批有效** | 过期审批自动拒绝 | 100% | 边界时间测试 |

---

### 3.3 计划和分工

#### 3.3.1 整体排期

| 阶段 | 周次 | 关键任务 | 交付物 |
| ---- | ---- | -------- | ------ |
| **M1：需求与设计** | W1–W2 | 完善赛题场景、核心叙事；细化四大创新的技术指标 | 设计稿 v1.0、评测集初稿 |
| **M2：模型边缘部署** | W3–W5 | 选型 MiniCPM-1B / Phi-3.5-mini；INT4 量化；llama.cpp / vLLM 部署；接入 OpenAI 兼容端点 | 边缘运行 demo、性能基线 |
| **M3：后端深化** | W6–W9 | 完善压缩链路（双路径 / 迭代 / 分支）；完善会话树（fork / lane / record）；完善风险分级（场景展开 / 冲突检测）；补全审计 | 单元测试 ≥ 90% 覆盖 |
| **M4：前端深化** | W10–W11 | 审批卡片（高风险详情可视化）；自动化管理 UI；树视图（分支切换 + 摘要展示） | UI 联调 demo |
| **M5：联调与压测** | W12–W14 | 端到端联调；长对话压测；并发压测；离线运行验证 | 压测报告、问题清单 |
| **M6：边缘真实环境** | W15–W16 | Jetson 实测性能；真实设备接入（≥ 1 类）；断网测试 | 边缘运行报告 |
| **M7：文档与答辩** | W17–W18 | 项目文档定稿；演示视频（5–8 min）；答辩准备 | 最终提交包 |

#### 3.3.2 分工

| 角色 | 人数 | 主要职责 | 关键产出 |
| ---- | ---- | -------- | -------- |
| **大模型 / Agent** | 2 | 模型适配（OpenAI 兼容）、压缩链路（双路径 / 迭代 / 分支 / 文件跟踪）、风险分级 + 场景展开 + 冲突检测、子 Agent 编排 | `app/agents/`、`app/compaction/`、`docs/compaction-tech-detail.md`（新增） |
| **后端工程** | 2 | FastAPI 路由、SQLAlchemy 迁移、LangGraph 状态机、SSE 流式、鉴权、限流、审计、JWT、多家庭隔离 | `app/api/`、`app/services/`、`tests/` |
| **前端工程** | 1 | Vue 3 + TS 组件（Chat / 审批 / 自动化 / 树视图）、Pinia store、SSE 解析、UI/UX | `smarthome-web/` |
| **边缘部署 / 硬件** | 1 | Jetson Orin Nano 适配、模型 INT4 量化、推理引擎选型（llama.cpp / vLLM / TensorRT-LLM）、性能基准、真实设备接入 | `scripts/bench_edge.py`、《边缘运行报告》 |

#### 3.3.3 风险与应对

| 风险 | 概率 | 影响 | 应对 |
| ---- | ---- | ---- | ---- |
| 1B 模型工具调用能力弱 | 中 | 高 | 启动时 `bind_tools` 校验，不支持立即降级到「无工具 + 仅对话」模式 |
| 1B 模型压缩摘要质量差 | 中 | 中 | 提示词强化 + 必要时引入「先用规则模板生成初版、再用模型润色」双阶段 |
| Jetson 推理延迟不达标 | 中 | 中 | 切换到 TensorRT-LLM / vLLM；量化到 INT4；启用 continuous batching |
| 真实设备接入受限 | 中 | 低 | 模拟器 + 至少 1 类真实设备（如米家智能灯）即可 |
| 赛期进度 | — | — | M3 完成后评估；若压缩/风险分支有阻塞，优先保证原型可用 + 文档完整 |

---

## 4 参考资料

### 4.1 大赛与赛题

- 第八届中国研究生人工智能创新大赛，赛题一：生成式大语言模型与智能体

### 4.2 模型与推理引擎

- MiniCPM 官方仓库与说明：<https://github.com/OpenBMB/MiniCPM>
- Phi-3.5-mini 官方文档
- NVIDIA Jetson 官方文档：<https://developer.nvidia.com/embedded/jetson>
- TensorRT-LLM 官方仓库
- llama.cpp（CUDA 后端）官方仓库
- vLLM 官方仓库与 Jetson 移植指南

### 4.3 框架与库

- LangGraph 官方文档：<https://langchain-ai.github.io/langgraph/>
- LangChain 官方文档
- FastAPI 官方文档
- SQLAlchemy 2.x 官方文档
- Vue 3 官方文档
- Pinia 官方文档

### 4.4 开源参考实现

- Pi（mono）开源 AI Agent：会话树形存储 + 上下文压缩设计（参考实现）
- LangGraph 内置 SqliteSaver / PostgresSaver（对比参考）
- MemGPT / Letta（对比参考）

### 4.5 项目内文档

- `README.md`（项目主说明 + 核心亮点）
- `docs/session-tree-storage.md`（会话树存储模块详细文档）
- `docs/session-tree-compaction-review.md`（会话树与上下文压缩实现评价）
- `docs/funnel-routing-architecture.md`（漏斗式分层路由架构）
- `docs/sub-agent-design.md`（子 Agent 设计）
- `docs/frontend-data-sources.md`、`docs/frontend-driven-agent-gap-analysis.md`（前端数据源与 Agent 差距分析）
- `app/session_tree/`（会话树实现，4 层架构）
- `app/compaction/`（上下文压缩编排）
- `app/agents/`（Agent 引擎：图、风险、审计、租约、工具）

---

> 文档结束。如对内容有疑问或希望补充特定模块的更多细节，请联系项目团队。
