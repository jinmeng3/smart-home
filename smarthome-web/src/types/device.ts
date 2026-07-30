export type DeviceType = "light" | "air_conditioner" | "lock" | "camera";

export interface Device {
  id: string;
  name: string;
  type: DeviceType;
  status: string;
  value?: string;
  room: string;
  online: boolean;
  updatedAt: string;
}

export interface DeviceSummary {
  online: number;
  offline: number;
  total: number;
}
