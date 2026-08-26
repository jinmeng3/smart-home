/**
 * 设备摘要（供 AI 接口作为上下文输入，不含敏感字段）。
 * 形状与后端 `app.schemas.automation_templates.DeviceSummary` 对齐。
 */
export interface DeviceSummary {
  online: number;
  offline: number;
  by_type: Record<string, number>;
}

/** 把 `Device[]` 折叠为 DeviceSummary，用于 LLM 上下文。 */
export const buildDeviceSummary = (
  devices: ReadonlyArray<{ type: string; status?: string }>,
): DeviceSummary => {
  const by_type: Record<string, number> = {};
  let online = 0;
  let offline = 0;
  for (const device of devices) {
    if (!device.type) continue;
    by_type[device.type] = (by_type[device.type] ?? 0) + 1;
    if (device.status === "offline") offline += 1;
    else online += 1;
  }
  return { online, offline, by_type };
};
