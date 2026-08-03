import { ElMessageBox } from "element-plus";
import type { Scene } from "../types/scene";

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

export const confirmHighRiskScene = async (
  scene: Scene,
): Promise<boolean> => {
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
