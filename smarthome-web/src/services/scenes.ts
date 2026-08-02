import { scenes as mockScenes } from "../mock/scenes";
import type { Scene, SceneFilters } from "../types/scene";

const delay = (duration = 220) =>
    new Promise<void>((resolve) => {
        window.setTimeout(resolve, duration);
    });

const matchesKeyword = (scene: Scene, keyword: string) => {
    const normalizedKeyword = keyword.trim().toLocaleLowerCase();

    if (!normalizedKeyword) {
        return true;
    }

    return [scene.name, scene.description, scene.triggerLabel]
        .join(" ")
        .toLocaleLowerCase()
        .includes(normalizedKeyword);
};

export const listScenes = async (filters: SceneFilters): Promise<Scene[]> => {
    await delay();

    return mockScenes
        .filter((scene) => matchesKeyword(scene, filters.keyword))
        .filter((scene) =>
            filters.triggerType ? scene.triggerType === filters.triggerType : true,
        )
        .filter((scene) => {
            if (filters.enabled === "enabled") return scene.enabled;
            if (filters.enabled === "disabled") return !scene.enabled;
            return true;
        })
        .map((scene) => ({
            ...scene,
            steps: [...scene.steps].sort((first, second) => first.order - second.order),
        }));
};

export const updateSceneEnabled = async (
    sceneId: string,
    enabled: boolean,
): Promise<Scene> => {
    await delay(180);
    const scene = mockScenes.find((item) => item.id === sceneId);

    if (!scene) {
        throw new Error("场景不存在");
    }

    scene.enabled = enabled;
    scene.updatedAt = "2026-08-02 18:30";
    return { ...scene, steps: [...scene.steps] };
};

export const executeScene = async (sceneId: string): Promise<Scene> => {
    await delay(480);
    const scene = mockScenes.find((item) => item.id === sceneId);

    if (!scene) {
        throw new Error("场景不存在");
    }

    scene.updatedAt = "2026-08-02 18:35";
    return { ...scene, steps: [...scene.steps] };
};
