export type ThemeMode = 'light' | 'dark' | 'system'
export type FontSize = 'small' | 'medium' | 'large'
export type WebSocketStatus = 'connected' | 'disconnected'

export interface AccountSettings {
  username: string
  email: string
  familyName: string
  role: string
}

export interface AppearanceSettings {
  themeMode: ThemeMode
  fontSize: FontSize
  animationsEnabled: boolean
  sidebarCollapsed: boolean
}

export interface AiAssistantSettings {
  model: string
  language: string
  detailLevel: number
  autoExecuteLowRisk: boolean
  confirmHighRisk: boolean
}

export interface HomeAssistantSettings {
  serviceUrl: string
  accessToken: string
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
