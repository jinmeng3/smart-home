<script setup lang="ts">
import { computed, ref } from 'vue'
import type { HomeAssistantSettings } from '../../types/settings'
import SettingsSectionCard from './SettingsSectionCard.vue'

const props = defineProps<{
  homeAssistant: HomeAssistantSettings
}>()

const emit = defineEmits<{
  sync: []
}>()

const showToken = ref(false)
const connected = computed(() => props.homeAssistant.websocketStatus === 'connected')
const statusClass = computed(() => (connected.value ? 'status-online' : 'status-offline'))
const statusText = computed(() => (connected.value ? '● 已连接' : '● 未连接'))

const syncDevices = () => {
  emit('sync')
}
</script>

<template>
  <SettingsSectionCard id="homeAssistant" icon="⌘" title="平台接入">
    <label class="settings-field"><span>服务地址</span><input v-model="homeAssistant.serviceUrl" class="settings-input" /></label>
    <label class="settings-field">
      <span>Access Token</span>
      <div class="relative min-w-[320px]">
        <input v-model="homeAssistant.accessToken" class="settings-input w-full pr-10" :type="showToken ? 'text' : 'password'" />
        <button class="absolute right-2 top-1/2 -translate-y-1/2 text-[var(--color-text-tertiary)]" type="button" @click="showToken = !showToken">●</button>
      </div>
    </label>
    <div class="settings-field">
      <span>WebSocket 状态</span>
      <span class="device-status-label rounded-lg px-3 py-1 text-sm font-semibold" :class="statusClass">{{ statusText }}</span>
    </div>
    <button class="secondary-button mx-auto mt-3" :disabled="!connected" type="button" @click="syncDevices">同步设备</button>
  </SettingsSectionCard>
</template>
