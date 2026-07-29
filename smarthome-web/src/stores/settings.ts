import { ref, watch } from 'vue'
import { defineStore } from 'pinia'
import { defaultSettings } from '../mock/settings'
import type { SettingsState } from '../types/settings'

const storageKey = 'smart-home-settings'

const cloneSettings = (): SettingsState => structuredClone(defaultSettings)

const loadSettings = (): SettingsState => {
  const savedSettings = window.localStorage.getItem(storageKey)

  if (!savedSettings) {
    return cloneSettings()
  }

  try {
    return {
      ...cloneSettings(),
      ...JSON.parse(savedSettings),
    }
  } catch {
    return cloneSettings()
  }
}

export const useSettingsStore = defineStore('settings', () => {
  const settings = ref<SettingsState>(loadSettings())
  const savedAt = ref<string | null>(null)
  const saveStatus = ref<'idle' | 'saved'>('idle')

  watch(
    settings,
    (currentSettings) => {
      window.localStorage.setItem(storageKey, JSON.stringify(currentSettings))
    },
    { deep: true },
  )

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

  const updateBackupTime = () => {
    settings.value.backup.lastBackupTime = new Intl.DateTimeFormat('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    }).format(new Date())
  }

  const importSettings = (nextSettings: SettingsState) => {
    settings.value = {
      ...cloneSettings(),
      ...nextSettings,
    }
    saveStatus.value = 'idle'
  }

  return {
    importSettings,
    resetSettings,
    saveSettings,
    saveStatus,
    savedAt,
    settings,
    syncDevices,
    updateBackupTime,
  }
})
