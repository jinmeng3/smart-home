<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import {
  ElButton,
  ElDialog,
  ElInputNumber,
  ElMessage,
  ElMessageBox,
  ElOption,
  ElSelect,
  ElSlider,
} from 'element-plus'
import type { AiAssistantSettings, ModelAdvancedSettings } from '../../types/settings'
import { useSettingsStore } from '../../stores/settings'
import SettingsSectionCard from './SettingsSectionCard.vue'
import 'element-plus/theme-chalk/el-dialog.css'
import 'element-plus/theme-chalk/el-input-number.css'
import 'element-plus/theme-chalk/el-message.css'
import 'element-plus/theme-chalk/el-message-box.css'
import 'element-plus/theme-chalk/el-overlay.css'
import 'element-plus/theme-chalk/el-select.css'
import 'element-plus/theme-chalk/el-slider.css'

const props = defineProps<{
  ai: AiAssistantSettings
}>()

const settingsStore = useSettingsStore()
const dialogVisible = ref(false)
const saving = ref(false)
const savedDraft = ref('')
const draft = reactive<ModelAdvancedSettings>({
  language: 'zh-CN',
  detailLevel: 70,
  temperature: 0.7,
  maxTokens: 4096,
})

const languageOptions: Array<{
  label: string
  value: ModelAdvancedSettings['language']
}> = [
  { label: '简体中文', value: 'zh-CN' },
  { label: 'English', value: 'en-US' },
  { label: '自动检测', value: 'auto' },
]
const tokenPresets = [2048, 4096, 8192]
const currentDraft = computed(() => JSON.stringify(draft))
const hasUnsavedChanges = computed(() => currentDraft.value !== savedDraft.value)

const copyCurrentSettings = () => {
  Object.assign(draft, {
    language: props.ai.language,
    detailLevel: props.ai.detailLevel,
    temperature: props.ai.temperature,
    maxTokens: props.ai.maxTokens,
  })
  savedDraft.value = currentDraft.value
}

const openDialog = () => {
  copyCurrentSettings()
  dialogVisible.value = true
}

const confirmDiscard = async () => {
  if (!hasUnsavedChanges.value) {
    return true
  }

  try {
    await ElMessageBox.confirm('当前设置尚未应用，确定放弃修改吗？', '放弃修改', {
      confirmButtonText: '放弃',
      cancelButtonText: '继续编辑',
      type: 'warning',
    })
    return true
  } catch {
    return false
  }
}

const requestClose = async () => {
  if (saving.value || !(await confirmDiscard())) {
    return
  }

  dialogVisible.value = false
}

const handleBeforeClose = async (done: () => void) => {
  if (saving.value || !(await confirmDiscard())) {
    return
  }

  done()
}

const validateDraft = () => {
  if (draft.temperature < 0 || draft.temperature > 2) {
    ElMessage.warning('创造性必须在 0 到 2 之间')
    return false
  }

  if (!Number.isInteger(draft.maxTokens) || draft.maxTokens < 1 || draft.maxTokens > 32768) {
    ElMessage.warning('回复长度上限必须是 1 到 32768 之间的整数')
    return false
  }

  return true
}

const applySettings = async () => {
  if (!validateDraft()) {
    return
  }

  const previousSettings: ModelAdvancedSettings = {
    language: props.ai.language,
    detailLevel: props.ai.detailLevel,
    temperature: props.ai.temperature,
    maxTokens: props.ai.maxTokens,
  }

  Object.assign(props.ai, draft)
  saving.value = true

  try {
    await settingsStore.saveAIModel()
    savedDraft.value = currentDraft.value
    dialogVisible.value = false
    ElMessage.success('模型高级设置已保存')
  } catch (error) {
    Object.assign(props.ai, previousSettings)
    ElMessage.error(error instanceof Error ? error.message : '模型高级设置保存失败')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <SettingsSectionCard id="ai" icon="✦" title="智能助手">
    <label class="settings-field">
      <span>模型选择</span>
      <select v-model="ai.model" class="settings-input">
        <option>Orion GPT-4o</option>
        <option>Orion GPT-4 Turbo</option>
      </select>
    </label>
    <div class="settings-field"><span>低风险操作自动执行</span><el-switch v-model="ai.autoExecuteLowRisk" /></div>
    <div class="settings-field"><span>高风险操作二次确认</span><el-switch v-model="ai.confirmHighRisk" /></div>
    <div class="settings-field">
      <span>模型高级参数</span>
      <ElButton plain type="primary" @click="openDialog">更多设置</ElButton>
    </div>
  </SettingsSectionCard>

  <ElDialog
    v-model="dialogVisible"
    :before-close="handleBeforeClose"
    :close-on-click-modal="true"
    :close-on-press-escape="true"
    :lock-scroll="true"
    :modal="true"
    :show-close="false"
    append-to-body
    class="model-advanced-dialog"
    modal-class="model-advanced-overlay"
    width="680px"
  >
    <template #header>
      <header class="dialog-header">
        <span class="ai-icon" aria-hidden="true">✦</span>
        <div>
          <h2>模型高级设置</h2>
          <p>调整回复的创造性和长度上限</p>
        </div>
        <ElButton aria-label="关闭" class="close-button" text @click="requestClose">×</ElButton>
      </header>
    </template>

    <div class="model-status">
      <span>当前模型</span>
      <strong>{{ ai.model }}</strong>
      <span class="active-status"><i />配置生效中</span>
    </div>

    <div class="settings-grid">
      <section class="setting-card">
        <div class="setting-title">
          <div><strong>回复语言</strong><span>Response language</span></div>
        </div>
        <p>选择助手默认使用的回复语言。</p>
        <ElSelect v-model="draft.language" class="full-width">
          <ElOption
            v-for="option in languageOptions"
            :key="option.value"
            :label="option.label"
            :value="option.value"
          />
        </ElSelect>
      </section>

      <section class="setting-card">
        <div class="setting-title">
          <div><strong>回复详细程度</strong><span>Detail level</span></div>
          <output>{{ draft.detailLevel }}%</output>
        </div>
        <p>数值越高，回复会包含更多背景和步骤。</p>
        <ElSlider v-model="draft.detailLevel" :max="100" :min="0" :show-tooltip="false" />
        <div class="range-labels"><span>简洁</span><span>均衡</span><span>详细</span></div>
      </section>

      <section class="setting-card">
        <div class="setting-title">
          <div><strong>创造性</strong><span>Temperature</span></div>
          <output>{{ draft.temperature.toFixed(1) }}</output>
        </div>
        <p>数值越低越稳定，越高则更有创造性。</p>
        <ElSlider
          v-model="draft.temperature"
          :max="2"
          :min="0"
          :show-tooltip="false"
          :step="0.1"
        />
        <div class="range-labels"><span>精确 0</span><span>均衡 1</span><span>创意 2</span></div>
      </section>

      <section class="setting-card">
        <div class="setting-title">
          <div><strong>回复长度上限</strong><span>Max tokens</span></div>
          <output>{{ draft.maxTokens.toLocaleString() }}</output>
        </div>
        <p>控制单次回复最多可生成的 token 数量。</p>
        <ElInputNumber
          v-model="draft.maxTokens"
          :max="32768"
          :min="1"
          :step="256"
          class="full-width"
          controls-position="right"
        />
        <div class="token-presets">
          <ElButton
            v-for="value in tokenPresets"
            :key="value"
            :type="draft.maxTokens === value ? 'primary' : 'default'"
            plain
            size="small"
            @click="draft.maxTokens = value"
          >
            {{ value }}
          </ElButton>
        </div>
      </section>
    </div>

    <template #footer>
      <footer class="dialog-footer">
        <p>设置将在保存页面更改后应用到新的对话</p>
        <div>
          <ElButton :disabled="saving" @click="requestClose">取消</ElButton>
          <ElButton :loading="saving" type="primary" @click="applySettings">应用设置</ElButton>
        </div>
      </footer>
    </template>
  </ElDialog>
</template>

<style scoped>
:global(.model-advanced-dialog) {
  overflow: hidden;
  border: 1px solid var(--color-border-default);
  border-radius: 20px;
  background: var(--color-panel-background);
  box-shadow: 0 24px 70px rgb(15 23 42 / 22%);
}

:global(.model-advanced-overlay) {
  background: rgb(15 23 42 / 45%);
  backdrop-filter: blur(4px);
}

:global(.model-advanced-dialog .el-dialog__header),
:global(.model-advanced-dialog .el-dialog__body),
:global(.model-advanced-dialog .el-dialog__footer) {
  padding: 0;
}

.dialog-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 17px 20px 14px;
  border-bottom: 1px solid var(--color-divider);
  background: linear-gradient(135deg, rgb(59 130 246 / 10%), transparent 62%);
}

.ai-icon {
  display: grid;
  width: 36px;
  height: 36px;
  flex: 0 0 36px;
  place-items: center;
  border-radius: 11px;
  color: white;
  font-size: 18px;
  background: linear-gradient(135deg, var(--color-primary-600), #60a5fa);
  box-shadow: 0 8px 20px rgb(59 130 246 / 24%);
}

.dialog-header h2 {
  color: var(--color-text-primary);
  font-size: 17px;
  font-weight: 800;
}

.dialog-header p {
  margin-top: 2px;
  color: var(--color-text-tertiary);
  font-size: 12px;
}

.close-button {
  margin: -4px -6px 0 auto;
  color: var(--color-text-tertiary);
  font-size: 22px;
}

.model-status {
  display: flex;
  align-items: center;
  gap: 9px;
  margin: 13px 20px 0;
  padding: 9px 12px;
  border: 1px solid var(--color-divider);
  border-radius: 11px;
  color: var(--color-text-tertiary);
  font-size: 12px;
  background: var(--color-workspace-background);
}

.model-status strong {
  color: var(--color-text-primary);
}

.active-status {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: auto;
  color: var(--color-success);
  font-weight: 700;
}

.active-status i {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentColor;
}

.settings-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  padding: 12px 20px 16px;
}

.setting-card {
  min-width: 0;
  padding: 13px;
  border: 1px solid var(--color-border-default);
  border-radius: 14px;
  background: var(--color-workspace-background);
  transition: border-color 160ms ease, box-shadow 160ms ease, transform 160ms ease;
}

.setting-card:hover {
  border-color: var(--color-border-focus);
  box-shadow: 0 8px 20px rgb(15 23 42 / 6%);
  transform: translateY(-1px);
}

.setting-title {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

.setting-title strong,
.setting-title span {
  display: block;
}

.setting-title strong {
  color: var(--color-text-primary);
  font-size: 13px;
}

.setting-title span {
  margin-top: 1px;
  color: var(--color-text-tertiary);
  font-size: 10px;
}

.setting-title output {
  color: var(--color-primary-600);
  font-size: 15px;
  font-weight: 800;
}

.setting-card > p {
  min-height: 34px;
  margin: 7px 0 5px;
  color: var(--color-text-tertiary);
  font-size: 11px;
  line-height: 1.4;
}

.full-width {
  width: 100%;
}

.range-labels {
  display: flex;
  justify-content: space-between;
  margin-top: -4px;
  color: var(--color-text-tertiary);
  font-size: 9px;
}

.token-presets {
  display: flex;
  gap: 5px;
  margin-top: 7px;
}

.token-presets :deep(.el-button) {
  flex: 1;
  margin-left: 0;
  padding: 5px;
}

.dialog-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 20px;
  border-top: 1px solid var(--color-divider);
  background: var(--color-workspace-background);
}

.dialog-footer p {
  color: var(--color-text-tertiary);
  font-size: 10px;
}

.dialog-footer > div {
  display: flex;
  gap: 8px;
}

@media (max-width: 640px) {
  :global(.model-advanced-dialog) {
    width: calc(100% - 24px) !important;
  }

  .settings-grid {
    grid-template-columns: 1fr;
  }

  .dialog-footer {
    align-items: stretch;
    flex-direction: column;
  }

  .dialog-footer > div {
    justify-content: flex-end;
  }
}
</style>
