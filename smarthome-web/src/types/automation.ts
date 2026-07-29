export interface Automation {
  id: string
  name: string
  trigger: string
  actions: string[]
  enabled: boolean
  time: string
  description: string
}
