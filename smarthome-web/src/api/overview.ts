import { apiRequest } from "./client";

export interface ScheduleItem {
  id?: number;
  time: string;
  name: string;
  detail: string;
  scene_id?: string;
  position: number;
  enabled: boolean;
  color: string;
}

export interface HouseholdSchedule {
  id: number;
  scheduleDate: string;
  enabled: boolean;
  repeatDays: number[];
  targets: { room_ids?: number[]; device_ids?: number[] };
  items: ScheduleItem[];
  version: number;
  updatedAt: string;
}

export interface ScheduleWrite {
  enabled: boolean;
  repeatDays: number[];
  targets: { room_ids?: number[]; device_ids?: number[] };
  items: ScheduleItem[];
  version?: number;
}

export const getSchedule = (date: string) =>
  apiRequest<HouseholdSchedule | null>(`/api/schedules/${date}`);

export const saveSchedule = (date: string, payload: ScheduleWrite) =>
  apiRequest<HouseholdSchedule>(`/api/schedules/${date}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
