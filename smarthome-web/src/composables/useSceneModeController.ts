import { ref } from "vue";
import { ElMessage } from "element-plus";
import {
  confirmHighRiskScene,
  isHighRiskScene,
} from "../utils/sceneRiskPolicy";
import type { useScenesStore } from "../stores/scenes";
import type {
    Scene,
    SceneInput,
    SceneTemplate,
} from "../types/scene";

type ScenesStore = ReturnType<typeof useScenesStore>;
type QuickActionKey = "batch" | "schedule" | "sort" | "logs";

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

    const editScene = async (scene: Scene) => {
        // 编辑场景需要场景编辑弹窗收集表单，目前复用创建弹窗逻辑未接入。
        // store.editScene 方法已就绪，可由编辑弹窗调用。
        ElMessage.info(`编辑 ${scene.name} 的弹窗尚未接入，API 已就绪`);
    };

    const previewSceneSteps = async (scene: Scene) => {
        try {
            return await store.previewScene(scene);
        } catch (error) {
            ElMessage.error(error instanceof Error ? error.message : "场景预览失败");
            return null;
        }
    };

    const loadSceneLogs = async (scene: Scene) => {
        try {
            return await store.loadSceneLogs(scene.id);
        } catch (error) {
            ElMessage.error(error instanceof Error ? error.message : "日志加载失败");
            return [];
        }
    };

    const runAction = async (key: QuickActionKey) => {
        try {
            if (key === "batch") {
                await store.batchSetEnabled([], true);
                ElMessage.success("已批量启用全部场景");
            } else if (key === "schedule") {
                await store.batchSetSchedule(
                    [],
                    "schedule",
                    "每日定时执行",
                );
                ElMessage.success("已批量设置场景定时");
            } else if (key === "sort") {
                const items = store.scenes.map((scene, index) => ({
                    id: scene.id,
                    sort_order: index,
                }));
                await store.reorderScenes(items);
                ElMessage.success("场景排序已更新");
            } else if (key === "logs") {
                const scene = store.selectedScene;
                if (scene) {
                    const logs = await store.loadSceneLogs(scene.id);
                    ElMessage.success(`已加载 ${scene.name} 的 ${logs.length} 条日志`);
                } else {
                    ElMessage.warning("请先选择一个场景");
                }
            }
        } catch (error) {
            ElMessage.error(error instanceof Error ? error.message : "操作失败");
        }
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

    return {
        copyScene,
        createDialogOpen,
        createScene,
        editScene,
        importTemplate,
        loadSceneLogs,
        openCreateDialog,
        openTemplateDialog,
        previewSceneSteps,
        runAction,
        runScene,
        saveDraft,
        templateDialogOpen,
        toggleScene,
    };
};
