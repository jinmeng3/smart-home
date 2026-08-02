import { ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import type { useScenesStore } from "../stores/scenes";
import type { Scene, SceneTemplate } from "../types/scene";

type ScenesStore = ReturnType<typeof useScenesStore>;
type QuickActionKey = "batch" | "schedule" | "sort" | "logs";

const highRiskDeviceKeywords = ["lock", "camera"];

const isHighRiskScene = (scene: Scene) =>
    scene.id === "away" ||
    scene.steps.some((step) =>
        highRiskDeviceKeywords.some((keyword) => step.deviceId.includes(keyword)),
    );

const confirmHighRiskScene = async (scene: Scene) => {
    if (!isHighRiskScene(scene)) {
        return true;
    }

    try {
        await ElMessageBox.confirm(
            `${scene.name} 包含门锁或安防相关动作，确认执行？`,
            "高风险动作确认",
            {
                confirmButtonText: "确认执行",
                cancelButtonText: "取消",
                type: "warning",
            },
        );

        return true;
    } catch {
        return false;
    }
};

export const useSceneModeController = (store: ScenesStore) => {
    const createDialogOpen = ref(false);
    const templateDialogOpen = ref(false);

    const openCreateDialog = () => {
        createDialogOpen.value = true;
    };

    const openTemplateDialog = () => {
        templateDialogOpen.value = true;
    };

    const createScene = () => {
        ElMessage.success("场景已创建");
    };

    const importTemplate = (template: SceneTemplate) => {
        ElMessage.success(`${template.name} 已导入`);
    };

    const editScene = (scene: Scene) => {
        ElMessage.info(`编辑 ${scene.name} 的入口已预留`);
    };

    const copyScene = (scene: Scene) => {
        ElMessage.success(`${scene.name} 已复制`);
    };

    const runScene = async (scene: Scene) => {
        const confirmed = await confirmHighRiskScene(scene);

        if (!confirmed) {
            return;
        }

        try {
            await store.runScene(scene);
            ElMessage.success(`${scene.name} 执行成功`);
        } catch (error) {
            ElMessage.error(error instanceof Error ? error.message : "场景执行失败");
        }
    };

    const toggleScene = async (scene: Scene, enabled: boolean) => {
        try {
            await store.setSceneEnabled(scene.id, enabled);
            ElMessage.success(`${scene.name}${enabled ? "已启用" : "已停用"}`);
        } catch (error) {
            ElMessage.error(error instanceof Error ? error.message : "场景状态更新失败");
        }
    };

    const runAction = (key: QuickActionKey) => {
        const messages: Record<QuickActionKey, string> = {
            batch: "批量启用入口已预留",
            schedule: "定时设置入口已预留",
            sort: "场景排序入口已预留",
            logs: "场景日志入口已预留",
        };

        ElMessage.info(messages[key]);
    };

    return {
        copyScene,
        createDialogOpen,
        createScene,
        editScene,
        importTemplate,
        openCreateDialog,
        openTemplateDialog,
        runAction,
        runScene,
        templateDialogOpen,
        toggleScene,
    };
};
