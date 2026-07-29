import { ref } from 'vue'
import { defineStore } from 'pinia'
import { defaultSettings } from '../mock/settings'
import type { SettingsState } from '../types/settings'

const cloneSettings = (): SettingsState => structuredClone(defaultSettings)

export const useSettingsStore = defineStore('settings', () => {
  const settings = ref<SettingsState>(cloneSettings())
  const savedAt = ref<string | null>(null)
  const saveStatus = ref<'idle' | 'saved'>('idle')

  const saveSettings = () => {
    savedAt.value = new Intl.DateTimeFormat('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    }).format(new Date())
    saveStatus.value = 'saved'

    window.setTimeout(() => {
      saveStatus.value = 'idle'
    }, 1600)
  }

  const resetSettings = () => {
    settings.value = cloneSettings()
    saveStatus.value = 'idle'
  }

  const syncDevices = () => {
    settings.value.summary.lastSync = '刚刚'
  }

  return {
    resetSettings,
    saveSettings,
    saveStatus,
    savedAt,
    settings,
    syncDevices,
  }
})
