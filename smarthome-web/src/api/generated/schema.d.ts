// 自动生成，请勿手动修改。
// 生成时间: 2026-09-02T13:26:17.162Z
// 来源: local file E:\File\practice\smart-home\smarthome-api\openapi.json

export interface AIAssistantPreferences {
  language?: "zh-CN" | "en-US" | "auto";
  detailLevel?: number;
  autoExecuteLowRisk?: boolean;
  confirmHighRisk?: boolean;
}

export interface AIModelCreate {
  name: string;
  provider: string;
  api?: "openai-completions" | "openai-responses" | "azure-openai-responses" | "openai-codex-responses" | "anthropic-messages" | "bedrock-converse-stream";
  api_endpoint: string;
  api_key?: unknown | unknown;
  parameters?: Record<string, unknown>;
  reasoning?: boolean;
  thinking_level_map?: unknown | unknown;
  context_window?: unknown | unknown;
  max_tokens?: number;
  cost?: unknown | unknown;
  headers?: unknown | unknown;
  compat?: unknown | unknown;
  is_active?: boolean;
  description?: unknown | unknown;
}

export interface AIModelProviderRead {
  id: string;
}

export interface AIModelRead {
  id: number;
  name: string;
  provider: string;
  api?: string;
  api_endpoint: string;
  parameters: Record<string, unknown>;
  compat?: unknown | unknown;
  temperature: number;
  max_tokens: number;
  is_active: boolean;
  has_api_key: boolean;
  description: unknown | unknown;
  created_at: string;
  updated_at: unknown | unknown;
}

export interface AIModelTestRequest {
  name: string;
  provider: string;
  api?: string;
  api_endpoint: string;
  api_key?: unknown | unknown;
  parameters?: Record<string, unknown>;
  compat?: unknown | unknown;
  temperature?: number;
  max_tokens?: number;
}

export interface AIModelTestResult {
  ok: boolean;
  latency_ms?: unknown | unknown;
  message: string;
}

export interface AIModelUpdate {
  name?: unknown | unknown;
  provider?: unknown | unknown;
  api?: unknown | unknown;
  api_endpoint?: unknown | unknown;
  api_key?: unknown | unknown;
  parameters?: unknown | unknown;
  compat?: unknown | unknown;
  temperature?: unknown | unknown;
  max_tokens?: unknown | unknown;
  is_active?: unknown | unknown;
  description?: unknown | unknown;
}

export interface AccountRead {
  id: number;
  name: string;
  email: string;
  avatar_url: unknown | unknown;
  created_at: string;
  updated_at: string;
}

export interface AccountUpdate {
  name?: unknown | unknown;
  email?: unknown | unknown;
}

export interface ActionWrite {
  type: string;
  config?: Record<string, unknown>;
  position: number;
  deviceId?: unknown | unknown;
  sceneId?: unknown | unknown;
}

export interface AgentDecisionRequest {
  household_id: number;
  approval_id: string;
  decision: "approve" | "reject";
}

export interface AgentRunRequest {
  session_id: number;
  household_id: number;
  household_name?: unknown | unknown;
  model?: unknown | unknown;
  message: string;
  tools_enabled?: boolean;
}

export interface AiSuggestionItem {
  id: string;
  target: "account" | "appearance" | "ai" | "homeAssistant" | "notifications" | "security" | "backup";
  title: string;
  description: string;
}

export interface AiSuggestionsRead {
  suggestions?: AiSuggestionItem[];
  cached?: boolean;
}

export interface AiTemplatesRead {
  templates?: AutomationTemplateItem[];
  cached?: boolean;
}

export interface AiTemplatesRequest {
  device_summary?: DeviceSummary;
  count?: number;
  force?: boolean;
}

export interface ApiResponse_AIModelRead_ {
  code?: number;
  message?: string;
  data?: AIModelRead | unknown;
}

export interface ApiResponse_AIModelTestResult_ {
  code?: number;
  message?: string;
  data?: AIModelTestResult | unknown;
}

export interface ApiResponse_AccountRead_ {
  code?: number;
  message?: string;
  data?: AccountRead | unknown;
}

export interface ApiResponse_AiSuggestionsRead_ {
  code?: number;
  message?: string;
  data?: AiSuggestionsRead | unknown;
}

export interface ApiResponse_AiTemplatesRead_ {
  code?: number;
  message?: string;
  data?: AiTemplatesRead | unknown;
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
  data?: null;
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

export interface ApiResponse_RoomEnvironmentLatestRead_ {
  code?: number;
  message?: string;
  data?: RoomEnvironmentLatestRead | unknown;
}

export interface ApiResponse_RoomEnvironmentReportRead_ {
  code?: number;
  message?: string;
  data?: RoomEnvironmentReportRead | unknown;
}

export interface ApiResponse_RoomEnvironmentTrendRead_ {
  code?: number;
  message?: string;
  data?: RoomEnvironmentTrendRead | unknown;
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

export interface ApiResponse_SecurityDeviceRead_ {
  code?: number;
  message?: string;
  data?: SecurityDeviceRead | unknown;
}

export interface ApiResponse_SecurityLogRead_ {
  code?: number;
  message?: string;
  data?: SecurityLogRead | unknown;
}

export interface ApiResponse_SecurityMetaRead_ {
  code?: number;
  message?: string;
  data?: SecurityMetaRead | unknown;
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

export interface ApiResponse_TodayEnergyRead_ {
  code?: number;
  message?: string;
  data?: TodayEnergyRead | unknown;
}

export interface ApiResponse_Union_ScheduleRead__NoneType__ {
  code?: number;
  message?: string;
  data?: ScheduleRead | unknown;
}

export interface ApiResponse_UserPreferencesWrite_ {
  code?: number;
  message?: string;
  data?: UserPreferencesWrite | unknown;
}

export interface ApiResponse_list_AIModelProviderRead__ {
  code?: number;
  message?: string;
  data?: unknown | unknown;
}

export interface ApiResponse_list_AIModelRead__ {
  code?: number;
  message?: string;
  data?: unknown | unknown;
}

export interface ApiResponse_list_ChatMessageRead__ {
  code?: number;
  message?: string;
  data?: unknown | unknown;
}

export interface ApiResponse_list_ChatSessionRead__ {
  code?: number;
  message?: string;
  data?: unknown | unknown;
}

export interface ApiResponse_list_HouseholdListItem__ {
  code?: number;
  message?: string;
  data?: unknown | unknown;
}

export interface AppearancePreferences {
  themeMode?: "light" | "dark" | "system";
  fontSize?: "small" | "medium" | "large";
  animationsEnabled?: boolean;
  sidebarCollapsed?: boolean;
  performanceMode?: boolean;
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
  updatedAt: string;
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
  createdAt: string;
  updatedAt: string;
}

export interface AutomationSummary {
  enabled: number;
  total: number;
  running: number;
  executionsToday: number;
  abnormal: number;
}

export interface AutomationTemplateItem {
  name: string;
  description: string;
  trigger_type: "schedule" | "location" | "device" | "manual";
  icon?: string;
  tone?: "purple" | "orange" | "green" | "blue" | "teal" | "red" | "amber";
  device_count?: number;
  triggers?: TemplateTrigger[];
  actions?: TemplateAction[];
}

export interface AutomationUpdate {
  name?: unknown | unknown;
  description?: unknown | unknown;
  enabled?: unknown | unknown;
  triggers?: unknown | unknown;
  conditions?: unknown | unknown;
  actions?: unknown | unknown;
  priority?: unknown | unknown;
  cooldownSeconds?: unknown | unknown;
  delaySeconds?: unknown | unknown;
  note?: unknown | unknown;
  version?: unknown | unknown;
}

export interface AvatarResponse {
  avatar_url: unknown | unknown;
}

export interface BackupPreferences {
  autoBackup?: boolean;
}

export interface BatchEnableRead {
  updatedCount: number;
  unchangedCount: number;
  executionBatchId?: unknown | unknown;
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
  model?: unknown | unknown;
  messages: ChatCompletionMessage[];
  session_id?: unknown | unknown;
  stream?: boolean;
}

export interface ChatMessageRead {
  id: number;
  session_id: number;
  role: string;
  content: string;
  created_at: string;
}

export interface ChatSessionRead {
  id: number;
  title: string;
  household_id?: unknown | unknown;
  mode?: string;
  model_name?: unknown | unknown;
  created_at: string;
  updated_at: string;
}

export interface ConditionWrite {
  type: string;
  config?: Record<string, unknown>;
  position?: unknown | unknown;
}

export interface DeviceBatchGroup {
  group: string; /* 分组名称 */
  device_ids?: number[]; /* 分配到该组的设备，为空则创建分组但不分配 */
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
  device_id?: unknown | unknown;
  firmware?: string;
  icon?: string;
  color?: string;
  image_url?: unknown | unknown;
}

export interface DeviceDetailRead {
  id: number;
  device_id: string;
  name: string;
  room: string;
  type: string;
  brand: string;
  status: "online" | "offline" | "warning" | "running";
  connection: "Home Assistant" | "Matter" | "Zigbee" | "MQTT";
  firmware: string;
  icon?: string;
  color?: string;
  image_url: unknown | unknown;
  last_online: unknown | unknown;
  created_at: string;
  updated_at: string;
}

export interface DeviceDetailWithLogs {
  id: number;
  device_id: string;
  name: string;
  room: string;
  type: string;
  brand: string;
  status: "online" | "offline" | "warning" | "running";
  connection: "Home Assistant" | "Matter" | "Zigbee" | "MQTT";
  firmware: string;
  icon?: string;
  color?: string;
  image_url: unknown | unknown;
  last_online: unknown | unknown;
  created_at: string;
  updated_at: string;
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
  created_at: string;
}

export interface DeviceRead {
  id: number;
  device_id: string;
  name: string;
  room: string;
  type: string;
  brand: string;
  status: "online" | "offline" | "warning" | "running";
  connection: "Home Assistant" | "Matter" | "Zigbee" | "MQTT";
  firmware: string;
  icon?: string;
  color?: string;
  image_url: unknown | unknown;
  last_online: unknown | unknown;
}

export interface DeviceStatus {
}

export interface DeviceSummary {
  online?: number;
  offline?: number;
  by_type?: Record<string, unknown>;
}

export interface DeviceSync {
  platform: "Home Assistant" | "Matter" | "Zigbee" | "MQTT";
}

export interface DeviceSyncRead {
  platform: "Home Assistant" | "Matter" | "Zigbee" | "MQTT";
  synced_count: number;
}

export interface DeviceUpdate {
  name?: unknown | unknown;
  room?: unknown | unknown;
  type?: unknown | unknown;
  brand?: unknown | unknown;
  status?: "online" | "offline" | "warning" | "running" | unknown;
  connection?: "Home Assistant" | "Matter" | "Zigbee" | "MQTT" | unknown;
  firmware?: unknown | unknown;
  icon?: unknown | unknown;
  color?: unknown | unknown;
  image_url?: unknown | unknown;
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
  durationMs: unknown | unknown;
  errorMessage: unknown | unknown;
  startedAt: string;
  finishedAt: unknown | unknown;
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
  address?: unknown | unknown;
  timezone?: string;
}

export interface HouseholdListItem {
  id: number;
  name: string;
  address: unknown | unknown;
  timezone: string;
  created_by: number;
  created_at: string;
  updated_at: string;
  role: string;
  member_count: number;
}

export interface HouseholdRead {
  id: number;
  name: string;
  address: unknown | unknown;
  timezone: string;
  created_by: number;
  created_at: string;
  updated_at: string;
}

export interface HouseholdRole {
}

export interface HouseholdUpdate {
  name?: unknown | unknown;
  address?: unknown | unknown;
  timezone?: unknown | unknown;
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
  avatar_url: unknown | unknown;
  role: HouseholdRole;
  joined_at: string;
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

export interface NotificationPreferences {
  deviceOffline?: boolean;
  securityAlerts?: boolean;
  automationResults?: boolean;
  quietStart?: string;
  quietEnd?: string;
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

export interface PendingApprovalRead {
  approval_id: string;
  run_id: string;
  session_id: number;
  call_id: string;
  tool: string;
  args: Record<string, unknown>;
  risk_level: string;
  reasons: string[];
  preview: Record<string, unknown>;
  resource_version: string;
}

export interface RegenerateRequest {
  target_message_id: number;
  model?: unknown | unknown;
  household_id?: unknown | unknown;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

export interface RoomDetailRead {
  room: RoomRead;
  currentScene?: unknown | unknown;
  recentActivity?: unknown | unknown;
  recentActivityTime?: unknown | unknown;
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
  updatedAt: string;
}

export interface RoomDeviceListRead {
  items: RoomDeviceListItem[];
  total: number;
}

export interface RoomDeviceMetaWrite {
  group?: unknown | unknown;
  favorite?: unknown | unknown;
  sortOrder?: unknown | unknown;
}

export interface RoomDeviceWrite {
  deviceId: number;
  status: DeviceStatus;
}

export interface RoomDevicesWrite {
  devices: RoomDeviceBinding[];
}

export interface RoomEnvironmentLatestRead {
  sampledAt: string;
  values?: Record<string, unknown>;
}

export interface RoomEnvironmentPoint {
  sampledAt: string;
  values?: Record<string, unknown>;
}

export interface RoomEnvironmentReportRead {
  taskId: string;
  status: string;
  downloadUrl?: unknown | unknown;
}

export interface RoomEnvironmentTrendRead {
  metrics?: string[];
  items?: RoomEnvironmentPoint[];
}

export interface RoomInput {
  name: string;
  floor?: string;
  roomType?: string;
  icon?: string;
  themeColor?: string;
  imageUrl?: unknown | unknown;
  area?: number;
  comfort?: number;
  version?: unknown | unknown;
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
  occurredAt: string;
  source: string;
  event: string;
  result: string;
  durationMs: unknown | unknown;
  deviceId: unknown | unknown;
  deviceName: unknown | unknown;
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
  imageUrl: unknown | unknown;
  icon?: string;
  themeColor?: string;
  version?: number;
  area: number;
  comfort: number;
  device?: RoomDeviceListItem[];
  deviceCount?: number;
  onlineCount?: number;
  createdAt: string;
  updatedAt: string;
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
  sceneIds?: string[]; /* 目标场景 ID 列表，为空则操作全部场景 */
  enabled: boolean;
}

export interface SceneBatchScheduleResult {
  updatedCount?: number;
}

export interface SceneBatchScheduleWrite {
  sceneIds?: string[]; /* 目标场景 ID 列表，为空则操作全部场景 */
  triggerType?: "manual" | "schedule" | "location" | "device";
  triggerLabel: string; /* 定时触发描述 */
}

export interface SceneCopyWrite {
  name: string;
}

export interface SceneDraftRead {
  draftId: string;
  updatedAt: string;
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
  highRisk?: unknown | unknown;
  steps?: SceneStepWrite[];
}

export interface SceneEnabledRead {
  id: string;
  enabled: boolean;
  updatedAt: string;
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
  startedAt: string;
  finishedAt: unknown | unknown;
  steps: SceneExecutionStepRead[];
}

export interface SceneExecutionStepRead {
  stepId: string;
  status: string;
  message: unknown | unknown;
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
  source: string;
  startedAt: string;
  finishedAt: unknown | unknown;
  message: unknown | unknown;
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
  sourceTemplateId: unknown | unknown;
  createdAt: string;
  updatedAt: string;
  steps: SceneStepRead[];
}

export interface SceneStepRead {
  name: string;
  description?: string;
  deviceId: string;
  order: number;
  action?: "on" | "off" | "set_temperature" | "set_position" | "noop" | unknown; /* 动作指令（on / off / set_temperature / set_position / noop） */
  actionValue?: unknown | unknown; /* 动作参数（温度 / 开合度 0-100） */
  id: string;
}

export interface SceneStepWrite {
  name: string;
  description?: string;
  deviceId: string;
  order: number;
  action?: "on" | "off" | "set_temperature" | "set_position" | "noop" | unknown; /* 动作指令（on / off / set_temperature / set_position / noop） */
  actionValue?: unknown | unknown; /* 动作参数（温度 / 开合度 0-100） */
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
  name?: unknown | unknown;
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
  highRisk?: unknown | unknown;
  steps?: SceneStepWrite[];
}

export interface ScheduleRead {
  enabled?: boolean;
  repeatDays?: number[];
  targets?: Record<string, unknown>;
  items?: Record<string, unknown>[];
  version: number;
  id: number;
  scheduleDate: string;
  updatedAt: string;
}

export interface ScheduleWrite {
  enabled?: boolean;
  repeatDays?: number[];
  targets?: Record<string, unknown>;
  items?: Record<string, unknown>[];
  version?: unknown | unknown;
}

export interface SecurityDeviceRead {
  id: number;
  device_name: string;
  location: string;
  last_active_at: string;
  trusted: boolean;
  is_current: boolean;
}

export interface SecurityDeviceTrustUpdate {
  trusted: boolean;
}

export interface SecurityLogCreate {
  title: string;
  detail: string;
}

export interface SecurityLogRead {
  id: number;
  title: string;
  detail: string;
  created_at: string;
}

export interface SecurityMetaRead {
  password_updated_at?: unknown | unknown;
  devices?: SecurityDeviceRead[];
  logs?: SecurityLogRead[];
}

export interface SecurityPreferences {
  twoFactorEnabled?: boolean;
}

export interface SessionModeUpdate {
  mode: "agent" | "chat";
}

export interface SessionModelUpdate {
  model_name: string;
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
  affectedDeviceCount?: unknown | unknown;
  checkedCount?: unknown | unknown;
  deviceCount?: unknown | unknown;
  estimatedSeconds?: unknown | unknown;
}

export interface TemplateAction {
  type?: string;
  position?: number;
  deviceId?: unknown | unknown;
  config?: Record<string, unknown>;
  device_type?: unknown | unknown;
  room?: unknown | unknown;
}

export interface TemplateTrigger {
  type: "schedule" | "location" | "device" | "manual";
  config?: Record<string, unknown>;
  description?: unknown | unknown;
}

export interface TodayEnergyRead {
  energy_kwh?: number; /* 今日总能耗（千瓦时） */
  device_count?: number; /* 有能耗记录的设备数 */
  recorded_at?: string; /* 最近记录时间 */
}

export interface UserPreferencesWrite {
  appearance?: AppearancePreferences;
  aiAssistant?: AIAssistantPreferences;
  notifications?: NotificationPreferences;
  security?: SecurityPreferences;
  backup?: BackupPreferences;
}

export interface ValidationError {
  loc: unknown | unknown[];
  msg: string;
  type: string;
  input?: unknown;
  ctx?: Record<string, unknown>;
}

