export type DeviceCategory = 'light' | 'climate' | 'lock' | 'camera' | 'energy' | 'air'

export type SemanticStatus = 'online' | 'offline' | 'running' | 'warning' | 'error' | 'success'

export interface StatusColorConfig {
  textClass: string
  backgroundClass: string
  borderClass: string
  dotClass: string
}
