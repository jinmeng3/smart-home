import { computed, onScopeDispose, ref, shallowRef } from 'vue'
import { defineStore } from 'pinia'
import { streamChatCompletion } from '../api/chat'
import { automations as mockAutomations, devices as mockDevices, messages as mockMessages, recentConversations } from '../mock/home'
import { useBatchedDeviceUpdates, type DeviceUpdate } from '../composables/useBatchedDeviceUpdates'
import type { AgentExecutionStep, AgentStatus } from '../types/animation'
import type { Automation } from '../types/automation'
import type { ChatMessage } from '../types/chat'
import type { Device } from '../types/device'

const createMessageId = () => `message-${Date.now()}-${Math.random().toString(16).slice(2)}`
const currentTime = () => new Intl.DateTimeFormat('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false }).format(new Date())

const createExecutionSteps = (): AgentExecutionStep[] => [
  { id: 'understand', label: '正在理解指令', status: 'pending' },
  { id: 'query', label: '正在请求模型', status: 'pending' },
  { id: 'execute', label: '正在生成回复', status: 'pending' },
  { id: 'verify', label: '正在整理结果', status: 'pending' },
]

export const useHomeStore = defineStore('home', () => {
  const activeMenu = ref('智能对话')
  const sidebarCollapsed = ref(false)
  const selectedDeviceId = ref<string | null>(null)
  const deviceDrawerOpen = ref(false)
  const deviceIds = shallowRef<string[]>(mockDevices.map((device) => device.id))
  const devicesById = shallowRef<Record<string, Device>>(
    mockDevices.reduce<Record<string, Device>>((record, device) => {
      record[device.id] = device
      return record
    }, {}),
  )
  const automations = ref<Automation[]>(mockAutomations)
  const messages = ref<ChatMessage[]>(mockMessages)
  const agentStatus = ref<AgentStatus>('idle')
  const executionSteps = ref<AgentExecutionStep[]>(createExecutionSteps())
  const energyToday = ref(18.62)
  const securityAlertHandled = ref(false)
  let replyTimerIds: number[] = []

  const devices = computed(() => deviceIds.value.map((id) => devicesById.value[id]).filter((device): device is Device => Boolean(device)))
  const selectedDevice = computed(() => (selectedDeviceId.value ? devicesById.value[selectedDeviceId.value] ?? null : null))

  const deviceSummary = computed(() => {
    const online = devices.value.filter((device) => device.online).length

    return {
      online,
      offline: devices.value.length - online,
      total: 26,
    }
  })

  const hasWarning = computed(() => deviceSummary.value.offline > 0 || !securityAlertHandled.value)
  const enabledAutomationCount = computed(() => automations.value.filter((automation) => automation.enabled).length)
  const alertCount = computed(() => (securityAlertHandled.value ? 0 : 1))

  const clearReplyTimers = () => {
    replyTimerIds.forEach((id) => window.clearTimeout(id))
    replyTimerIds = []
  }

  const resetExecutionSteps = () => {
    executionSteps.value = createExecutionSteps()
  }

  const setActiveMenu = (menu: string) => {
    activeMenu.value = menu
  }

  const toggleSidebar = () => {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  const selectDevice = (device: Device) => {
    selectedDeviceId.value = device.id
    deviceDrawerOpen.value = true
  }

  const closeDeviceDrawer = () => {
    deviceDrawerOpen.value = false
  }

  const toggleAutomation = (id: string) => {
    const automation = automations.value.find((item) => item.id === id)

    if (automation) {
      automation.enabled = !automation.enabled
    }
  }

  const commitDeviceUpdates = (updates: DeviceUpdate[]) => {
    const nextDevicesById = { ...devicesById.value }

    updates.forEach((update) => {
      const currentDevice = nextDevicesById[update.id]

      if (!currentDevice) {
        return
      }

      nextDevicesById[update.id] = {
        ...currentDevice,
        status: update.status ?? currentDevice.status,
        value: update.value === undefined ? currentDevice.value : String(update.value),
        updatedAt: update.updatedAt ?? currentDevice.updatedAt,
        online: update.online ?? currentDevice.online,
      }
    })

    devicesById.value = nextDevicesById
  }

  const { queueDeviceUpdate, queueDeviceUpdates } = useBatchedDeviceUpdates(commitDeviceUpdates, (id) => devicesById.value[id])

  const finishAiReply = () => {
    executionSteps.value = executionSteps.value.map((step) => ({ ...step, status: 'completed' }))
    agentStatus.value = 'success'

    replyTimerIds.push(
      window.setTimeout(() => {
        agentStatus.value = 'idle'
        resetExecutionSteps()
      }, 700),
    )
  }

  const runAgentFlow = async () => {
    clearReplyTimers()
    resetExecutionSteps()
    agentStatus.value = 'thinking'
    executionSteps.value = executionSteps.value.map((step, index) => ({
      ...step,
      status: index === 0 ? 'executing' : 'pending',
    }))

    const assistantMessage: ChatMessage = {
      id: createMessageId(),
      role: 'assistant',
      content: '',
      timestamp: currentTime(),
    }

    messages.value.push(assistantMessage)

    try {
      await streamChatCompletion(
        messages.value
          .filter((message) => message.content.trim())
          .slice(-12)
          .map((message) => ({
            role: message.role,
            content: message.content,
          })),
        (delta) => {
          assistantMessage.content += delta
          agentStatus.value = 'executing'
          executionSteps.value = executionSteps.value.map((step) => ({ ...step, status: 'completed' }))
        },
      )

      if (!assistantMessage.content.trim()) {
        assistantMessage.content = '模型没有返回内容。'
      }

      finishAiReply()
    } catch (error) {
      assistantMessage.content = error instanceof Error ? error.message : '请求大模型失败'
      agentStatus.value = 'idle'
      resetExecutionSteps()
    }
  }

  const sendMessage = (content: string) => {
    const trimmedContent = content.trim()

    if (!trimmedContent || agentStatus.value === 'thinking' || agentStatus.value === 'executing') {
      return
    }

    messages.value.push({
      id: createMessageId(),
      role: 'user',
      content: trimmedContent,
      timestamp: currentTime(),
    })

    void runAgentFlow()
  }

  const markAlertHandled = () => {
    securityAlertHandled.value = true
  }

  onScopeDispose(clearReplyTimers)

  return {
    activeMenu,
    alertCount,
    agentStatus,
    automations,
    closeDeviceDrawer,
    deviceDrawerOpen,
    deviceIds,
    devices,
    devicesById,
    deviceSummary,
    enabledAutomationCount,
    energyToday,
    executionSteps,
    hasWarning,
    markAlertHandled,
    messages,
    recentConversations,
    securityAlertHandled,
    selectedDevice,
    queueDeviceUpdate,
    queueDeviceUpdates,
    selectDevice,
    sendMessage,
    setActiveMenu,
    sidebarCollapsed,
    toggleSidebar,
    toggleAutomation,
  }
})
