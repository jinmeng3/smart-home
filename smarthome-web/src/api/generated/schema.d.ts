// 自动生成，禁止手工编辑。
// 来源：后端 openapi.json（npm run api:generate）。
// 前端组件不应直接引用此文件，应通过 api/ 模块导出。

// ── 通用响应包装 ──
export type ApiResponse<T = unknown> = { code: number; message: string; data: T | null };
export type Paginated<T> = { items: T[]; total: number; page: number; page_size: number };

// ── 组件 Schema ──
export interface AIModelCreate {
  name: string;
  provider: string;
  api_endpoint: string;
  api_key?: string | unknown;
  parameters?: Record<string, unknown>;
  temperature?: number;
  max_tokens?: number;
  is_active?: boolean;
  description?: string | unknown;
}

export interface AIModelRead {
  id: number;
  name: string;
  provider: string;
  api_endpoint: string;
  parameters: Record<string, unknown>;
  temperature: number;
  max_tokens: number;
  is_active: boolean;
  description: string | unknown;
  created_at: string /* date-time */;
  updated_at: string /* date-time */ | unknown;
}

export interface AIModelUpdate {
  name?: string | unknown;
  provider?: string | unknown;
  api_endpoint?: string | unknown;
  api_key?: string | unknown;
  parameters?: Record<string, unknown> | unknown;
  temperature?: number | unknown;
  max_tokens?: number | unknown;
  is_active?: boolean | unknown;
  description?: string | unknown;
}

export interface AccountRead {
  id: number;
  name: string;
  email: string;
  avatar_url: string | unknown;
  created_at: string /* date-time */;
  updated_at: string /* date-time */;
}

export interface AccountUpdate {
  name?: string | unknown;
  email?: string | unknown;
}

export interface ActionWrite {
  type: string;
  config?: Record<string, unknown>;
  position: number;
  deviceId?: number | unknown;
  sceneId?: string | unknown;
}

export interface ApiResponse_AIModelRead_ {
  code?: number;
  message?: string;
  data?: AIModelRead | unknown;
}

export interface ApiResponse_AccountRead_ {
  code?: number;
  message?: string;
  data?: AccountRead | unknown;
}

export interface ApiResponse_AuthResponse_ {
  code?: number;
  message?: string;
  data?: AuthResponse | unknown;
}

export interface ApiResponse_AutomationListRead_ {
  code?: number;
  message?: string;
  data?: AutomationListRead | unknown;
}

export interface ApiResponse_AutomationRead_ {
  code?: number;
  message?: string;
  data?: AutomationRead | unknown;
}

export interface ApiResponse_AvatarResponse_ {
  code?: number;
  message?: string;
  data?: AvatarResponse | unknown;
}

export interface ApiResponse_BatchEnableRead_ {
  code?: number;
  message?: string;
  data?: BatchEnableRead | unknown;
}

export interface ApiResponse_ChatSessionRead_ {
  code?: number;
  message?: string;
  data?: ChatSessionRead | unknown;
}

export interface ApiResponse_DeviceBatchGroupResult_ {
  code?: number;
  message?: string;
  data?: DeviceBatchGroupResult | unknown;
}

export interface ApiResponse_DeviceDetailRead_ {
  code?: number;
  message?: string;
  data?: DeviceDetailRead | unknown;
}

export interface ApiResponse_DeviceDetailWithLogs_ {
  code?: number;
  message?: string;
  data?: DeviceDetailWithLogs | unknown;
}

export interface ApiResponse_DeviceImageRead_ {
  code?: number;
  message?: string;
  data?: DeviceImageRead | unknown;
}

export interface ApiResponse_DeviceListRead_ {
  code?: number;
  message?: string;
  data?: DeviceListRead | unknown;
}

export interface ApiResponse_DeviceLogListRead_ {
  code?: number;
  message?: string;
  data?: DeviceLogListRead | unknown;
}

export interface ApiResponse_DeviceSyncRead_ {
  code?: number;
  message?: string;
  data?: DeviceSyncRead | unknown;
}

export interface ApiResponse_EnabledRead_ {
  code?: number;
  message?: string;
  data?: EnabledRead | unknown;
}

export interface ApiResponse_ExecuteRead_ {
  code?: number;
  message?: string;
  data?: ExecuteRead | unknown;
}

export interface ApiResponse_ExecutionListRead_ {
  code?: number;
  message?: string;
  data?: ExecutionListRead | unknown;
}

export interface ApiResponse_HouseholdRead_ {
  code?: number;
  message?: string;
  data?: HouseholdRead | unknown;
}

export interface ApiResponse_MemberListResponse_ {
  code?: number;
  message?: string;
  data?: MemberListResponse | unknown;
}

export interface ApiResponse_MemberRead_ {
  code?: number;
  message?: string;
  data?: MemberRead | unknown;
}

export interface ApiResponse_NoneType_ {
  code?: number;
  message?: string;
  data?: unknown;
}

export interface ApiResponse_OverviewRead_ {
  code?: number;
  message?: string;
  data?: OverviewRead | unknown;
}

export interface ApiResponse_RoomDetailRead_ {
  code?: number;
  message?: string;
  data?: RoomDetailRead | unknown;
}

export interface ApiResponse_RoomDeviceListRead_ {
  code?: number;
  message?: string;
  data?: RoomDeviceListRead | unknown;
}

export interface ApiResponse_RoomListRead_ {
  code?: number;
  message?: string;
  data?: RoomListRead | unknown;
}

export interface ApiResponse_RoomLogListRead_ {
  code?: number;
  message?: string;
  data?: RoomLogListRead | unknown;
}

export interface ApiResponse_RoomRead_ {
  code?: number;
  message?: string;
  data?: RoomRead | unknown;
}

export interface ApiResponse_RoomStatsRead_ {
  code?: number;
  message?: string;
  data?: RoomStatsRead | unknown;
}

export interface ApiResponse_SceneBatchEnabledResult_ {
  code?: number;
  message?: string;
  data?: SceneBatchEnabledResult | unknown;
}

export interface ApiResponse_SceneBatchScheduleResult_ {
  code?: number;
  message?: string;
  data?: SceneBatchScheduleResult | unknown;
}

export interface ApiResponse_SceneDraftRead_ {
  code?: number;
  message?: string;
  data?: SceneDraftRead | unknown;
}

export interface ApiResponse_SceneEnabledRead_ {
  code?: number;
  message?: string;
  data?: SceneEnabledRead | unknown;
}

export interface ApiResponse_SceneExecutionRead_ {
  code?: number;
  message?: string;
  data?: SceneExecutionRead | unknown;
}

export interface ApiResponse_SceneListRead_ {
  code?: number;
  message?: string;
  data?: SceneListRead | unknown;
}

export interface ApiResponse_SceneLogListRead_ {
  code?: number;
  message?: string;
  data?: SceneLogListRead | unknown;
}

export interface ApiResponse_SceneOrderRead_ {
  code?: number;
  message?: string;
  data?: SceneOrderRead | unknown;
}

export interface ApiResponse_ScenePreviewRead_ {
  code?: number;
  message?: string;
  data?: ScenePreviewRead | unknown;
}

export interface ApiResponse_SceneRead_ {
  code?: number;
  message?: string;
  data?: SceneRead | unknown;
}

export interface ApiResponse_SceneSummaryRead_ {
  code?: number;
  message?: string;
  data?: SceneSummaryRead | unknown;
}

export interface ApiResponse_SceneTemplateListRead_ {
  code?: number;
  message?: string;
  data?: SceneTemplateListRead | unknown;
}

export interface ApiResponse_SceneTemplatePreviewRead_ {
  code?: number;
  message?: string;
  data?: SceneTemplatePreviewRead | unknown;
}

export interface ApiResponse_ScheduleRead_ {
  code?: number;
  message?: string;
  data?: ScheduleRead | unknown;
}

export interface ApiResponse_SyncJobRead_ {
  code?: number;
  message?: string;
  data?: SyncJobRead | unknown;
}

export interface ApiResponse_TaskRead_ {
  code?: number;
  message?: string;
  data?: TaskRead | unknown;
}

export interface ApiResponse_Union_ScheduleRead__NoneType__ {
  code?: number;
  message?: string;
  data?: ScheduleRead | unknown;
}

export interface ApiResponse_list_AIModelRead__ {
  code?: number;
  message?: string;
  data?: AIModelRead[] | unknown;
}

export interface ApiResponse_list_ChatMessageRead__ {
  code?: number;
  message?: string;
  data?: ChatMessageRead[] | unknown;
}

export interface ApiResponse_list_ChatSessionRead__ {
  code?: number;
  message?: string;
  data?: ChatSessionRead[] | unknown;
}

export interface ApiResponse_list_HouseholdListItem__ {
  code?: number;
  message?: string;
  data?: HouseholdListItem[] | unknown;
}

export interface AuthResponse {
  accessToken: string;
  tokenType: string;
  expiresIn: number;
  user: AccountRead;
}

export interface AutomationCreate {
  name: string;
  description?: string;
  enabled?: boolean;
  triggers: FlowItem[];
  conditions?: ConditionWrite[];
  actions: ActionWrite[];
  priority?: number;
  cooldownSeconds?: number;
  delaySeconds?: number;
  note?: string;
}

export interface AutomationListItem {
  id: number;
  name: string;
  description: string;
  triggerType: string;
  enabled: boolean;
  deviceCount: number;
  updatedAt: string /* date-time */;
}

export interface AutomationListRead {
  summary: AutomationSummary;
  items: AutomationListItem[];
  total: number;
}

export interface AutomationRead {
  id: number;
  householdId: number;
  name: string;
  description: string;
  triggerType: string;
  enabled: boolean;
  deviceCount: number;
  priority: number;
  cooldownSeconds: number;
  delaySeconds: number;
  note: string;
  version: number;
  triggers: FlowItem[];
  conditions: ConditionWrite[];
  actions: ActionWrite[];
  createdAt: string /* date-time */;
  updatedAt: string /* date-time */;
}

export interface AutomationSummary {
  enabled: number;
  total: number;
  running: number;
  executionsToday: number;
  abnormal: number;
}

export interface AutomationUpdate {
  name?: string | unknown;
  description?: string | unknown;
  enabled?: boolean | unknown;
  triggers?: FlowItem[] | unknown;
  conditions?: ConditionWrite[] | unknown;
  actions?: ActionWrite[] | unknown;
  priority?: number | unknown;
  cooldownSeconds?: number | unknown;
  delaySeconds?: number | unknown;
  note?: string | unknown;
  version?: number | unknown;
}

export interface AvatarResponse {
  avatar_url: string | unknown;
}

export interface BatchEnableRead {
  updatedCount: number;
  unchangedCount: number;
  executionBatchId?: string | unknown;
}

export interface BatchEnableWrite {
  ruleIds: number[];
  executeNow?: boolean;
  executionIntervalSeconds?: number;
}

export interface BatchScheduleWrite {
  ruleIds: number[];
  timezone: string;
  time: string;
  weekdays: number[];
  frequency?: "daily" | "weekly";
  interval?: number;
}

export interface Body_upload_avatar_api_account_me_avatar_post {
  avatar: string;
}

export interface Body_upload_image_api_devices_images_post {
  file: string;
}

export interface ChatCompletionMessage {
  role: "system" | "user" | "assistant" | "tool";
  content: string;
}

export interface ChatCompletionRequest {
  model?: string | unknown;
  messages: ChatCompletionMessage[];
  session_id?: number | unknown;
  stream?: boolean;
}

export interface ChatMessageRead {
  id: number;
  sessionId: number;
  role: string;
  content: string;
  createdAt: string /* date-time */;
}

export interface ChatSessionRead {
  id: number;
  title: string;
  createdAt: string /* date-time */;
  updatedAt: string /* date-time */;
}

export interface ConditionWrite {
  type: string;
  config?: Record<string, unknown>;
  position?: number | unknown;
}

export interface DeviceBatchGroup {
  group: string;
  device_ids?: number[];
}

export interface DeviceBatchGroupResult {
  group_id: number;
  group: string;
  assigned_count?: number;
}

export interface DeviceCreate {
  name: string;
  room: string;
  type: string;
  brand: string;
  connection: "Home Assistant" | "Matter" | "Zigbee" | "MQTT";
  device_id?: string | unknown;
  firmware?: string;
  icon?: string;
  color?: string;
  image_url?: string | unknown;
}

export interface DeviceDetailRead {
  id: number;
  name: string;
  room: string;
  type: string;
  brand: string;
  status: "online" | "offline" | "warning" | "running";
  connection: "Home Assistant" | "Matter" | "Zigbee" | "MQTT";
  firmware: string;
  icon?: string;
  color?: string;
  image_url: string | unknown;
  last_online: string /* date-time */ | unknown;
  device_id: string;
  created_at: string /* date-time */;
  updated_at: string /* date-time */;
}

export interface DeviceDetailWithLogs {
  id: number;
  name: string;
  room: string;
  type: string;
  brand: string;
  status: "online" | "offline" | "warning" | "running";
  connection: "Home Assistant" | "Matter" | "Zigbee" | "MQTT";
  firmware: string;
  icon?: string;
  color?: string;
  image_url: string | unknown;
  last_online: string /* date-time */ | unknown;
  device_id: string;
  created_at: string /* date-time */;
  updated_at: string /* date-time */;
  logs: DeviceLogRead[];
}

export interface DeviceImageRead {
  image_url: string;
  original_name: string;
  mime_type: string;
  size_bytes: number;
}

export interface DeviceListRead {
  total: number;
  page: number;
  page_size: number;
  items: DeviceRead[];
}

export interface DeviceLogListRead {
  total: number;
  page: number;
  page_size: number;
  items: DeviceLogRead[];
}

export interface DeviceLogRead {
  id: number;
  device_id: number;
  action: string;
  message: string;
  created_at: string /* date-time */;
}

export interface DeviceRead {
  id: number;
  name: string;
  room: string;
  type: string;
  brand: string;
  status: "online" | "offline" | "warning" | "running";
  connection: "Home Assistant" | "Matter" | "Zigbee" | "MQTT";
  firmware: string;
  icon?: string;
  color?: string;
  image_url: string | unknown;
  last_online: string /* date-time */ | unknown;
}

export type DeviceStatus = "online" | "offline" | "warning" | "running";
export interface DeviceSync {
  platform: "Home Assistant" | "Matter" | "Zigbee" | "MQTT";
}

export interface DeviceSyncRead {
  platform: "Home Assistant" | "Matter" | "Zigbee" | "MQTT";
  synced_count: number;
}

export interface DeviceUpdate {
  name?: string | unknown;
  room?: string | unknown;
  type?: string | unknown;
  brand?: string | unknown;
  status?: "online" | "offline" | "warning" | "running" | unknown;
  connection?: "Home Assistant" | "Matter" | "Zigbee" | "MQTT" | unknown;
  firmware?: string | unknown;
  icon?: string | unknown;
  color?: string | unknown;
  image_url?: string | unknown;
}

export interface EnabledRead {
  id: number;
  enabled: boolean;
}

export interface EnabledWrite {
  enabled: boolean;
}

export interface ExecuteRead {
  executionId: number;
  status: string;
}

export interface ExecuteWrite {
  source?: string;
}

export interface ExecutionListRead {
  total: number;
  items: ExecutionRead[];
}

export interface ExecutionRead {
  id: number;
  status: string;
  source: string;
  triggerSnapshot: Record<string, unknown>;
  durationMs: number | unknown;
  errorMessage: string | unknown;
  startedAt: string /* date-time */;
  finishedAt: string /* date-time */ | unknown;
}

export interface FlowItem {
  type: string;
  config?: Record<string, unknown>;
}

export interface HTTPValidationError {
  detail?: ValidationError[];
}

export interface HomeStatus {
  status?: string;
  people_home?: number;
  temperature: number;
  humidity: number;
  air_quality: string;
  pm25: number;
  locked_count?: number;
  lock_total?: number;
}

export interface HouseholdCreate {
  name: string;
  address?: string | unknown;
  timezone?: string;
}

export interface HouseholdListItem {
  id: number;
  name: string;
  address: string | unknown;
  timezone: string;
  created_by: number;
  created_at: string /* date-time */;
  updated_at: string /* date-time */;
  role: string;
  member_count: number;
}

export interface HouseholdRead {
  id: number;
  name: string;
  address: string | unknown;
  timezone: string;
  created_by: number;
  created_at: string /* date-time */;
  updated_at: string /* date-time */;
}

export type HouseholdRole = "admin" | "member";
export interface HouseholdUpdate {
  name?: string | unknown;
  address?: string | unknown;
  timezone?: string | unknown;
}

export interface InspectionWrite {
  scope: string;
  roomIds?: number[];
  deviceTypes?: string[];
  checks: string[];
}

export interface LoginRequest {
  account: string;
  password: string;
}

export interface MemberCreate {
  email: string;
  role?: HouseholdRole;
}

export interface MemberListResponse {
  items: MemberRead[];
  total: number;
}

export interface MemberRead {
  membership_id: number;
  user_id: number;
  name: string;
  email: string;
  avatar_url: string | unknown;
  role: HouseholdRole;
  joined_at: string /* date-time */;
}

export interface MemberRoleUpdate {
  role: HouseholdRole;
}

export interface ModeExecuteWrite {
  mode: string;
  roomIds?: number[];
  runAutomations?: boolean;
  idempotencyKey: string;
}

export interface OverviewRead {
  summary: OverviewSummary;
  home_status: HomeStatus;
  rooms: OverviewRoom[];
  recent_devices?: Record<string, unknown>[];
  activities?: Record<string, unknown>[];
  schedule?: Record<string, unknown>[];
  alerts?: Record<string, unknown>[];
}

export interface OverviewRoom {
  id: number;
  name: string;
  device_count: number;
  light_on: number;
  light_total: number;
  temperature: number;
  device_summaries: string[];
}

export interface OverviewSummary {
  device_total: number;
  device_online: number;
  running_automation_count: number;
  alert_count?: number;
  monthly_energy_kwh?: number;
  energy_saving_rate?: number;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

export interface RoomDetailRead {
  room: RoomRead;
  currentScene?: string | unknown;
  recentActivity?: string | unknown;
  recentActivityTime?: string | unknown;
}

export interface RoomDeviceBinding {
  deviceId: number;
  group?: string;
  favorite?: boolean;
  sortOrder?: number;
}

export interface RoomDeviceListItem {
  id: number;
  name: string;
  type: string;
  brand: string;
  status: string;
  icon?: string;
  color?: string;
  group: string;
  favorite: boolean;
  sortOrder: number;
  updatedAt: string /* date-time */;
}

export interface RoomDeviceListRead {
  items: RoomDeviceListItem[];
  total: number;
}

export interface RoomDeviceMetaWrite {
  group?: string | unknown;
  favorite?: boolean | unknown;
  sortOrder?: number | unknown;
}

export interface RoomDeviceWrite {
  deviceId: number;
  status: DeviceStatus;
}

export interface RoomDevicesWrite {
  devices: RoomDeviceBinding[];
}

export interface RoomInput {
  name: string;
  floor?: string;
  roomType?: string;
  icon?: string;
  themeColor?: string;
  imageUrl?: string | unknown;
  area?: number;
  comfort?: number;
  version?: number | unknown;
  deviceIds?: number[];
}

export interface RoomListRead {
  items: RoomRead[];
  total: number;
}

export interface RoomLogListRead {
  total: number;
  page: number;
  pageSize: number;
  items: RoomLogRead[];
}

export interface RoomLogRead {
  id: number;
  occurredAt: string /* date-time */;
  source: string;
  event: string;
  result: string;
  durationMs: number | unknown;
  deviceId: number | unknown;
  deviceName: string | unknown;
  tags: string[];
  detail: Record<string, unknown>;
}

export interface RoomQuickActionWrite {
  action: string;
}

export interface RoomRead {
  id: number;
  name: string;
  floor: string;
  roomType: string;
  imageUrl: string | unknown;
  icon?: string;
  themeColor?: string;
  version?: number;
  area: number;
  comfort: number;
  device?: RoomDeviceListItem[];
  deviceCount?: number;
  onlineCount?: number;
  createdAt: string /* date-time */;
  updatedAt: string /* date-time */;
}

export interface RoomSceneExecuteWrite {
  scope?: string;
  syncAutomation?: boolean;
}

export interface RoomStatsRead {
  roomCount: number;
  roomCountChange?: number;
  onlineRate?: number;
  alertCount?: number;
  pendingAlertCount?: number;
}

export interface SceneBatchEnabledResult {
  updatedCount?: number;
}

export interface SceneBatchEnabledWrite {
  sceneIds?: string[];
  enabled: boolean;
}

export interface SceneBatchScheduleResult {
  updatedCount?: number;
}

export interface SceneBatchScheduleWrite {
  sceneIds?: string[];
  triggerType?: "manual" | "schedule" | "location" | "device";
  triggerLabel: string;
}

export interface SceneCopyWrite {
  name: string;
}

export interface SceneDraftRead {
  draftId: string;
  updatedAt: string /* date-time */;
}

export interface SceneDraftWrite {
  name?: string;
  description?: string;
  icon?: string;
  color?: string;
  triggerType?: "manual" | "schedule" | "location" | "device";
  triggerLabel?: string;
  roomLabels?: string[];
  deviceIds?: string[];
  enabled?: boolean;
  recommended?: boolean;
  highRisk?: boolean | unknown;
  steps?: SceneStepWrite[];
}

export interface SceneEnabledRead {
  id: string;
  enabled: boolean;
  updatedAt: string /* date-time */;
}

export interface SceneEnabledWrite {
  enabled: boolean;
}

export interface SceneExecuteWrite {
  confirmHighRisk?: boolean;
  source?: string;
}

export interface SceneExecutionRead {
  executionId: string;
  sceneId: string;
  status: string;
  startedAt: string /* date-time */;
  finishedAt: string /* date-time */ | unknown;
  steps: SceneExecutionStepRead[];
}

export interface SceneExecutionStepRead {
  stepId: string;
  status: string;
  message: string | unknown;
}

export interface SceneListRead {
  items: SceneRead[];
  total: number;
}

export interface SceneLogListRead {
  items: SceneLogRead[];
}

export interface SceneLogRead {
  id: string;
  sceneId: string;
  status: string;
  startedAt: string /* date-time */;
  finishedAt: string /* date-time */ | unknown;
  message: string | unknown;
}

export interface SceneOrderItem {
  id: string;
  sortOrder: number;
}

export interface SceneOrderRead {
  updated: number;
}

export interface SceneOrderWrite {
  items: SceneOrderItem[];
}

export interface ScenePreviewRead {
  sceneId: string;
  highRisk: boolean;
  triggerLabel: string;
  steps: ScenePreviewStep[];
}

export interface ScenePreviewStep {
  stepId: string;
  name: string;
  deviceId: string;
  estimatedMs: number;
  riskLevel: "low" | "high";
}

export interface ScenePreviewWrite {
  source?: string;
}

export interface SceneRead {
  id: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  triggerType: "manual" | "schedule" | "location" | "device";
  triggerLabel: string;
  roomLabels: string[];
  deviceCount: number;
  enabled: boolean;
  recommended: boolean;
  highRisk: boolean;
  sortOrder: number;
  sourceTemplateId: string | unknown;
  createdAt: string /* date-time */;
  updatedAt: string /* date-time */;
  steps: SceneStepRead[];
}

export interface SceneStepRead {
  name: string;
  description?: string;
  deviceId: string;
  order: number;
  id: string;
}

export interface SceneStepWrite {
  name: string;
  description?: string;
  deviceId: string;
  order: number;
}

export interface SceneSummaryRead {
  enabled: number;
  automation: number;
  manual: number;
  monthlyExecutions: number;
  enabledRate: number;
  automationRate: number;
  manualRate: number;
  monthlyGrowthRate: number;
}

export interface SceneTemplateListRead {
  items: SceneTemplateRead[];
}

export interface SceneTemplatePreviewRead {
  templateId: string;
  matchedDeviceCount: number;
  missingDeviceCount: number;
  steps: SceneTemplatePreviewStep[];
}

export interface SceneTemplatePreviewStep {
  name: string;
  description: string;
  deviceId: string;
  matched: boolean;
}

export interface SceneTemplateRead {
  id: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  triggerType: "manual" | "schedule" | "location" | "device";
  triggerLabel: string;
  roomLabels: string[];
  deviceCount: number;
  recommended: boolean;
  category: string;
  steps: SceneStepRead[];
}

export interface SceneTemplateUseWrite {
  name?: string | unknown;
  enabled?: boolean;
  deviceMapping?: Record<string, unknown>;
}

export interface SceneWrite {
  name: string;
  description?: string;
  icon?: string;
  color?: string;
  triggerType?: "manual" | "schedule" | "location" | "device";
  triggerLabel?: string;
  roomLabels?: string[];
  deviceIds?: string[];
  enabled?: boolean;
  recommended?: boolean;
  highRisk?: boolean | unknown;
  steps?: SceneStepWrite[];
}

export interface ScheduleRead {
  enabled?: boolean;
  repeatDays?: number[];
  targets?: Record<string, unknown>;
  items?: Record<string, unknown>[];
  version: number;
  id: number;
  scheduleDate: string /* date */;
  updatedAt: string /* date-time */;
}

export interface ScheduleWrite {
  enabled?: boolean;
  repeatDays?: number[];
  targets?: Record<string, unknown>;
  items?: Record<string, unknown>[];
  version?: number | unknown;
}

export interface SyncJobRead {
  id: number;
  status: string;
  statistics?: Record<string, unknown>;
}

export interface SyncJobWrite {
  scope?: string;
  sources: string[];
  options?: Record<string, unknown>;
  idempotencyKey: string;
}

export interface TaskRead {
  id: number;
  status: string;
  affectedDeviceCount?: number | unknown;
  checkedCount?: number | unknown;
  deviceCount?: number | unknown;
  estimatedSeconds?: number | unknown;
}

export interface ValidationError {
  loc: string | number[];
  msg: string;
  type: string;
  input?: unknown;
  ctx?: Record<string, unknown>;
}

// ── 操作路径与方法 ──
// Read Me
export type read_me_api_account_me_get = { path: "/api/account/me"; method: "GET" };
// Update Me
export type update_me_api_account_me_patch = { path: "/api/account/me"; method: "PATCH" };
// Upload Avatar
export type upload_avatar_api_account_me_avatar_post = { path: "/api/account/me/avatar"; method: "POST" };
// Delete Avatar
export type delete_avatar_api_account_me_avatar_delete = { path: "/api/account/me/avatar"; method: "DELETE" };
// Get Automations
export type get_automations_api_households__household_id__automations_get = { path: "/api/households/{household_id}/automations"; method: "GET" };
// Add Automation
export type add_automation_api_households__household_id__automations_post = { path: "/api/households/{household_id}/automations"; method: "POST" };
// Read Automation
export type read_automation_api_automations__automation_id__get = { path: "/api/automations/{automation_id}"; method: "GET" };
// Edit Automation
export type edit_automation_api_automations__automation_id__patch = { path: "/api/automations/{automation_id}"; method: "PATCH" };
// Change Automation Enabled
export type change_automation_enabled_api_automations__automation_id__enabled_patch = { path: "/api/automations/{automation_id}/enabled"; method: "PATCH" };
// Run Automation
export type run_automation_api_automations__automation_id__execute_post = { path: "/api/automations/{automation_id}/execute"; method: "POST" };
// Get Automation Executions
export type get_automation_executions_api_automations__automation_id__executions_get = { path: "/api/automations/{automation_id}/executions"; method: "GET" };
// Batch Enable Automations
export type batch_enable_automations_api_automations_batch_enable_post = { path: "/api/automations/batch-enable"; method: "POST" };
// Batch Set Schedule
export type batch_set_schedule_api_automations_schedules_batch_put = { path: "/api/automations/schedules/batch"; method: "PUT" };
// Get Ai Models
export type get_ai_models_api_ai_model_models_get = { path: "/api/ai_model/models"; method: "GET" };
// Read Ai Model
export type read_ai_model_api_ai_model_model_get = { path: "/api/ai_model/model"; method: "GET" };
// Add Ai Model
export type add_ai_model_api_ai_model_model_post = { path: "/api/ai_model/model"; method: "POST" };
// Delete Ai Model
export type delete_ai_model_api_ai_model_model_delete = { path: "/api/ai_model/model"; method: "DELETE" };
// Update Ai Model
export type update_ai_model_api_ai_model_model_patch = { path: "/api/ai_model/model"; method: "PATCH" };
// Activate Model
export type activate_model_api_ai_model_models__model_id__activate_post = { path: "/api/ai_model/models/{model_id}/activate"; method: "POST" };
// List Chat Sessions
export type list_chat_sessions_api_chat_sessions_get = { path: "/api/chat/sessions"; method: "GET" };
// Create Session
export type create_session_api_chat_sessions_post = { path: "/api/chat/sessions"; method: "POST" };
// List Chat Messages
export type list_chat_messages_api_chat_sessions__session_id__messages_get = { path: "/api/chat/sessions/{session_id}/messages"; method: "GET" };
// Create Chat
export type create_chat_api_chat_completions_post = { path: "/api/chat/completions"; method: "POST" };
// Create Chat
export type create_chat_api_v1_chat_completions_post = { path: "/api/v1/chat/completions"; method: "POST" };
// List Devices
export type list_devices_api_devices_get = { path: "/api/devices"; method: "GET" };
// Add Device
export type add_device_api_devices_post = { path: "/api/devices"; method: "POST" };
// Get Device
export type get_device_api_devices__device_id__get = { path: "/api/devices/{device_id}"; method: "GET" };
// Update Device
export type update_device_api_devices__device_id__patch = { path: "/api/devices/{device_id}"; method: "PATCH" };
// Remove Device
export type remove_device_api_devices__device_id__delete = { path: "/api/devices/{device_id}"; method: "DELETE" };
// Sync Devices
export type sync_devices_api_devices_sync_post = { path: "/api/devices/sync"; method: "POST" };
// List Device Logs
export type list_device_logs_api_devices__device_id__logs_get = { path: "/api/devices/{device_id}/logs"; method: "GET" };
// Upload Image
export type upload_image_api_devices_images_post = { path: "/api/devices/images"; method: "POST" };
// Batch Assign Group
export type batch_assign_group_api_devices_groups_assign_post = { path: "/api/devices/groups/assign"; method: "POST" };
// List Households
export type list_households_api_households_get = { path: "/api/households"; method: "GET" };
// Create Household
export type create_household_api_households_post = { path: "/api/households"; method: "POST" };
// Read Household
export type read_household_api_households__household_id__get = { path: "/api/households/{household_id}"; method: "GET" };
// Update Household
export type update_household_api_households__household_id__patch = { path: "/api/households/{household_id}"; method: "PATCH" };
// List Members
export type list_members_api_households__household_id__members_get = { path: "/api/households/{household_id}/members"; method: "GET" };
// Add Member
export type add_member_api_households__household_id__members_post = { path: "/api/households/{household_id}/members"; method: "POST" };
// Update Member Role
export type update_member_role_api_households__household_id__members__membership_id__patch = { path: "/api/households/{household_id}/members/{membership_id}"; method: "PATCH" };
// Delete Member
export type delete_member_api_households__household_id__members__membership_id__delete = { path: "/api/households/{household_id}/members/{membership_id}"; method: "DELETE" };
// Get Overview
export type get_overview_api_households__household_id__overview_get = { path: "/api/households/{household_id}/overview"; method: "GET" };
// Get Household Devices
export type get_household_devices_api_households__household_id__devices_get = { path: "/api/households/{household_id}/devices"; method: "GET" };
// Sync Household Devices
export type sync_household_devices_api_households__household_id__devices_sync_post = { path: "/api/households/{household_id}/devices/sync"; method: "POST" };
// Execute Mode
export type execute_mode_api_overview_modes_execute_post = { path: "/api/overview/modes/execute"; method: "POST" };
// Create Inspection
export type create_inspection_api_inspections_post = { path: "/api/inspections"; method: "POST" };
// Get Inspection
export type get_inspection_api_inspections__inspection_id__get = { path: "/api/inspections/{inspection_id}"; method: "GET" };
// Save Schedule
export type save_schedule_api_schedules__schedule_date__put = { path: "/api/schedules/{schedule_date}"; method: "PUT" };
// Read Schedule
export type read_schedule_api_schedules__schedule_date__get = { path: "/api/schedules/{schedule_date}"; method: "GET" };
// Create Sync Job
export type create_sync_job_api_device_sync_jobs_post = { path: "/api/device-sync-jobs"; method: "POST" };
// Get Sync Job
export type get_sync_job_api_device_sync_jobs__job_id__get = { path: "/api/device-sync-jobs/{job_id}"; method: "GET" };
// List Rooms
export type list_rooms_api_rooms_get = { path: "/api/rooms"; method: "GET" };
// Add Room
export type add_room_api_rooms_post = { path: "/api/rooms"; method: "POST" };
// List Room Stats
export type list_room_stats_api_rooms_stats_get = { path: "/api/rooms/stats"; method: "GET" };
// Get Room Detail
export type get_room_detail_api_rooms__room_id__get = { path: "/api/rooms/{room_id}"; method: "GET" };
// Edit Room
export type edit_room_api_rooms__room_id__patch = { path: "/api/rooms/{room_id}"; method: "PATCH" };
// Delete Room
export type delete_room_api_rooms__room_id__delete = { path: "/api/rooms/{room_id}"; method: "DELETE" };
// Get Room Logs
export type get_room_logs_api_rooms__room_id__logs_get = { path: "/api/rooms/{room_id}/logs"; method: "GET" };
// Get Room Devices
export type get_room_devices_api_rooms__room_id__devices_get = { path: "/api/rooms/{room_id}/devices"; method: "GET" };
// Set Room Devices
export type set_room_devices_api_rooms__room_id__devices_put = { path: "/api/rooms/{room_id}/devices"; method: "PUT" };
// Edit Room Device
export type edit_room_device_api_rooms__room_id__devices__device_id__patch = { path: "/api/rooms/{room_id}/devices/{device_id}"; method: "PATCH" };
// Update Device
export type update_device_api_rooms__room_id__device_patch = { path: "/api/rooms/{room_id}/device"; method: "PATCH" };
// Quick Action
export type quick_action_api_rooms__room_id__quick_action_post = { path: "/api/rooms/{room_id}/quick-action"; method: "POST" };
// Get Room Scenes
export type get_room_scenes_api_rooms__room_id__scenes_get = { path: "/api/rooms/{room_id}/scenes"; method: "GET" };
// Preview Room Scene
export type preview_room_scene_api_rooms__room_id__scenes__scene_id__preview_post = { path: "/api/rooms/{room_id}/scenes/{scene_id}/preview"; method: "POST" };
// Execute Room Scene
export type execute_room_scene_api_rooms__room_id__scenes__scene_id__execute_post = { path: "/api/rooms/{room_id}/scenes/{scene_id}/execute"; method: "POST" };
// Get Scenes
export type get_scenes_api_scenes_get = { path: "/api/scenes"; method: "GET" };
// Add Scene
export type add_scene_api_scenes_post = { path: "/api/scenes"; method: "POST" };
// Get Summary
export type get_summary_api_scenes_summary_get = { path: "/api/scenes/summary"; method: "GET" };
// Reorder Scenes
export type reorder_scenes_api_scenes_order_patch = { path: "/api/scenes/order"; method: "PATCH" };
// Add Draft
export type add_draft_api_scenes_drafts_post = { path: "/api/scenes/drafts"; method: "POST" };
// Get Templates
export type get_templates_api_scenes_templates_get = { path: "/api/scenes/templates"; method: "GET" };
// Get Template Preview
export type get_template_preview_api_scenes_templates__template_id__preview_get = { path: "/api/scenes/templates/{template_id}/preview"; method: "GET" };
// Import Template
export type import_template_api_scenes_templates__template_id__use_post = { path: "/api/scenes/templates/{template_id}/use"; method: "POST" };
// Get Execution
export type get_execution_api_scenes_executions__execution_id__get = { path: "/api/scenes/executions/{execution_id}"; method: "GET" };
// Edit Scene
export type edit_scene_api_scenes__scene_id__put = { path: "/api/scenes/{scene_id}"; method: "PUT" };
// Remove Scene
export type remove_scene_api_scenes__scene_id__delete = { path: "/api/scenes/{scene_id}"; method: "DELETE" };
// Change Enabled
export type change_enabled_api_scenes__scene_id__enabled_patch = { path: "/api/scenes/{scene_id}/enabled"; method: "PATCH" };
// Run Scene
export type run_scene_api_scenes__scene_id__execute_post = { path: "/api/scenes/{scene_id}/execute"; method: "POST" };
// Duplicate Scene
export type duplicate_scene_api_scenes__scene_id__copy_post = { path: "/api/scenes/{scene_id}/copy"; method: "POST" };
// Get Logs
export type get_logs_api_scenes__scene_id__logs_get = { path: "/api/scenes/{scene_id}/logs"; method: "GET" };
// Get Scene Preview
export type get_scene_preview_api_scenes__scene_id__preview_post = { path: "/api/scenes/{scene_id}/preview"; method: "POST" };
// Batch Change Enabled
export type batch_change_enabled_api_scenes_batch_enabled_post = { path: "/api/scenes/batch/enabled"; method: "POST" };
// Batch Set Schedule
export type batch_set_schedule_api_scenes_batch_schedule_post = { path: "/api/scenes/batch/schedule"; method: "POST" };
// Login
export type login_api_auth_login_post = { path: "/api/auth/login"; method: "POST" };
// Register
export type register_api_auth_register_post = { path: "/api/auth/register"; method: "POST" };
// Logout
export type logout_api_auth_logout_post = { path: "/api/auth/logout"; method: "POST" };