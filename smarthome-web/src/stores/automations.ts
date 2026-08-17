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
    detail?.actions.forEach((action, index) => {
        const config = action.config;
        steps.push({
            id: `action-${rule.id}-${index}`,
            name: String(config.name ?? config.command ?? `执行动作 ${index + 1}`),
            description: String(config.deviceName ?? config.description ?? `设备 #${action.deviceId ?? "未指定"}`),
            icon: "device-management",
            tone: index % 2 ? "teal" : "orange",
        });
    });
    return steps;
};

// === 自动化 Store ===

export const useAutomationsStore = defineStore("automations", () => {
    const householdStore = useHouseholdStore();

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
        stepStatuses.value = rule
            ? buildAutomationSteps(rule, selectedDetail.value).reduce<Record<string, AutomationStepStatus>>(
                  (record, step) => {
                      record[step.id] = "pending";
                      return record;
                  },
                  {},
              )
            : {};
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

    // 切换活动家庭后，自动化列表随全局上下文同步刷新。
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
            // 乐观更新失败时回滚本地状态，避免 UI 与后端不一致
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
            for (const step of buildAutomationSteps(rule, selectedDetail.value)) {
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
        resetStepStatuses();
        return rule;
    };

    const removeAutomation = async (rule: AutomationDisplayRule) => {
        await apiDeleteAutomation(rule.id);
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

    const useTemplate = async (name: string) => {
        const template = TEMPLATE_POOL.find((item) => item.name === name) ?? TEMPLATE_POOL[0]!;
        const created = await apiCreateAutomation(requireHouseholdId(), {
            name: template.name,
            description: template.description,
            triggers: [{ type: "manual", config: {} }],
            actions: [{ type: "device_command", position: 0, deviceId: null, config: {} }],
        });
        const rule = toDisplayRule(created);
        automations.value.unshift(rule);
        selectedId.value = rule.id;
        resetStepStatuses();
        return rule;
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
    };
});
