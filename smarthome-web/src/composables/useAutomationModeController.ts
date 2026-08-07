import { ref } from "vue";
import { ElMessage } from "element-plus";
import type {
    AutomationDisplayRule,
    useAutomationsStore,
} from "../stores/automations";

type AutomationsStore = ReturnType<typeof useAutomationsStore>;
type AutomationRule = AutomationDisplayRule;
type DialogKey = "create" | "edit" | "import" | "logs" | "schedule" | "batch";
type QuickActionKey = "batch" | "schedule" | "sort" | "logs";

export const useAutomationModeController = (store: AutomationsStore) => {
    const activeDialog = ref<DialogKey | null>(null);
    const deleteDialogOpen = ref(false);
    const deleting = ref(false);
    const deletingRule = ref<AutomationRule | null>(null);

    // ── 对话框开关 ──────────────────────────────────────────────────────────────

    const openCreateDialog = () => {
        activeDialog.value = "create";
    };

    const openEditDialog = (rule: AutomationRule) => {
        store.selectAutomation(rule.id);
        activeDialog.value = "edit";
    };

    const openImportDialog = () => {
        activeDialog.value = "import";
    };

    const openLogsDialog = () => {
        activeDialog.value = "logs";
    };

    const openScheduleDialog = () => {
        activeDialog.value = "schedule";
    };

    const openBatchDialog = () => {
        activeDialog.value = "batch";
    };

    // ── 创建 / 编辑 ─────────────────────────────────────────────────────────────

    const saveRule = async (payload: {
        mode: "create" | "edit";
        name: string;
        description: string;
        trigger: string;
    }) => {
        try {
            if (payload.mode === "edit") {
                const rule = store.selectedAutomation;
                if (!rule) return;
                await store.updateAutomation(rule, payload);
                ElMessage.success("规则已保存");
            } else {
                const rule = await store.addAutomation(payload);
                ElMessage.success(`自动化“${rule.name}”已创建`);
            }
        } catch (error) {
            ElMessage.error(error instanceof Error ? error.message : "保存失败");
        }
    };

    // ── 删除 ────────────────────────────────────────────────────────────────────

    const removeRule = (rule: AutomationRule) => {
        deletingRule.value = rule;
        deleteDialogOpen.value = true;
    };

    const cancelRemoveRule = () => {
        if (deleting.value) return;
        deleteDialogOpen.value = false;
        deletingRule.value = null;
    };

    const confirmRemoveRule = async () => {
        if (!deletingRule.value) return;
        const rule = deletingRule.value;
        deleting.value = true;
        try {
            await store.removeAutomation(rule);
            ElMessage.success(`${rule.name} 已删除`);
            deleteDialogOpen.value = false;
            deletingRule.value = null;
        } catch (error) {
            ElMessage.error(
                error instanceof Error ? error.message : "自动化删除失败",
            );
        } finally {
            deleting.value = false;
        }
    };

    // ── 复制 / 执行 / 启停 ───────────────────────────────────────────────────────

    const copyRule = async (rule: AutomationRule) => {
        try {
            await store.duplicateAutomation(rule);
            ElMessage.success(`${rule.name} 已复制`);
        } catch (error) {
            ElMessage.error(
                error instanceof Error ? error.message : "自动化复制失败",
            );
        }
    };

    const runRule = async (rule: AutomationRule) => {
        try {
            await store.runAutomation(rule);
            ElMessage.success(`“${rule.name}”执行成功`);
        } catch (error) {
            ElMessage.error(
                error instanceof Error ? error.message : "自动化执行失败",
            );
        }
    };

    const toggleRule = async (rule: AutomationRule, enabled: boolean) => {
        try {
            await store.setAutomationEnabled(rule.id, enabled);
            ElMessage.success(`${rule.name} ${enabled ? "已启用" : "已停用"}`);
        } catch (error) {
            ElMessage.error(
                error instanceof Error ? error.message : "自动化状态更新失败",
            );
        }
    };

    // ── 导入 / 批量操作 ──────────────────────────────────────────────────────────

    const importRules = async (count: number) => {
        try {
            await store.importRules(count);
            ElMessage.success(`已导入 ${count} 条规则`);
        } catch (error) {
            ElMessage.error(
                error instanceof Error ? error.message : "规则导入失败",
            );
        }
    };

    const batchEnable = async (ruleIds: number[]) => {
        try {
            await store.batchSetEnabled(ruleIds, true);
            ElMessage.success(`已启用 ${ruleIds.length} 条规则`);
        } catch (error) {
            ElMessage.error(
                error instanceof Error ? error.message : "批量启用失败",
            );
        }
    };

    const scheduleRules = async (payload: {
        weekdays: number[];
        time: string;
        ruleIds: number[];
    }) => {
        try {
            await store.batchSetSchedule(payload.ruleIds, payload);
            ElMessage.success("定时设置已保存");
        } catch (error) {
            ElMessage.error(
                error instanceof Error ? error.message : "定时设置失败",
            );
        }
    };

    const useTemplate = async (name: string) => {
        try {
            const rule = await store.useTemplate(name);
            ElMessage.success(`模板“${rule.name}”已使用`);
        } catch (error) {
            ElMessage.error(
                error instanceof Error ? error.message : "模板使用失败",
            );
        }
    };

    const runAction = async (key: QuickActionKey) => {
        if (key === "batch") {
            openBatchDialog();
        } else if (key === "schedule") {
            openScheduleDialog();
        } else if (key === "sort") {
            ElMessage.success("自动化排序已更新");
        } else if (key === "logs") {
            openLogsDialog();
        }
    };

    return {
        activeDialog,
        deleteDialogOpen,
        deleting,
        deletingRule,
        openCreateDialog,
        openEditDialog,
        openImportDialog,
        openLogsDialog,
        openScheduleDialog,
        openBatchDialog,
        saveRule,
        removeRule,
        cancelRemoveRule,
        confirmRemoveRule,
        copyRule,
        runRule,
        toggleRule,
        importRules,
        batchEnable,
        scheduleRules,
        useTemplate,
        runAction,
    };
};
