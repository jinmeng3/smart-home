# 前端推断后端接口规范（历史需求分析）

> 本文档保留前端驱动的历史需求分析，用于追踪设计来源，不代表当前后端实现状态。
> 当前接口请以 [后端文档总览](./README.md)、各模块文档和运行时 `/openapi.json` 为准。

---

## 说明

- **推断依据**：前端 API 文件、Pinia Store、Composable、View 组件中的数据处理逻辑、Mock 数据形状
- **状态标记**：
  - ⚪ 已对接 — 前端已调用，后端已有对应路由
  - ✅ 待对接 — 后端已有对应路由，前端尚未调用
  - ❌ 待实现 — 后端尚无对应路由，前端已调用
  - 📝 待规划 — 前端尚无 API 调用，但视图已使用 Mock 数据，暗示需要后端接口

---

## 1. 认证模块 (Auth)

**推断来源**: `api/auth.ts` → `stores/auth.ts`

| 方法 | 路径 | 前端函数 | 输入 | 输出 | 状态 |
|------|------|---------|------|------|------|
| POST | `/api/auth/login` | `login` | `{ account, password }` | `{ access_token, token_type, expires_in, user }` | ⚪ 已对接 |
| POST | `/api/auth/register` | `register` | `{ username, email, password }` | 同登录 | ⚪ 已对接 |
| POST | `/api/auth/logout` | `logout` | 无（需认证） | `{ code, message }` | ⚪ 已对接 |

---

## 2. 账户模块 (Account)

**推断来源**: `api/account.ts` → `stores/settings.ts`

| 方法 | 路径 | 前端函数 | 输入 | 输出 | 状态 |
|------|------|---------|------|------|------|
| GET | `/api/account/me` | `getAccount` | 无（需认证） | `{ id, name, email, avatar_url, created_at, updated_at }` | ⚪ 已对接 |
| PATCH | `/api/account/me` | `updateAccount` | `{ name?, email? }` | 同上 | ⚪ 已对接 |
| POST | `/api/account/me/avatar` | `uploadAvatar` | `multipart: avatar` | `{ avatar_url }` | ⚪ 已对接 |
| DELETE | `/api/account/me/avatar` | `deleteAvatar` | 无（需认证） | `{ avatar_url: null }` | ⚪ 已对接 |

---

## 3. 家庭管理 (Household)

**推断来源**: `api/account.ts` → `stores/settings.ts`

| 方法 | 路径 | 前端函数 | 输入 | 输出 | 状态 |
|------|------|---------|------|------|------|
| GET | `/api/households` | `listHouseholds` | 无（需认证） | `[{ id, name, address, timezone, role, member_count }]` | ⚪ 已对接 |
| POST | `/api/households` | `createHousehold` | `{ name, address?, timezone? }` | 家庭对象 | ✅ 已对接 |
| GET | `/api/households/{id}` | `getHouseholdDetail` | 路径参数 | 家庭对象 | ✅ 已对接 |
| PATCH | `/api/households/{id}` | `updateHousehold` | `{ name?, address?, timezone? }` | 家庭对象 | ⚪ 已对接 |

---

## 4. 家庭成员管理 (Members)

**推断来源**: `api/account.ts` → `stores/settings.ts`

| 方法 | 路径 | 前端函数 | 输入 | 输出 | 状态 |
|------|------|---------|------|------|------|
| GET | `/api/households/{id}/members` | `listMembers` | 路径参数 | `{ items: Member[], total }` | ⚪ 已对接 |
| POST | `/api/households/{id}/members` | `addMember` | `{ email, role? }` | Member | ⚪ 已对接 |
| PATCH | `/api/households/{id}/members/{mid}` | `updateMemberRole` | `{ role }` | Member | ⚪ 已对接 |
| DELETE | `/api/households/{id}/members/{mid}` | `deleteMember` | 路径参数 | 204 | ⚪ 已对接 |

---

## 5. 房间管理 (Rooms)

**推断来源**: `api/room.ts`, `views/RoomControlView.vue`, `types/room.ts`

### 前端期望的数据形状

```typescript
interface Room {
  id: number;
  name: string;
  floor: string;
  roomType: string;      // 后端返回 camelCase
  imageUrl?: string | null;
  area: number;
  comfort: number;
  temperature: number;
  humidity: number;
  pm25: number;
  illuminance: number;
  noise: number;
  deviceCount: number;
  onlineCount: number;
  deviceStates: Record<string, boolean | number | string>;
  updatedAt: string;
}
```

### 推断的后端接口

| 方法 | 路径 | 前端函数 | 输入 | 输出 | 状态 |
|------|------|---------|------|------|------|
| GET | `/api/rooms` | `fetchRooms` | `floor?, room_type?` | `{ items: Room[], total }` | ⚪ 已对接 |
| PATCH | `/api/rooms/{id}/device` | `updateRoomDevice` | `{ device, value }` | Room | ⚪ 已对接 |
| POST | `/api/rooms/{id}/quick-action` | `runRoomQuickAction` | `{ action }` | Room | ⚪ 已对接 |

### 前端 RoomControlView 中暗示的额外接口

RoomControlView 的 `handleRoomCreated` 和 `handleRoomUpdated` 已对接 `POST /api/rooms` 和 `PUT /api/rooms/{id}`，以下接口也已全部实现并导出：

| 方法 | 路径 | 前端期望输入 | 前端期望输出 | 状态 |
|------|------|-------------|-------------|------|
| POST | `/api/rooms` | `{ name, floor, room_type }` | Room 对象 | ✅ 已对接 |
| PUT | `/api/rooms/{id}` | `{ name, floor, room_type, ... }` | Room 对象 | ✅ 已对接 |
| GET | `/api/rooms/{id}/environment/latest` | 路径参数 | 环境数据 | ✅ 已对接 |
| GET | `/api/rooms/{id}/environment/trends` | `metrics?` | 趋势数据 | ✅ 已对接 |
| GET | `/api/rooms/{id}/logs` | `date_from?, date_to?, keyword?, page?` | 日志列表 | ✅ 已对接 |
| GET | `/api/rooms/{id}/devices` | `keyword?, type?, status?` | `{ items, total }` | ✅ 已对接 |

---

## 6. 设备管理 (Devices)

**推断来源**: `api/device.ts`, `composables/useDeviceManagementController.ts`, `types/device.ts`, `views/DeviceManagement.vue`

### 前端期望的数据形状

```typescript
interface Device {
  id: number;
  name: string;
  room: string;
  type: DeviceType;       // light|air_conditioner|lock|camera|sensor|socket|curtain
  brand: string;
  status: DeviceStatus;   // online|offline|warning|running
  connection: DevicePlatform; // Home Assistant|Matter|Zigbee|MQTT
  firmware: string;
  lastOnline: string;
  image?: string;
}

interface DeviceDetail extends Device {
  deviceId: string;
  imageUrl?: string;
  createdAt: string;
  updatedAt: string;
  logs: DeviceLog[];
}
```

### 推断的后端接口

| 方法 | 路径 | 前端函数 | 输入 | 输出 | 状态 |
|------|------|---------|------|------|------|
| GET | `/api/devices` | `listDevices` | `page, page_size, keyword?, type?, status?, room?` | `{ total, items: Device[] }` | ⚪ 已对接 |
| POST | `/api/devices` | `createDevice` | `{ name, room, type, brand, connection, device_id?, firmware?, image_url? }` | Device | ⚪ 已对接 |
| POST | `/api/devices/sync` | `syncDevices` | `{ platform }` | `{ platform, synced_count }` | ⚪ 已对接 |
| GET | `/api/devices/{id}` | `getDevice` | 路径参数 | DeviceDetail | ⚪ 已对接 |
| PUT | `/api/devices/{id}` | `updateDevice` | `{ name?, room?, type?, brand?, status?, connection?, firmware?, image_url? }` | Device | ⚪ 已对接 |
| DELETE | `/api/devices/{id}` | `deleteDevice` | 路径参数 | 空 | ⚪ 已对接 |
| GET | `/api/devices/{id}/logs` | `listDeviceLogs` | `page?, page_size?` | `{ total, items: DeviceLog[] }` | ⚪ 已对接 |
| POST | `/api/devices/images` | `uploadDeviceImage` | `multipart: file, device_id?` | 图片 URL | ⚪ 已对接 |
| POST | `/api/devices/groups/assign` | `batchGroupDevices` | `{ group, device_ids? }` | `{ group_id, group, assigned_count }` | ⚪ 已对接 |

### ❌ 后端缺失的接口

| 方法 | 路径 | 前端函数 | 前端期望输入 | 前端期望输出 | 状态 |
|------|------|---------|-------------|-------------|------|
| POST | `/api/devices/scan` | `scanDevices` | `{ platform: string \| null }` | `{ platform, scanned_count, found_count, found: ApiDevice[] }` | ❌ 待实现 |
| POST | `/api/devices/firmware` | `batchUpdateFirmware` | `{ device_ids: number[], version: string }` | `{ updated_count: number }` | ❌ 待实现 |

### 前端 Composable `runQuickAction` 暗示的快捷操作

`useDeviceManagementController.ts` 中定义了 4 种快捷操作，其中 `scan` 和 `firmware` 后端缺失：

```typescript
const messageMap = {
  scan: "扫描新设备接口已预留",    // ❌ 后端缺失
  group: "批量分组接口已预留",     // ⚪ 已对接 batchGroupDevices
  firmware: "固件更新接口已预留",  // ❌ 后端缺失
  logs: "日志接口已预留",         // ⚪ 已对接 listDeviceLogs
};
```

---

## 7. 设备总览仪表盘 (Overview)

**推断来源**: `views/WholeHomeOverview.vue`, `mock/home.ts`, `stores/home.ts`

### 前端 Mock 数据形状

WholeHomeOverview.vue 使用完整的 Mock 数据，包括：
- 房间列表（6个房间，含名称、设备统计、环境状态）
- 活动日志（13条活动记录，含时间、图标、标题、描述）
- 设备列表（8个设备，含状态、是否收藏、是否常用）
- 日程安排（4条日程，含时间、名称、详情、颜色）
- 首页统计（设备在线/离线/告警数量）

### 推断的后端接口

| 方法 | 路径 | 前端期望 | 输入 | 输出 | 状态 |
|------|------|---------|------|------|------|
| GET | `/api/households/{id}/overview` | 首页总览数据 | 路径参数 | `{ summary, homeStatus, rooms, recentDevices, activities, schedule, alerts }` | ✅ 已对接 |
| GET | `/api/households/{id}/devices` | 家庭下所有设备 | 路径参数 | `{ items: Device[] }` | ✅ 已对接 |
| POST | `/api/households/{id}/devices/sync` | 同步设备 | 路径参数 | `{ id, status, statistics }` | ✅ 已对接 |
| POST | `/api/overview/modes/execute` | 执行家庭模式 | `{ mode, roomIds?, runAutomations? }` | `{ id, status, affectedDeviceCount }` | ✅ 已对接 |

---

## 8. 场景模式 (Scenes)

**推断来源**: `api/scenes.ts`, `stores/scenes.ts`, `composables/useSceneModeController.ts`, `views/SceneModeView.vue`, `types/scene.ts`

### 前端已对接的接口

| 方法 | 路径 | 前端函数 | 状态 |
|------|------|---------|------|
| GET | `/api/scenes` | `fetchScenes` | ⚪ 已对接 |
| GET | `/api/scenes/summary` | `fetchSceneSummary` | ⚪ 已对接 |
| POST | `/api/scenes` | `createScene` | ⚪ 已对接 |
| POST | `/api/scenes/drafts` | `saveSceneDraft` | ⚪ 已对接 |
| PATCH | `/api/scenes/{id}/enabled` | `updateSceneEnabled` | ⚪ 已对接 |
| POST | `/api/scenes/{id}/execute` | `executeScene` | ⚪ 已对接 |
| POST | `/api/scenes/{id}/copy` | `copyScene` | ⚪ 已对接 |
| GET | `/api/scenes/templates` | `fetchSceneTemplates` | ⚪ 已对接 |
| POST | `/api/scenes/templates/{id}/use` | `useSceneTemplate` | ⚪ 已对接 |

### 前端 Composable runAction 暗示的快捷操作

`useSceneModeController.ts` 中 `runAction` 已对接全部快捷操作的后端接口：

```typescript
const runAction = async (key: QuickActionKey) => {
  if (key === "batch")   await store.batchSetEnabled(...)    // POST /api/scenes/batch/enabled
  if (key === "schedule") await store.batchSetSchedule(...)  // POST /api/scenes/batch/schedule
  if (key === "sort")    await store.reorderScenes(...)      // PATCH /api/scenes/order
  if (key === "logs")   await store.loadSceneLogs(...)      // GET  /api/scenes/{id}/logs
};
```

| 方法 | 路径 | 前端函数 | 状态 |
|------|------|---------|------|
| POST | `/api/scenes/batch/enabled` | `batchUpdateSceneEnabled` | ✅ 已对接 |
| POST | `/api/scenes/batch/schedule` | `batchUpdateSceneSchedule` | ✅ 已对接 |
| PATCH | `/api/scenes/order` | `updateSceneOrder` | ✅ 已对接 |
| GET | `/api/scenes/{id}/logs` | `getSceneLogs` | ✅ 已对接 |
| PUT | `/api/scenes/{id}` | `updateScene` | ✅ 已对接 |
| POST | `/api/scenes/{id}/preview` | `previewScene` | ✅ 已对接 |
| GET | `/api/scenes/templates/{id}/preview` | `previewSceneTemplate` | ✅ 已对接 |
| GET | `/api/scenes/executions/{id}` | `getSceneExecution` | ✅ 已对接 |
| POST | `/api/rooms/{id}/scenes/{sid}/preview` | `previewRoomScene` | ✅ 已对接 |
| POST | `/api/rooms/{id}/scenes/{sid}/execute` | `executeRoomScene` | ✅ 已对接 |

---

## 9. 自动化规则 (Automations)

**推断来源**: `views/AutomationCenter.vue`, `stores/automations.ts`, `composables/useAutomationModeController.ts`

### 前端现状

AutomationCenter.vue 已重构为 **Pinia Store + 真实 API 调用**（`stores/automations.ts`），通过 `api/automation.ts` 的 9 个后端接口完成数据交互。

- 状态管理：`useAutomationsStore`（Pinia Store）
- 操作编排：`useAutomationModeController`（Composable）
- 后端规则通过 `toDisplayRule()` 映射为前端展示模型（含 trigger/icon/tone 等显示字段）
- 流程步骤通过 `buildAutomationSteps()` 根据后端返回的 deviceCount 动态生成

### 前端展示模型

```typescript
interface AutomationDisplayRule {
  id: number;
  name: string;
  description: string;
  trigger: string;       // 触发类型显示标签（位置触发|时间触发|设备状态|手动触发）
  devices: number;       // 关联设备数量
  icon: string;
  tone: string;
  enabled: boolean;
}
```

### 已对接的 API

| 方法 | 路径 | 前端函数 | 使用场景 |
|------|------|---------|---------|
| GET | `/api/households/{id}/automations` | `listAutomations` | 规则列表加载、筛选 |
| POST | `/api/households/{id}/automations` | `createAutomation` | 创建规则、复制规则、导入模板 |
| PATCH | `/api/automations/{id}` | `updateAutomation` | 编辑规则 |
| PATCH | `/api/automations/{id}/enabled` | `toggleAutomationEnabled` | 启用/停用、删除（停用代替） |
| POST | `/api/automations/{id}/execute` | `executeAutomation` | 手动执行 |
| POST | `/api/automations/batch-enable` | `batchEnableAutomations` | 批量启用 |
| PUT | `/api/automations/schedules/batch` | `batchSetAutomationSchedule` | 批量设置定时 |

### 尚未对接的 API

| 方法 | 路径 | 前端函数 | 原因 |
|------|------|---------|------|
| GET | `/api/automations/{id}` | `getAutomation` | 列表返回已含详情，暂不需要单独调用 |
| GET | `/api/automations/{id}/executions` | `listAutomationExecutions` | 执行日志对话框暂用本地 Mock 数据 |

---

## 10. 日程管理 (Schedules)

**推断来源**: `api/overview.ts`, `views/WholeHomeOverview.vue`

### 前端期望的数据形状

```typescript
interface ScheduleItem {
  id?: number;
  time: string;
  name: string;
  detail: string;
  scene_id?: string;
  position: number;
  enabled: boolean;
  color: string;
}

interface HouseholdSchedule {
  id: number;
  scheduleDate: string;
  enabled: boolean;
  repeatDays: number[];
  targets: { room_ids?: number[]; device_ids?: number[] };
  items: ScheduleItem[];
  version: number;
  updatedAt: string;
}
```

### 推断的后端接口

| 方法 | 路径 | 前端函数 | 输入 | 输出 | 状态 |
|------|------|---------|------|------|------|
| GET | `/api/schedules/{date}` | `getSchedule` | 路径参数 | `HouseholdSchedule \| null` | ⚪ 已对接 |
| PUT | `/api/schedules/{date}` | `saveSchedule` | `{ enabled, repeatDays, targets, items, version? }` | `HouseholdSchedule` | ⚪ 已对接 |

---

## 11. AI 模型管理 (AI Model)

**推断来源**: `api/aiModel.ts`, `stores/settings.ts`

| 方法 | 路径 | 前端函数 | 状态 |
|------|------|---------|------|
| GET | `/api/ai_model/models` | `listAIModels` | ⚪ 已对接 |
| GET | `/api/ai_model/model` | `getAIModel` | ⚪ 已对接 |
| POST | `/api/ai_model/model` | `createAIModel` | ⚪ 已对接 |
| POST | `/api/ai_model/models/{id}/activate` | `activateAIModel` | ⚪ 已对接 |
| PATCH | `/api/ai_model/model` | `updateAIModel` | ⚪ 已对接 |

---

## 12. 聊天 (Chat)

**推断来源**: `api/chat.ts`, `composables/useHomeChat.ts`, `stores/home.ts`

| 方法 | 路径 | 前端函数 | 状态 |
|------|------|---------|------|
| GET | `/api/chat/sessions` | `listChatSessions` | ⚪ 已对接 |
| POST | `/api/chat/sessions` | `createChatSession` | ⚪ 已对接 |
| GET | `/api/chat/sessions/{id}/messages` | `listChatMessages` | ⚪ 已对接 |
| POST | `/api/chat/completions` | `streamChatCompletion` | ⚪ 已对接 |

---

## 13. 前端需后端实现的接口清单

### 后端缺失，需优先实现

| 优先级 | 方法 | 路径 | 前端函数 | 期望数据类型 |
|--------|------|------|---------|-------------|
| P0 | POST | `/api/devices/scan` | `scanDevices` | `{ platform, scanned_count, found_count, found: ApiDevice[] }` |
| P0 | POST | `/api/devices/firmware` | `batchUpdateFirmware` | `{ updated_count: number }` |

### 后端已有，前端需对接的接口

| 优先级 | 方法 | 路径 | 模块 | 说明 |
|--------|------|------|------|------|
| P1 | GET | `/api/households/{id}/overview` | Overview | 替换首页 Mock 数据 |
| P2 | POST | `/api/scenes/batch/enabled` | Scenes | 批量启用 |
| P2 | POST | `/api/scenes/batch/schedule` | Scenes | 批量设置定时 |
| P2 | PATCH | `/api/scenes/order` | Scenes | 更新排序 |
| P2 | GET | `/api/scenes/{id}/logs` | Scenes | 执行日志 |
| P2 | PUT | `/api/scenes/{id}` | Scenes | 更新场景 |
| P2 | GET | `/api/rooms/{id}/environment/latest` | Rooms | 环境数据 |
| P2 | GET | `/api/rooms/{id}/logs` | Rooms | 活动日志 |
| P2 | GET | `/api/rooms/{id}/devices` | Rooms | 设备列表 |
| P3 | POST | `/api/households` | Household | 创建家庭 |
| P3 | POST | `/api/rooms` | Rooms | 创建房间 |
| P3 | PUT | `/api/rooms/{id}` | Rooms | 编辑房间 |
| P3 | POST | `/api/overview/modes/execute` | Overview | 执行模式 |
| P3 | POST | `/api/inspections` | Overview | 创建巡检 |
| P3 | DELETE | `/api/ai_model/model` | AI Model | 删除模型 |
| P3 | POST | `/api/v1/chat/completions` | Chat | OpenAI 兼容格式 |

---

---

## 14. 数据格式规范

### 命名风格

前端 API 模块中，不同模块使用了不同的命名风格，后端需保持一致：

| 模块 | 前端 DTO 字段风格 | 后端响应格式 |
|------|-----------------|-------------|
| Auth/Account/Device/AI/Chat | `snake_case` | 后端返回 `snake_case`，前端直接映射 |
| Room/Scene/Automation/Overview | `camelCase` | 后端返回 `camelCase`（Pydantic alias generator） |
| Schedule | `camelCase` + 部分 `snake_case` | 混合使用 |

### 统一的响应包装

所有接口应返回 `ApiResponse<T>` 格式：

```json
{
  "code": 0,
  "message": "ok",
  "data": T
}
```

### 认证方式

所有需认证的接口通过 `Authorization: Bearer <token>` 头部传递，token 存储在 `sessionStorage` 的 `smart-home-access-token` 键中。
