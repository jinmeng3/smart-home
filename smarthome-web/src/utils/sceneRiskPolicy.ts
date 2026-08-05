import type { Scene, SceneStep } from "../types/scene";

/**
 * 场景执行风险策略模块（SRP：风险判定与确认逻辑从控制器中剥离；
 * OCP：新增风险规则时只扩展本模块，不改动控制器）。
 */

const highRiskDeviceKeywords = ["lock", "camera"];

const highRiskSceneIds = ["away"];

export const isHighRiskScene = (scene: Scene): boolean =>
  scene.highRisk === true ||
  highRiskSceneIds.includes(scene.id) ||
  scene.steps.some((step) =>
    highRiskDeviceKeywords.some((keyword) => step.deviceId.includes(keyword)),
  );

/**
 * 返回场景中涉及高风险（门锁 / 安防监控）的具体步骤，
 * 用于在高风险确认弹窗中展示给用户。
 */
export const getHighRiskSteps = (scene: Scene): SceneStep[] =>
  scene.steps.filter((step) =>
    highRiskDeviceKeywords.some((keyword) => step.deviceId.includes(keyword)),
  );
