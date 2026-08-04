import { computed, reactive, ref } from "vue";
import { defineStore } from "pinia";
import {
    copyScene as apiCopyScene,
    createScene as apiCreateScene,
    executeScene as apiExecuteScene,
    fetchSceneSummary,
    fetchScenes,
    saveSceneDraft as apiSaveSceneDraft,
    useSceneTemplate as apiUseSceneTemplate,
    updateSceneEnabled as apiUpdateSceneEnabled,
} from "../api/scenes";
import { sleep } from "../utils/async";
import type {
    Scene,
    SceneFilters,
    SceneInput,
    SceneStepStatus,
    SceneSummary,
    SceneTemplate,
} from "../types/scene";

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
    const summary = ref<SceneSummary | null>(null);

    const selectedScene = computed(() =>
        selectedSceneId.value
            ? (scenes.value.find((scene) => scene.id === selectedSceneId.value) ?? null)
            : null,
    );

    const stats = computed(() => ({
        enabled: summary.value?.enabled ?? 0,
        automation: summary.value?.automation ?? 0,
        manual: summary.value?.manual ?? 0,
        monthlyExecutions: summary.value?.monthlyExecutions ?? 0,
    }));

    const loadScenes = async () => {
        loading.value = true;

        try {
            const [sceneItems, sceneSummary] = await Promise.all([
                fetchScenes(filters),
                fetchSceneSummary(),
            ]);
            scenes.value = sceneItems;
            summary.value = sceneSummary;
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
        const scene = scenes.value.find((item) => item.id === sceneId);
        if (!scene) throw new Error("场景不存在");
        const updated = await apiUpdateSceneEnabled(sceneId, enabled);
        scenes.value = scenes.value.map((item) =>
            item.id === sceneId ? { ...item, ...updated } : item,
        );
        if (summary.value) {
            summary.value = {
                ...summary.value,
                enabled: summary.value.enabled + (enabled ? 1 : -1),
            };
        }
    };

    const runScene = async (scene: Scene, confirmHighRisk: boolean) => {
        runningSceneId.value = scene.id;
        selectedSceneId.value = scene.id;
        resetStepStatuses();

        try {
            const nextStatuses = { ...stepStatuses.value };

            for (const step of scene.steps) {
                nextStatuses[step.id] = "running";
                stepStatuses.value = nextStatuses;
                await sleep(180);
                nextStatuses[step.id] = "completed";
                stepStatuses.value = nextStatuses;
            }

            const execution = await apiExecuteScene(scene.id, confirmHighRisk);
            scenes.value = scenes.value.map((item) =>
                item.id === scene.id
                    ? { ...item, updatedAt: execution.finishedAt ?? execution.startedAt }
                    : item,
            );
            summary.value = await fetchSceneSummary();
        } finally {
            runningSceneId.value = null;
        }
    };

    const addScene = async (payload: SceneInput) => {
        const scene = await apiCreateScene(payload);
        await loadScenes();
        selectedSceneId.value = scene.id;
        resetStepStatuses();
        return scene;
    };

    const saveDraft = (payload: SceneInput) => apiSaveSceneDraft(payload);

    const importTemplate = async (template: SceneTemplate) => {
        const scene = await apiUseSceneTemplate(template.id, {
            name: template.name,
            enabled: true,
        });
        await loadScenes();
        selectedSceneId.value = scene.id;
        resetStepStatuses();
        return scene;
    };

    const duplicateScene = async (scene: Scene) => {
        const duplicate = await apiCopyScene(scene.id, `${scene.name} 副本`);
        await loadScenes();
        selectedSceneId.value = duplicate.id;
        resetStepStatuses();
        return duplicate;
    };

    return {
        filters,
        loading,
        addScene,
        duplicateScene,
        runningSceneId,
        scenes,
        selectedScene,
        selectedSceneId,
        stats,
        stepStatuses,
        loadScenes,
        importTemplate,
        resetStepStatuses,
        runScene,
        saveDraft,
        selectScene,
        setSceneEnabled,
    };
});
