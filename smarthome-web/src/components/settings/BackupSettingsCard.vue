<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import type { BackupSettings, SettingsState } from '../../types/settings'
import SettingsSectionCard from './SettingsSectionCard.vue'

defineProps<{
  backup: BackupSettings
}>()

const emit = defineEmits<{
  export: []
  import: [settings: SettingsState]
}>()

const fileInput = ref<HTMLInputElement | null>(null)

const selectBackupFile = () => {
  fileInput.value?.click()
}

const readBackupFile = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]

  if (!file) {
    return
  }

  const reader = new FileReader()

  reader.onload = () => {
    try {
      emit('import', JSON.parse(String(reader.result)) as SettingsState)
      ElMessage.success('配置已导入')
    } catch {
      ElMessage.error('备份文件格式不正确')
    } finally {
      target.value = ''
    }
  }

  reader.readAsText(file)
}
</script>

<template>
  <SettingsSectionCard id="backup" icon="▤" title="备份恢复">
    <div class="settings-field"><span>导出配置</span><button class="secondary-button" type="button" @click="emit('export')">导出</button></div>
    <div class="settings-field">
      <span>导入备份</span>
      <button class="secondary-button" type="button" @click="selectBackupFile">导入</button>
      <input ref="fileInput" class="hidden" accept="application/json" type="file" @change="readBackupFile" />
    </div>
    <div class="settings-field"><span>自动备份</span><el-switch v-model="backup.autoBackup" /></div>
    <div class="settings-field"><span>最近备份时间</span><strong class="text-sm font-semibold text-[var(--color-text-secondary)]">{{ backup.lastBackupTime }}</strong></div>
  </SettingsSectionCard>
</template>
