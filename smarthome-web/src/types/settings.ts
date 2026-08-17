export type ThemeMode = 'light' | 'dark' | 'system'
export type FontSize = 'small' | 'medium' | 'large'
export type WebSocketStatus = 'connected' | 'disconnected'

export interface AccountSettings {
  id?: number
  username: string
  email: string
  avatarUrl?: string | null
  familyName: string
  householdId?: number
  householdAddress?: string | null
  householdTimezone?: string
  role: string
  members?: HouseholdMember[]
}

export interface AppearanceSettings {
  themeMode: ThemeMode
  fontSize: FontSize
  animationsEnabled: boolean
  performanceMode: boolean
}

export interface ModelAdvancedSettings {
  language: 'zh-CN' | 'en-US' | 'auto'
  detailLevel: number
  temperature: number
  maxTokens: number
}

export interface AiAssistantSettings extends ModelAdvancedSettings {
  model: string
  autoExecuteLowRisk: boolean
  confirmHighRisk: boolean
}

export interface HomeAssistantSettings {
  serviceUrl: string
  accessToken: string
  parameters: string
  tokenConfigured: boolean
  websocketStatus: WebSocketStatus
}

export interface NotificationSettings {
  deviceOffline: boolean
  securityAlerts: boolean
  automationResults: boolean
  quietStart: string
  quietEnd: string
}

export interface SecuritySettings {
  twoFactorEnabled: boolean
}

export interface BackupSettings {
  autoBackup: boolean
  lastBackupTime: string
}

export interface SettingsSummary {
  currentHome: string
  accountStatus: string
  homeAssistantStatus: 'online' | 'offline'
  lastSync: string
}

export interface SettingsSuggestionItem {
  id: string
  target: SettingsSectionId
  title: string
  description: string
}

export type SettingsSectionId = 'account' | 'appearance' | 'ai' | 'homeAssistant' | 'notifications' | 'security' | 'backup'

export interface SettingsState {
  account: AccountSettings
  appearance: AppearanceSettings
  aiAssistant: AiAssistantSettings
  homeAssistant: HomeAssistantSettings
  notifications: NotificationSettings
  security: SecuritySettings
  backup: BackupSettings
  summary: SettingsSummary
  suggestions: SettingsSuggestionItem[]
}

export interface UserPreferences {
  appearance: AppearanceSettings
  aiAssistant: Pick<AiAssistantSettings, 'detailLevel' | 'autoExecuteLowRisk' | 'confirmHighRisk'>
  notifications: NotificationSettings
  security: SecuritySettings
  backup: Pick<BackupSettings, 'autoBackup'>
}

export type HouseholdRole = 'admin' | 'member'

// === 表单与展示类型 (原 types/account.ts) ===

export interface AccountForm {
  name: string;
  email: string;
  avatarUrl: string | null;
  householdName: string;
  address: string;
  timezone: string;
}

/** 成员列表展示用的轻量类型，与 HouseholdMember 字段对应 */
export interface FamilyMember {
  id: number;
  name: string;
  email: string;
  avatarUrl: string | null;
  role: HouseholdRole;
}

export interface HouseholdMember {
  membershipId: number
  userId: number
  name: string
  email: string
  avatarUrl: string | null
  role: HouseholdRole
  joinedAt: string
}

/** 全局家庭上下文：家庭列表项 + 当前用户在其中的角色 */
export interface HouseholdContext {
  id: number
  name: string
  address: string | null
  timezone: string
  role: HouseholdRole
  memberCount: number
}

export interface SecurityDevice {
  id: number
  name: string
  location: string
  lastActive: string
  trusted: boolean
  current: boolean
}

export interface SecurityLog {
  id: number
  title: string
  detail: string
  at: string
}

export interface SecurityMeta {
  passwordUpdatedAt: string | null
  devices: SecurityDevice[]
  logs: SecurityLog[]
}

export interface BackupRecord {
  id: number
  type: 'manual' | 'auto'
  at: string
  note: string
}
