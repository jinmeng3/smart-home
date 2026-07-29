import { ref } from 'vue'
import type { AgentExecutionStep, AgentStatus } from '../types/animation'

const defaultSteps = (): AgentExecutionStep[] => [
  { id: 'understand', label: '正在理解指令', status: 'pending' },
  { id: 'query', label: '正在查询设备', status: 'pending' },
  { id: 'execute', label: '正在执行控制', status: 'pending' },
  { id: 'verify', label: '正在验证设备状态', status: 'pending' },
]

export const useAgentStatus = () => {
  const agentStatus = ref<AgentStatus>('idle')
  const executionSteps = ref<AgentExecutionStep[]>(defaultSteps())
  let timeoutIds: number[] = []

  const clearTimers = () => {
    timeoutIds.forEach((id) => window.clearTimeout(id))
    timeoutIds = []
  }

  const resetSteps = () => {
    executionSteps.value = defaultSteps()
  }

  const runThinkingFlow = (onComplete: () => void) => {
    clearTimers()
    resetSteps()
    agentStatus.value = 'thinking'

    timeoutIds.push(
      window.setTimeout(() => {
        agentStatus.value = 'executing'
      }, 650),
    )

    executionSteps.value.forEach((step, index) => {
      timeoutIds.push(
        window.setTimeout(() => {
          executionSteps.value = executionSteps.value.map((item, itemIndex) => {
            if (itemIndex < index) {
              return { ...item, status: 'completed' }
            }

            if (item.id === step.id) {
              return { ...item, status: 'executing' }
            }

            return item
          })
        }, 900 + index * 360),
      )
    })

    timeoutIds.push(
      window.setTimeout(() => {
        executionSteps.value = executionSteps.value.map((step) => ({ ...step, status: 'completed' }))
        agentStatus.value = 'success'
        onComplete()
      }, 2500),
    )

    timeoutIds.push(
      window.setTimeout(() => {
        agentStatus.value = 'idle'
        resetSteps()
      }, 3200),
    )
  }

  return {
    agentStatus,
    clearTimers,
    executionSteps,
    runThinkingFlow,
  }
}
