import { computed, onScopeDispose, shallowRef, ref } from 'vue'
import { defineStore } from 'pinia'
import { automations as mockAutomations, devices as mockDevices, messages as mockMessages, recentConversations } from '../mock/home'
import { useBatchedDeviceUpdates, type DeviceUpdate } from '../composables/useBatchedDeviceUpdates'
import type { Automation } from '../types/automation'
import type { ChatMessage } from '../types/chat'
import type { Device } from '../types/device'
import type { AgentExecutionStep, AgentStatus } from '../types/animation'

const createMessageId = () => `message-${Date.now()}-${Math.random().toString(16).slice(2)}`
const currentTime = () => new Intl.DateTimeFormat('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false }).format(new Date())

const createExecutionSteps = (): AgentExecutionStep[] => [
  { id: 'understand', label: '正在理解指令', status: 'pending' },
  { id: 'query', label: '正在查询设备', status: 'pending' },
  { id: 'execute', label: '正在执行控制', status: 'pending' },
  { id: 'verify', label: '正在验证设备状态', status: 'pending' },
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
    messages.value.push({
      id: createMessageId(),
      role: 'assistant',
      content: '已收到，我会结合当前设备状态、自动化计划和能耗数据给出控制建议。',
      timestamp: currentTime(),
    })

    replyTimerIds.push(
      window.setTimeout(() => {
        agentStatus.value = 'idle'
        resetExecutionSteps()
      }, 700),
    )
  }

  const runAgentFlow = () => {
    clearReplyTimers()
    resetExecutionSteps()
    agentStatus.value = 'thinking'

    replyTimerIds.push(
      window.setTimeout(() => {
        agentStatus.value = 'executing'
      }, 650),
    )

    executionSteps.value.forEach((step, index) => {
      replyTimerIds.push(
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

    replyTimerIds.push(window.setTimeout(finishAiReply, 2500))
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

    runAgentFlow()
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
