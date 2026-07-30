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
  sidebarCollapsed: boolean
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

export type HouseholdRole = 'admin' | 'member'

export interface HouseholdMember {
  membershipId: number
  userId: number
  name: string
  email: string
  avatarUrl: string | null
  role: HouseholdRole
  joinedAt: string
}
