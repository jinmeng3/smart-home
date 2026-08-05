import { computed, reactive, ref } from "vue";
import { defineStore } from "pinia";
import {
    listAutomations as apiListAutomations,
    createAutomation as apiCreateAutomation,
    updateAutomation as apiUpdateAutomation,
    toggleAutomationEnabled as apiToggleEnabled,
    executeAutomation as apiExecuteAutomation,
    batchEnableAutomations as apiBatchEnable,
    batchSetAutomationSchedule as apiBatchSchedule,
} from "../api/automation";
import type { AutomationCreate, AutomationUpdate } from "../types/automation";
import { sleep } from "../utils/async";

// ── 自动化流程步骤 ──────────────────────────────────────────────────────────────────

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
    "位置触发": { icon: "location", tone: "blue" },
    "时间触发": { icon: "clock", tone: "purple" },
    "设备状态": { icon: "sensor", tone: "orange" },
    "手动触发": { icon: "automation", tone: "green" },
};

/** 设备动作模板（按顺序生成执行步骤） */
const DEVICE_ACTIONS: Array<{
    icon: string;
    tone: string;
    name: string;
    description: string;
}> = [
    { icon: "light", tone: "orange", name: "打开灯光", description: "客厅灯、玄关灯" },
    { icon: "curtain", tone: "teal", name: "关闭窗帘", description: "客厅窗帘" },
    { icon: "air-conditioner", tone: "blue", name: "设置空调", description: "制冷 26°C" },
    { icon: "security", tone: "purple", name: "安防模式", description: "回家模式" },
];

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
export const buildAutomationSteps = (rule: AutomationDisplayRule): AutomationStep[] => {
    const trigger = TRIGGER_DISPLAY_META[rule.trigger] ?? { icon: "automation", tone: "blue" };
    const steps: AutomationStep[] = [
        {
            id: `trigger-${rule.id}`,
            name: rule.trigger,
            description: rule.description,
            icon: trigger.icon,
            tone: trigger.tone,
        },
    ];
    const count = Math.min(Math.max(rule.devices, 1), DEVICE_ACTIONS.length);
    DEVICE_ACTIONS.slice(0, count).forEach((action, index) => {
        steps.push({ id: `action-${rule.id}-${index}`, ...action });
    });
    return steps;
};

// ── 自动化 Store ────────────────────────────────────────────────────────────────────

export const useAutomationsStore = defineStore("automations", () => {
    const filters = reactive<AutomationFilters>({
        keyword: "",
        triggerType: "",
        enabled: "all",
    });
    const automations = ref<AutomationDisplayRule[]>([]);
    const loading = ref(false);
    const runningId = ref<number | null>(null);
    const selectedId = ref<number | null>(null);
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

    const stats = computed(() => ({
        enabled: automations.value.filter((item) => item.enabled).length,
        total: automations.value.length,
        running: runningId.value
            ? automations.value.filter((item) => item.id === runningId.value).length
            : 0,
        executionsToday: 36,
        abnormal: 1,
    }));

    const resetStepStatuses = () => {
        const rule = selectedAutomation.value;
        stepStatuses.value = rule
            ? buildAutomationSteps(rule).reduce<Record<string, AutomationStepStatus>>(
                  (record, step) => {
                      record[step.id] = "pending";
                      return record;
                  },
                  {},
              )
            : {};
    };

    const loadAutomations = async () => {
        loading.value = true;
        try {
            const result = await apiListAutomations(1, {
                keyword: filters.keyword || undefined,
                triggerType: filters.triggerType || undefined,
                enabled:
                    filters.enabled === "all"
                        ? undefined
                        : filters.enabled === "true",
            });
            automations.value = result.items.map(toDisplayRule);
            if (
                !selectedId.value ||
                !automations.value.some((item) => item.id === selectedId.value)
            ) {
                selectedId.value = automations.value[0]?.id ?? null;
            }
            resetStepStatuses();
        } finally {
            loading.value = false;
        }
    };

    const selectAutomation = (ruleId: number) => {
        selectedId.value = ruleId;
        resetStepStatuses();
    };

    const setAutomationEnabled = async (ruleId: number, enabled: boolean) => {
        await apiToggleEnabled(ruleId, enabled);
        const rule = automations.value.find((item) => item.id === ruleId);
        if (rule) rule.enabled = enabled;
    };

    const runAutomation = async (rule: AutomationDisplayRule) => {
        if (!rule.enabled) throw new Error("自动化规则已停用");
        runningId.value = rule.id;
        selectedId.value = rule.id;
        resetStepStatuses();
        try {
            const next = { ...stepStatuses.value };
            for (const step of buildAutomationSteps(rule)) {
                next[step.id] = "running";
                stepStatuses.value = next;
                await sleep(220);
                next[step.id] = "completed";
                stepStatuses.value = next;
            }
            await apiExecuteAutomation(rule.id);
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
            triggers: [{ type: meta?.[0] ?? "manual", config: {} }],
            actions: [{ type: "device_command", position: 0, deviceId: null, config: {} }],
        };
        const created = await apiCreateAutomation(1, createPayload);
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
            triggers: [{ type: meta?.[0] ?? "manual", config: {} }],
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
        // 后端没有 delete 前端用 PATCH 停用代替
        await apiToggleEnabled(rule.id, false);
        automations.value = automations.value.filter((item) => item.id !== rule.id);
        if (selectedId.value === rule.id) {
            selectedId.value = automations.value[0]?.id ?? null;
        }
        resetStepStatuses();
    };

    const duplicateAutomation = async (rule: AutomationDisplayRule) => {
        const createPayload: AutomationCreate = {
            name: `${rule.name} 副本`,
            description: rule.description,
            triggers: [{ type: "manual", config: {} }],
            actions: [{ type: "device_command", position: 0, deviceId: null, config: {} }],
        };
        const created = await apiCreateAutomation(1, createPayload);
        const copy = toDisplayRule(created);
        copy.name = `${rule.name} 副本`;
        automations.value.unshift(copy);
        selectedId.value = copy.id;
        resetStepStatuses();
        return copy;
    };

    const importRules = async (count: number) => {
        const created = await Promise.all(
            TEMPLATE_POOL.slice(0, count).map((template) =>
                apiCreateAutomation(1, {
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
        const created = await apiCreateAutomation(1, {
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
        stepStatuses,
        visible,
        stats,
        loadAutomations,
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