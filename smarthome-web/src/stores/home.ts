import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { automations as mockAutomations, devices as mockDevices, messages as mockMessages, recentConversations } from '../mock/home'
import type { Automation } from '../types/automation'
import type { ChatMessage } from '../types/chat'
import type { Device } from '../types/device'

const createMessageId = () => `message-${Date.now()}-${Math.random().toString(16).slice(2)}`
const currentTime = () => new Intl.DateTimeFormat('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false }).format(new Date())

export const useHomeStore = defineStore('home', () => {
  const activeMenu = ref('智能对话')
  const sidebarCollapsed = ref(false)
  const selectedDevice = ref<Device | null>(null)
  const devices = ref<Device[]>(mockDevices)
  const automations = ref<Automation[]>(mockAutomations)
  const messages = ref<ChatMessage[]>(mockMessages)

  const deviceSummary = computed(() => {
    const online = devices.value.filter((device) => device.online).length

    return {
      online,
      offline: devices.value.length - online,
      total: 26,
    }
  })

  const enabledAutomationCount = computed(() => automations.value.filter((automation) => automation.enabled).length)

  const setActiveMenu = (menu: string) => {
    activeMenu.value = menu
  }

  const toggleSidebar = () => {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  const selectDevice = (device: Device) => {
    selectedDevice.value = device
  }

  const toggleAutomation = (id: string) => {
    const automation = automations.value.find((item) => item.id === id)

    if (automation) {
      automation.enabled = !automation.enabled
    }
  }

  const sendMessage = (content: string) => {
    const trimmedContent = content.trim()

    if (!trimmedContent) {
      return
    }

    messages.value.push({
      id: createMessageId(),
      role: 'user',
      content: trimmedContent,
      timestamp: currentTime(),
    })

    window.setTimeout(() => {
      messages.value.push({
        id: createMessageId(),
        role: 'assistant',
        content: '已收到，我会结合当前设备状态、自动化计划和能耗数据给出控制建议。',
        timestamp: currentTime(),
      })
    }, 500)
  }

  return {
    activeMenu,
    automations,
    devices,
    deviceSummary,
    enabledAutomationCount,
    messages,
    recentConversations,
    selectedDevice,
    selectDevice,
    sendMessage,
    setActiveMenu,
    sidebarCollapsed,
    toggleSidebar,
    toggleAutomation,
  }
})
