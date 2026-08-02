import { computed, reactive, ref } from "vue";
import { defineStore } from "pinia";
import {
    executeScene,
    listScenes,
    updateSceneEnabled,
} from "../services/scenes";
import type { Scene, SceneFilters, SceneStepStatus } from "../types/scene";

export const useScenesStore = defineStore("scenes", () => {
    const filters = reactive<SceneFilters>({
        keyword: "",
        triggerType: "",
        enabled: "all",
    });
    const scenes = ref<Scene[]>([]);
    const loading = ref(false);
    const runningSceneId = ref<string | null>(null);
    const selectedSceneId = ref<string | null>(null);
    const stepStatuses = ref<Record<string, SceneStepStatus>>({});
    const monthlyExecutions = ref(86);

    const selectedScene = computed(() =>
        selectedSceneId.value
            ? (scenes.value.find((scene) => scene.id === selectedSceneId.value) ?? null)
            : null,
    );

    const stats = computed(() => ({
        enabled: scenes.value.filter((scene) => scene.enabled).length,
        automation: scenes.value.filter((scene) => scene.triggerType !== "manual").length,
        manual: scenes.value.filter((scene) => scene.triggerType === "manual").length,
        monthlyExecutions: monthlyExecutions.value,
    }));

    const loadScenes = async () => {
        loading.value = true;

        try {
            scenes.value = await listScenes(filters);
            selectedSceneId.value = scenes.value.some(
                (scene) => scene.id === selectedSceneId.value,
            )
                ? selectedSceneId.value
                : (scenes.value[0]?.id ?? null);
            resetStepStatuses();
        } finally {
            loading.value = false;
        }
    };

    const selectScene = (sceneId: string) => {
        selectedSceneId.value = sceneId;
        resetStepStatuses();
    };

    const resetStepStatuses = () => {
        const scene = selectedScene.value;

        stepStatuses.value = scene
            ? scene.steps.reduce<Record<string, SceneStepStatus>>((record, step) => {
                record[step.id] = "pending";
                return record;
            }, {})
            : {};
    };

    const setSceneEnabled = async (sceneId: string, enabled: boolean) => {
        const updatedScene = await updateSceneEnabled(sceneId, enabled);
        scenes.value = scenes.value.map((scene) =>
            scene.id === sceneId ? updatedScene : scene,
        );
    };

    const runScene = async (scene: Scene) => {
        runningSceneId.value = scene.id;
        selectedSceneId.value = scene.id;
        resetStepStatuses();

        for (const step of scene.steps) {
            stepStatuses.value = {
                ...stepStatuses.value,
                [step.id]: "running",
            };
            await new Promise<void>((resolve) => {
                window.setTimeout(resolve, 260);
            });
            stepStatuses.value = {
                ...stepStatuses.value,
                [step.id]: "completed",
            };
        }

        const updatedScene = await executeScene(scene.id);
        monthlyExecutions.value += 1;
        scenes.value = scenes.value.map((item) =>
            item.id === scene.id ? updatedScene : item,
        );
        runningSceneId.value = null;
    };

    return {
        filters,
        loading,
        monthlyExecutions,
        runningSceneId,
        scenes,
        selectedScene,
        selectedSceneId,
        stats,
        stepStatuses,
        loadScenes,
        resetStepStatuses,
        runScene,
        selectScene,
        setSceneEnabled,
    };
});
