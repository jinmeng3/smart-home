<script setup lang="ts">
import type { AiAssistantSettings } from '../../types/settings'
import SettingsSectionCard from './SettingsSectionCard.vue'

defineProps<{
  ai: AiAssistantSettings
}>()
</script>

<template>
  <SettingsSectionCard id="ai" icon="✦" title="智能助手">
    <label class="settings-field"><span>模型选择</span><select v-model="ai.model" class="settings-input"><option>Orion GPT-4o</option><option>Orion GPT-4 Turbo</option></select></label>
    <label class="settings-field"><span>回复语言</span><select v-model="ai.language" class="settings-input"><option>简体中文</option><option>English</option></select></label>
    <label class="settings-field">
      <span>回复详细程度</span>
      <div class="flex min-w-[220px] items-center gap-3">
        <input v-model.number="ai.detailLevel" class="accent-[var(--color-primary-600)]" max="100" min="0" type="range" />
        <strong class="w-10 text-[var(--color-primary-600)]">{{ ai.detailLevel }}%</strong>
      </div>
    </label>
    <div class="settings-field"><span>低风险操作自动执行</span><el-switch v-model="ai.autoExecuteLowRisk" /></div>
    <div class="settings-field"><span>高风险操作二次确认</span><el-switch v-model="ai.confirmHighRisk" /></div>
  </SettingsSectionCard>
</template>
