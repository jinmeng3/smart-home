export type AgentStatus = 'idle' | 'thinking' | 'executing' | 'success' | 'error'

export type DeviceStatus = 'online' | 'offline' | 'running' | 'warning'

export type SuggestionStatus = 'pending' | 'executing' | 'completed' | 'failed'

export interface AgentExecutionStep {
  id: string
  label: string
  status: SuggestionStatus
  message?: string
}
