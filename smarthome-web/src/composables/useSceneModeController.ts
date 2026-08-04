import { ref } from "vue";
import { ElMessage } from "element-plus";
import {
  confirmHighRiskScene,
  isHighRiskScene,
} from "../utils/sceneRiskPolicy";
import type { useScenesStore } from "../stores/scenes";
import type { Scene, SceneInput, SceneTemplate } from "../types/scene";

type ScenesStore = ReturnType<typeof useScenesStore>;
type QuickActionKey = "batch" | "schedule" | "sort" | "logs";

const quickActionMessages: Record<QuickActionKey, string> = {
  batch: "批量启用入口已预留",
  schedule: "定时设置入口已预留",
  sort: "场景排序入口已预留",
  logs: "场景日志入口已预留",
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

    const createScene = async (payload: SceneInput) => {
        try {
            const scene = await store.addScene(payload);
            ElMessage.success(`${scene.name} 已创建`);
        } catch (error) {
            ElMessage.error(error instanceof Error ? error.message : "场景创建失败");
        }
    };

    const saveDraft = async (payload: SceneInput) => {
        try {
            await store.saveDraft(payload);
            ElMessage.success("场景草稿已保存");
        } catch (error) {
            ElMessage.error(error instanceof Error ? error.message : "草稿保存失败");
        }
    };

    const importTemplate = async (template: SceneTemplate) => {
        try {
            await store.importTemplate(template);
            ElMessage.success(`${template.name} 已导入`);
        } catch (error) {
            ElMessage.error(error instanceof Error ? error.message : "模板导入失败");
        }
    };

    const editScene = (scene: Scene) => {
        ElMessage.info(`编辑 ${scene.name} 的入口已预留`);
    };

    const copyScene = async (scene: Scene) => {
        try {
            await store.duplicateScene(scene);
            ElMessage.success(`${scene.name} 已复制`);
        } catch (error) {
            ElMessage.error(error instanceof Error ? error.message : "场景复制失败");
        }
    };

    const runScene = async (scene: Scene) => {
        const confirmed = await confirmHighRiskScene(scene);

        if (!confirmed) {
            return;
        }

        try {
            await store.runScene(scene, isHighRiskScene(scene));
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
        ElMessage.info(quickActionMessages[key]);
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
        saveDraft,
        templateDialogOpen,
        toggleScene,
    };
};
