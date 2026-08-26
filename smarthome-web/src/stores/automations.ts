import { computed, reactive, ref, watch } from "vue";
import { defineStore } from "pinia";
import {
    listAutomations as apiListAutomations,
    createAutomation as apiCreateAutomation,
    updateAutomation as apiUpdateAutomation,
    deleteAutomation as apiDeleteAutomation,
    toggleAutomationEnabled as apiToggleEnabled,
    executeAutomation as apiExecuteAutomation,
    batchEnableAutomations as apiBatchEnable,
    batchSetAutomationSchedule as apiBatchSchedule,
    getAutomation as apiGetAutomation,
    listAutomationExecutions as apiListExecutions,
} from "../api/automation";
import type {
    AutomationCreate,
    AutomationRule,
    AutomationSummary,
    AutomationUpdate,
    ExecutionRecord,
} from "../types/automation";
import type { LoadingState } from "../types/loading";
import { useHouseholdStore } from "./households";
import { sleep } from "../utils/async";

// === 自动化流程步骤 ===

export type AutomationStepStatus = "pending" | "running" | "completed";

export interface AutomationStep {
    id: string;
    name: string;
    description: string;
    icon: string;
    tone: string;
    /** 来自 AI 推荐的绑定（多设备并行 action 时全部标记为 true） */
    aiBound?: boolean;
}

/** 前端展示用的自动化规则模型 */
export interface AutomationDisplayRule {
    id: number;
    name: string;
    description: string;
    trigger: string;
    devices: number;
    icon: string;
    tone: string;
    enabled: boolean;
}

export interface AutomationFilters {
    keyword: string;
    triggerType: string;
    enabled: "all" | "true" | "false";
}

export interface AutomationInput {
    name: string;
    description: string;
    trigger: string;
    deviceIds: number[];
    rooms: string[];
    delay: number;
    note: string;
}

/** 触发类型映射：后端 triggerType → 前端显示文字 / 图标 / 色调 */
const TRIGGER_TYPE_MAP: Record<
    string,
    { label: string; icon: string; tone: string }
> = {
    location: { label: "位置触发", icon: "location", tone: "blue" },
    schedule: { label: "时间触发", icon: "clock", tone: "purple" },
    device: { label: "设备状态", icon: "sensor", tone: "orange" },
    manual: { label: "手动触发", icon: "automation", tone: "green" },
};

const DEFAULT_TRIGGER_META = { label: "手动触发", icon: "automation", tone: "blue" };

/** 触发显示标签 → 图标/色调 */
const TRIGGER_DISPLAY_META: Record<string, { icon: string; tone: string }> = {
    "设备状态变化": { icon: "sensor", tone: "orange" },
    "位置触发": { icon: "location", tone: "blue" },
    "时间触发": { icon: "clock", tone: "purple" },
    "设备状态": { icon: "sensor", tone: "orange" },
    "手动触发": { icon: "automation", tone: "green" },
};

/** 模板规则池：导入与推荐模板共用 */
const TEMPLATE_POOL: Array<Omit<AutomationDisplayRule, "id" | "enabled">> = [
    { name: "夜间安防", description: "夜间自动布防与照明联动", trigger: "时间触发", devices: 6, icon: "security", tone: "purple" },
    { name: "晨间唤醒", description: "灯光、窗帘、空调联动唤醒", trigger: "时间触发", devices: 5, icon: "illumination", tone: "orange" },
    { name: "节能回家", description: "节能模式 + 舒适回家流程", trigger: "位置触发", devices: 7, icon: "home", tone: "green" },
    { name: "影院模式", description: "一键开启影院灯光与音响", trigger: "设备状态", devices: 4, icon: "automation", tone: "blue" },
];

/** 将后端规则列表项转为前端展示模型 */
const toDisplayRule = (item: {
    id: number;
    name: string;
    description: string;
    triggerType: string;
    enabled: boolean;
    deviceCount: number;
}): AutomationDisplayRule => {
    const meta = TRIGGER_TYPE_MAP[item.triggerType] ?? DEFAULT_TRIGGER_META;
    return {
        id: item.id,
        name: item.name,
        description: item.description,
        trigger: meta.label,
        devices: item.deviceCount,
        icon: meta.icon,
        tone: meta.tone,
        enabled: item.enabled,
    };
};

/** 根据规则生成流程步骤：触发条件 + 设备动作 */
export const buildAutomationSteps = (
    rule: AutomationDisplayRule,
    detail?: AutomationRule | null,
    aiBoundPositions: number[] = [],
): AutomationStep[] => {
    const trigger = TRIGGER_DISPLAY_META[rule.trigger] ?? { icon: "automation", tone: "blue" };
    const triggerConfig = detail?.triggers[0]?.config ?? {};
    const steps: AutomationStep[] = [{
        id: `trigger-${rule.id}`,
        name: rule.trigger,
        description: String(triggerConfig.description ?? rule.description),
        icon: trigger.icon,
        tone: trigger.tone,
    }];
    const aiBoundSet = new Set(aiBoundPositions);
    detail?.actions.forEach((action, index) => {
        const config = action.config;
        steps.push({
            id: `action-${rule.id}-${index}`,
            name: String(config.name ?? config.command ?? `执行动作 ${index + 1}`),
            description: String(config.deviceName ?? config.description ?? `设备 #${action.deviceId ?? "未指定"}`),
            icon: "device-management",
            tone: index % 2 ? "teal" : "orange",
            aiBound: aiBoundSet.has(index),
        });
    });
    return steps;
};

// === 自动化 Store ===

export const useAutomationsStore = defineStore("automations", () => {
    const householdStore = useHouseholdStore();

    /** AI 生成的推荐模板，默认未加载；被 loadAiTemplates 填充 */
    const aiTemplates = ref<Array<Omit<AutomationDisplayRule, "id" | "enabled">>>([]);

    /**
     * 根据 AI 项的 device_type / room 提示从用户设备列表中匹配真实 device_id 列表。
     * 匹配顺序：
     * 1. 精确匹配：type + room 完全一致
     * 2. 模糊匹配：type + room includes
     * 3. 同 type 在线的设备
     * 4. 任意同 type 设备
     * 全部为空则返回 null，调用方将 action 标为 unresolved。
     */
    const resolveDeviceIds = (
        deviceType: string | null,
        room: string | null,
        devices: ReadonlyArray<{
            id: string | number;
            type?: string;
            room?: string;
            status?: string;
        }>,
    ): number[] => {
        if (!deviceType) return [];
        const list = devices
            .map((d) => ({
                id: typeof d.id === "string" ? Number(d.id) : d.id,
                type: d.type,
                room: d.room,
                online: d.status !== "offline",
            }))
            .filter((d) => Number.isFinite(d.id) && d.type === deviceType);
        if (list.length === 0) return [];
        if (room) {
            const exact = list.filter((d) => d.room === room);
            if (exact.length > 0) return exact.map((d) => Number(d.id));
            const fuzzy = list.filter((d) => d.room?.includes(room));
            if (fuzzy.length > 0) return fuzzy.map((d) => Number(d.id));
        }
        const online = list.filter((d) => d.online);
        if (online.length > 0) return online.map((d) => Number(d.id));
        return list.map((d) => Number(d.id));
    };
    /**
     * AI 模板的原始 payload（name → 解析后的 triggers/actions）。
     * 用于 useTemplate 时传递真实 device_id 提交到后端。
     */
    const aiTemplatePayloads = ref<
        Map<
            string,
            {
                triggers: Array<{ type: string; config: Record<string, unknown> }>;
                actions: Array<{
                    type: "device_command";
                    position: number;
                    deviceId: number | null;
                    config: Record<string, unknown>;
                    resolved: boolean;
                }>;
            }
        >
    >(new Map());
    const aiTemplatesLoading = ref(false);
    const aiTemplatesError = ref<string | null>(null);
    let aiTemplatesAbort: AbortController | null = null;
    /**
     * AI 创建后记录的"AI 绑定”映射。ruleId → 该规则中被 AI 透传绑定的 action positions。
     * 供 buildAutomationSteps 在生成步骤时标记 aiBound。
     */
    const aiTemplateBindings = ref<Record<number, number[]>>({});

    /**
     * 后台加载 AI 推荐模板。
     * - 任意环节失败保留 TEMPLATE_POOL 兏底（调用方应使用 displayTemplates）。
     * - 重复调用自动取消上一次请求。
     */
    const loadAiTemplates = async (count = 6, force = false) => {
        aiTemplatesAbort?.abort();
        const controller = new AbortController();
        aiTemplatesAbort = controller;
        aiTemplatesLoading.value = true;
        aiTemplatesError.value = null;
        try {
            // 从 home store 取设备列表（避免重复拉取）。home store 的 devices 是 computed
            const { useHomeStore } = await import("./home");
            const homeStore = useHomeStore();
            const devices = homeStore.devices.map((d) => ({
                type: d.type,
                status: d.status,
            }));
            const { buildDeviceSummary } = await import("../types/deviceSummary");
            const summary = buildDeviceSummary(devices);
            const { fetchAiAutomationTemplates } = await import("../api/automationTemplates");
            const items = await fetchAiAutomationTemplates(summary, count, {
                force,
                signal: controller.signal,
            });
            aiTemplates.value = items.map((item) => ({
                name: item.name,
                description: item.description,
                trigger: TRIGGER_TYPE_MAP[item.trigger_type]?.label ?? item.trigger_type,
                devices: item.device_count,
                icon: item.icon || "automation",
                tone: item.tone,
            }));
            // 同时取全量设备用于解析（包含 id/room/status）
            const { useHomeStore: useHomeStore2 } = await import("./home");
            const fullDevices = useHomeStore2().devices;
            const payloadMap = new Map<
                string,
                {
                    triggers: Array<{ type: string; config: Record<string, unknown> }>;
                    actions: Array<{
                        type: "device_command";
                        position: number;
                        deviceId: number | null;
                        config: Record<string, unknown>;
                        resolved: boolean;
                    }>;
                }
            >();
            for (const item of items) {
                const triggers = item.triggers.map((t) => ({
                    type: t.type,
                    config: t.config ?? {},
                }));
                // 多设备并行：LLM 给一个语义提示，可能匹配多台同 type 设备。
                // 每台设备拆为一条独立 action，后端按 position 顺序并行执行。
                // 上限 49（后端 AutomationCreate.actions max=50）保留一条兏底位。
                let pos = 0;
                const actions: Array<{
                    type: "device_command";
                    position: number;
                    deviceId: number | null;
                    config: Record<string, unknown>;
                    resolved: boolean;
                }> = [];
                let truncated = false;
                for (const a of item.actions) {
                    if (actions.length >= 49) {
                        truncated = true;
                        break;
                    }
                    const deviceIds = resolveDeviceIds(
                        a.device_type ?? null,
                        a.room ?? null,
                        fullDevices,
                    );
                    if (deviceIds.length === 0) {
                        actions.push({
                            type: "device_command",
                            position: pos++,
                            deviceId: null,
                            config: a.config ?? {},
                            resolved: false,
                        });
                    } else {
                        for (const id of deviceIds) {
                            if (actions.length >= 49) {
                                truncated = true;
                                break;
                            }
                            actions.push({
                                type: "device_command",
                                position: pos++,
                                deviceId: id,
                                config: a.config ?? {},
                                resolved: true,
                            });
                        }
                        if (truncated) break;
                    }
                }
                payloadMap.set(item.name, { triggers, actions });
                if (truncated) {
                    console.warn(
                        `[ai-templates] 模板“${item.name}”的动作数量超过上限 49，已截断`,
                    );
                }
            }
            aiTemplatePayloads.value = payloadMap;
        } catch (error) {
            if ((error as { name?: string })?.name === "AbortError") return;
            aiTemplates.value = [];
            aiTemplatePayloads.value = new Map();
            aiTemplatesError.value =
                error instanceof Error ? error.message : "AI 模板生成失败";
        } finally {
            if (aiTemplatesAbort === controller) {
                aiTemplatesAbort = null;
                aiTemplatesLoading.value = false;
            }
        }
    };

    /** 取消进行中的 AI 模板请求。 */
    const cancelAiTemplates = () => {
        aiTemplatesAbort?.abort();
        aiTemplatesAbort = null;
        aiTemplatesLoading.value = false;
    };

    /** 展示用模板列表：优先使用 AI 生成结果，未加载时回退到本地 TEMPLATE_POOL */
    const displayTemplates = computed<
        Array<Omit<AutomationDisplayRule, "id" | "enabled">>
    >(() => (aiTemplates.value.length > 0 ? aiTemplates.value : TEMPLATE_POOL));

    const requireHouseholdId = () => {
        const id = householdStore.activeHouseholdId;
        if (!id) {
            throw new Error("请先创建或选择家庭");
        }
        return id;
    };

    const filters = reactive<AutomationFilters>({
        keyword: "",
        triggerType: "",
        enabled: "all",
    });
    const automations = ref<AutomationDisplayRule[]>([]);
    const loading = ref<LoadingState>("idle");
    const runningId = ref<number | null>(null);
    const selectedId = ref<number | null>(null);
    const selectedDetail = ref<AutomationRule | null>(null);
    const executions = ref<ExecutionRecord[]>([]);
    const backendSummary = ref<AutomationSummary | null>(null);
    const stepStatuses = ref<Record<string, AutomationStepStatus>>({});

    const selectedAutomation = computed(() =>
        selectedId.value
            ? (automations.value.find((item) => item.id === selectedId.value) ?? null)
            : null,
    );

    const visible = computed(() =>
        automations.value.filter(
            (item) =>
                item.name.includes(filters.keyword.trim()) &&
                (!filters.triggerType || item.trigger === filters.triggerType) &&
                (filters.enabled === "all" ||
                    String(item.enabled) === filters.enabled),
        ),
    );

    const stats = computed(() => backendSummary.value ?? ({
        enabled: 0, total: 0, running: 0, executionsToday: 0, abnormal: 0,
    }));

    const resetStepStatuses = () => {
        const rule = selectedAutomation.value;
        if (!rule) {
            stepStatuses.value = {};
            return;
        }
        const aiPositions = aiTemplateBindings.value[rule.id] ?? [];
        stepStatuses.value = buildAutomationSteps(
            rule,
            selectedDetail.value,
            aiPositions,
        ).reduce<Record<string, AutomationStepStatus>>(
            (record, step) => {
                record[step.id] = "pending";
                return record;
            },
            {},
        );
    };

    const loadSelectedAutomation = async () => {
        if (!selectedId.value) {
            selectedDetail.value = null;
            executions.value = [];
            return;
        }
        const ruleId = selectedId.value;
        const [detail, history] = await Promise.all([
            apiGetAutomation(ruleId),
            apiListExecutions(ruleId, { pageSize: 10 }),
        ]);
        if (selectedId.value !== ruleId) return;
        selectedDetail.value = detail;
        executions.value = history.items;
        resetStepStatuses();
    };

    const loadAutomations = async () => {
        loading.value = "loading";
        try {
            const householdId = householdStore.activeHouseholdId;
            if (!householdId) {
                automations.value = [];
                backendSummary.value = null;
                selectedId.value = null;
                selectedDetail.value = null;
                executions.value = [];
                resetStepStatuses();
                loading.value = "success";
                return;
            }
            const result = await apiListAutomations(householdId, {
                keyword: filters.keyword || undefined,
                triggerType: filters.triggerType || undefined,
                enabled:
                    filters.enabled === "all"
                        ? undefined
                        : filters.enabled === "true",
            });
            automations.value = result.items.map(toDisplayRule);
            backendSummary.value = result.summary;
            if (
                !selectedId.value ||
                !automations.value.some((item) => item.id === selectedId.value)
            ) {
                selectedId.value = automations.value[0]?.id ?? null;
            }
            resetStepStatuses();
            await loadSelectedAutomation();
            loading.value = "success";
        } catch (error) {
            loading.value = "error";
            throw error;
        }
    };

    watch(
        () => householdStore.activeHouseholdId,
        () => {
            if (householdStore.loadedOnce) {
                void loadAutomations().catch(() => undefined);
            }
        },
    );

    const selectAutomation = (ruleId: number) => {
        selectedId.value = ruleId;
        selectedDetail.value = null;
        executions.value = [];
        resetStepStatuses();
        void loadSelectedAutomation().catch(() => undefined);
    };

    const setAutomationEnabled = async (ruleId: number, enabled: boolean) => {
        const rule = automations.value.find((item) => item.id === ruleId);
        if (rule) rule.enabled = enabled;
        try {
            await apiToggleEnabled(ruleId, enabled);
            if (backendSummary.value) backendSummary.value.enabled += enabled ? 1 : -1;
        } catch (error) {
            if (rule) rule.enabled = !enabled;
            throw error;
        }
    };

    const runAutomation = async (rule: AutomationDisplayRule) => {
        if (!rule.enabled) throw new Error("自动化规则已停用");
        runningId.value = rule.id;
        selectedId.value = rule.id;
        resetStepStatuses();
        try {
            const next = { ...stepStatuses.value };
            const aiPositions = aiTemplateBindings.value[rule.id] ?? [];
            for (const step of buildAutomationSteps(rule, selectedDetail.value, aiPositions)) {
                next[step.id] = "running";
                stepStatuses.value = next;
                await sleep(220);
                next[step.id] = "completed";
                stepStatuses.value = next;
            }
            await apiExecuteAutomation(rule.id);
            await loadSelectedAutomation();
            await loadAutomations();
        } finally {
            runningId.value = null;
        }
    };

    const addAutomation = async (payload: AutomationInput) => {
        const meta = Object.entries(TRIGGER_TYPE_MAP).find(
            ([, v]) => v.label === payload.trigger,
        );
        const createPayload: AutomationCreate = {
            name: payload.name,
            description: payload.description,
            triggers: [{ type: payload.trigger === "设备状态变化" ? "device" : meta?.[0] ?? "manual", config: {} }],
            actions: payload.deviceIds.map((deviceId, position) => ({
                type: "device_command", position, deviceId,
                config: { command: "turn_on" },
            })),
            delaySeconds: payload.delay,
            note: payload.note || payload.rooms.join("、"),
        };
        const created = await apiCreateAutomation(requireHouseholdId(), createPayload);
        const rule = toDisplayRule(created);
        automations.value.unshift(rule);
        selectedId.value = rule.id;
        resetStepStatuses();
        return rule;
    };

    const updateAutomation = async (
        rule: AutomationDisplayRule,
        payload: AutomationInput,
    ) => {
        const meta = Object.entries(TRIGGER_TYPE_MAP).find(
            ([, v]) => v.label === payload.trigger,
        );
        const updatePayload: AutomationUpdate = {
            name: payload.name,
            description: payload.description,
            triggers: [{ type: payload.trigger === "设备状态变化" ? "device" : meta?.[0] ?? "manual", config: {} }],
            actions: payload.deviceIds.map((deviceId, position) => ({
                type: "device_command", position, deviceId,
                config: { command: "turn_on" },
            })),
            delaySeconds: payload.delay,
            note: payload.note || payload.rooms.join("、"),
        };
        const updated = await apiUpdateAutomation(rule.id, updatePayload);
        Object.assign(rule, {
            name: updated.name,
            description: updated.description,
        });
        // 编辑后原 AI 绑定的 position 不再可靠，清理该规则的 bindings。
        if (aiTemplateBindings.value[rule.id]) {
            const { [rule.id]: _removed, ...rest } = aiTemplateBindings.value;
            void _removed;
            aiTemplateBindings.value = rest;
        }
        resetStepStatuses();
        return rule;
    };

    const removeAutomation = async (rule: AutomationDisplayRule) => {
        await apiDeleteAutomation(rule.id);
        if (aiTemplateBindings.value[rule.id]) {
            const { [rule.id]: _removed, ...rest } = aiTemplateBindings.value;
            void _removed;
            aiTemplateBindings.value = rest;
        }
        await loadAutomations();
    };

    const duplicateAutomation = async (rule: AutomationDisplayRule) => {
        const createPayload: AutomationCreate = {
            name: `${rule.name} 副本`,
            description: rule.description,
            triggers: [{ type: "manual", config: {} }],
            actions: [{ type: "device_command", position: 0, deviceId: null, config: {} }],
        };
        const created = await apiCreateAutomation(requireHouseholdId(), createPayload);
        const copy = toDisplayRule(created);
        copy.name = `${rule.name} 副本`;
        automations.value.unshift(copy);
        selectedId.value = copy.id;
        resetStepStatuses();
        return copy;
    };

    const importRules = async (count: number) => {
        const householdId = requireHouseholdId();
        const created = await Promise.all(
            TEMPLATE_POOL.slice(0, count).map((template) =>
                apiCreateAutomation(householdId, {
                    name: template.name,
                    description: template.description,
                    triggers: [{ type: "manual", config: {} }],
                    actions: [{ type: "device_command", position: 0, deviceId: null, config: {} }],
                }),
            ),
        );
        const rules = created.map(toDisplayRule);
        if (!rules.length) return;
        automations.value.unshift(...rules);
        selectedId.value = rules[0]?.id ?? selectedId.value;
        resetStepStatuses();
    };

    /**
     * 根据名称查找模板 payload（优先 AI 生成，兏底本地 TEMPLATE_POOL）。
     * 返回 null 时调用方应报“未找到模板”。
     */
    const findTemplatePayload = (
        name: string,
    ): {
        name: string;
        description: string;
        triggers: Array<{ type: string; config: Record<string, unknown> }>;
        actions: Array<{
            type: "device_command";
            position: number;
            deviceId: number | null;
            config: Record<string, unknown>;
        }>;
    } | null => {
        const aiPayload = aiTemplatePayloads.value.get(name);
        if (aiPayload) {
            return {
                name,
                description:
                    aiTemplates.value.find((item) => item.name === name)?.description ??
                    "",
                triggers: aiPayload.triggers,
                actions: aiPayload.actions.map((a) => ({
                    type: a.type,
                    position: a.position,
                    deviceId: a.deviceId,
                    config: a.config,
                })),
            };
        }
        const local = TEMPLATE_POOL.find((item) => item.name === name) ?? TEMPLATE_POOL[0];
        if (!local) return null;
        return {
            name: local.name,
            description: local.description,
            triggers: [{ type: "manual", config: {} }],
            actions: [
                { type: "device_command", position: 0, deviceId: null, config: {} },
            ],
        };
    };

    /**
     * 使用模板创建规则：
     * - AI 项：透传 triggers + actions（已解析 deviceId）
     * - 本地项：兑底为 manual + 空 action
     * - AI 项中可能存在 unresolved action（deviceId=null），后端会 422。
     *   为避免创建失败，将这些 action 过滤为 “待绑定” 提示。
     */
    const useTemplate = async (name: string) => {
        const payload = findTemplatePayload(name);
        if (!payload) throw new Error("未找到对应模板");
        const aiPayload = aiTemplatePayloads.value.get(name);
        const unresolvedCount = aiPayload
            ? aiPayload.actions.filter((a) => a.deviceId === null).length
            : 0;
        // 记录哪些原始 position 是 AI 透传并成功绑定的，后续按 position 标记 aiBound。
        const aiResolvedPositions = aiPayload
            ? aiPayload.actions
                  .filter((a) => a.deviceId !== null)
                  .map((a) => a.position)
            : [];
        // 过滤掉未解析的 action，避免后端 422；同时保证至少一条 action。
        const safeActions = payload.actions.filter(
            (action) => action.deviceId !== null,
        );
        if (safeActions.length === 0) {
            safeActions.push({
                type: "device_command",
                position: 0,
                deviceId: null,
                config: {},
            });
        }
        // 为保持后端 position 与 AI 原始 position 一致，取所有原始 position 的最小
        // 并重新连续编号。aiResolvedPositions 重新映射到新的连续 position。
        const finalPayload = {
            ...payload,
            actions: safeActions.map((a, idx) => ({ ...a, position: idx })),
        };
        const created = await apiCreateAutomation(requireHouseholdId(), finalPayload);
        const rule = toDisplayRule(created);
        automations.value.unshift(rule);
        selectedId.value = rule.id;
        resetStepStatuses();
        // AI 项中成功绑定的设备原本可能是从不同原始 position 展开的多台设备，
        // 这里统一记为后端实际提交的所有 position （除兑底位）。
        if (aiPayload && aiResolvedPositions.length > 0) {
            const boundPositions = safeActions
                .map((a, idx) => idx)
                .filter((idx) => idx < safeActions.length - 1 || safeActions.length === 1);
            aiTemplateBindings.value = {
                ...aiTemplateBindings.value,
                [rule.id]: boundPositions,
            };
        }
        return { ...rule, unresolved: unresolvedCount };
    };

    const batchSetEnabled = async (ruleIds: number[], enabled: boolean) => {
        await apiBatchEnable({
            ruleIds: ruleIds.length ? ruleIds : automations.value.map((item) => item.id),
            executeNow: false,
        });
        const targets = ruleIds.length ? ruleIds : automations.value.map((item) => item.id);
        automations.value.forEach((rule) => {
            if (targets.includes(rule.id)) rule.enabled = enabled;
        });
    };

    const batchSetSchedule = async (
        ruleIds: number[],
        schedule: { weekdays: number[]; time: string },
    ) => {
        await apiBatchSchedule({
            ruleIds: ruleIds.length ? ruleIds : automations.value.map((item) => item.id),
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            time: schedule.time,
            weekdays: schedule.weekdays,
            frequency: "daily",
        });
        const targets = ruleIds.length ? ruleIds : automations.value.map((item) => item.id);
        const days = schedule.weekdays.length ? `每周 ${schedule.weekdays.length} 天` : "每天";
        automations.value.forEach((rule) => {
            if (targets.includes(rule.id)) {
                rule.trigger = "时间触发";
                rule.description = `时间触发 · ${schedule.time} · ${days}`;
            }
        });
        resetStepStatuses();
    };

    return {
        filters,
        loading,
        automations,
        runningId,
        selectedId,
        selectedAutomation,
        selectedDetail,
        executions,
        stepStatuses,
        visible,
        stats,
        loadAutomations,
        loadSelectedAutomation,
        selectAutomation,
        setAutomationEnabled,
        runAutomation,
        addAutomation,
        updateAutomation,
        removeAutomation,
        duplicateAutomation,
        importRules,
        useTemplate,
        batchSetEnabled,
        batchSetSchedule,
        resetStepStatuses,
        aiTemplates,
        aiTemplatesLoading,
        aiTemplatesError,
        aiTemplatePayloads,
        aiTemplateBindings,
        loadAiTemplates,
        cancelAiTemplates,
        displayTemplates,
    };
});
