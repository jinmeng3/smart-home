export type SceneTriggerType =
    | "manual"
    | "schedule"
    | "location"
    | "device";

export type SceneStatus =
    | "enabled"
    | "disabled"
    | "running"
    | "failed";

export interface SceneStep {
    id: string;
    name: string;
    description: string;
    deviceId: string;
    order: number;
}

export interface Scene {
    id: string;
    name: string;
    description: string;
    icon: string;
    color: string;
    triggerType: SceneTriggerType;
    triggerLabel: string;
    deviceCount: number;
    enabled: boolean;
    recommended: boolean;
    steps: SceneStep[];
    createdAt: string;
    updatedAt: string;
}

export interface SceneFilters {
    keyword: string;
    triggerType: SceneTriggerType | "";
    enabled: "all" | "enabled" | "disabled";
}

export type SceneStepStatus = "pending" | "running" | "completed";

export interface SceneTemplate {
    id: string;
    name: string;
    description: string;
    icon: string;
    color: string;
    triggerType: SceneTriggerType;
    triggerLabel: string;
    roomLabels: string[];
    deviceCount: number;
    recommended: boolean;
    category: string;
    steps: SceneStep[];
}
