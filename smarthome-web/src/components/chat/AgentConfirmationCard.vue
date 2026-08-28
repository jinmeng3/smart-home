<script setup lang="ts">
import { computed } from "vue";
import SvgIcon from "../common/SvgIcon.vue";
import type { PendingApproval } from "../../types/chat";

const props = defineProps<{
  approval: PendingApproval;
  submitting?: boolean;
}>();

defineEmits<{
  approve: [];
  reject: [];
}>();

const preview = computed(() => props.approval.preview);
const kind = computed(() => String(preview.value.kind || ""));
const isSceneExecution = computed(() => kind.value === "scene_execution");
const isAutomationCreate = computed(() => kind.value === "create_automation");
const isAutomationUpdate = computed(() => kind.value === "update_automation");
const isAutomationToggle = computed(() => kind.value === "set_automation_enabled");
const isAutomationDelete = computed(() => kind.value === "delete_automation");
const isDeviceCommand = computed(() => kind.value === "device_command");

const title = computed(() => {
  if (isSceneExecution.value) return "需要确认场景执行";
  if (isAutomationCreate.value) return "需要确认创建自动化";
  if (isAutomationUpdate.value) return "需要确认修改自动化";
  if (isAutomationToggle.value) return "需要确认启停自动化";
  if (isAutomationDelete.value) return "需要确认删除自动化";
  if (isDeviceCommand.value) return "需要确认设备操作";
  return "需要确认操作";
});

const summary = computed(() => String(preview.value.summary || ""));
const automationName = computed(() => String(preview.value.automation_name || ""));
const canApprove = computed(() => {
  if (isSceneExecution.value) {
    return Boolean(preview.value.enabled);
  }
  return true;
});

const disabledTip = computed(() => {
  if (isSceneExecution.value && !preview.value.enabled) {
    return "当前场景已停用，无法执行。";
  }
  return "";
});

const changedFields = computed(() => (preview.value.changed_fields as string[]) || []);
const affectedDeviceNames = computed(() => (preview.value.affected_device_names as string[]) || []);
const triggerCount = computed(() => Number(preview.value.trigger_count ?? 0));
const conditionCount = computed(() => Number(preview.value.condition_count ?? 0));
const actionCount = computed(() => Number(preview.value.action_count ?? 0));
const targetEnabled = computed(() => Boolean(preview.value.target_enabled));

const sceneSteps = computed(() => (preview.value.steps as any[]) || []);
const sceneName = computed(() => String(preview.value.scene_name || ""));

// === 设备命令预览（对应 kind === "device_command"） ===

/** 设备名 + 品牌拼接：Yeelight 灯 → "客厅吊灯（Yeelight）"。 */
const deviceLabel = computed(() => {
  if (!isDeviceCommand.value) return "";
  const name = String(preview.value.device_name || "未知设备");
  const brand = String(preview.value.device_brand || "").trim();
  return brand ? `${name}（${brand}）` : name;
});

/** 操作名 + 参数。 */
const operationLabel = computed(() => {
  if (!isDeviceCommand.value) return "";
  const op = String(preview.value.operation || "");
  const args = preview.value as Record<string, unknown>;
  if (op === "set_device_power") {
    const power = String(args.power || "");
    return power === "on" ? "开启电源" : "关闭电源";
  }
  if (op === "set_device_temperature") {
    const temp = args.temperature;
    return `设置温度（${temp}℃）`;
  }
  if (op === "set_curtain_position") {
    const pos = args.position;
    return `设置开合度（${pos}%）`;
  }
  return op || "设备操作";
});

/** 通用影响描述。 */
const impact = computed(() => {
  if (!isDeviceCommand.value) return "";
  return String(preview.value.impact || "设备状态将变更");
});

/** 设备类型 → 设备图标。 */
const deviceTypeIcon = computed(() => {
  if (!isDeviceCommand.value) return "device-management";
  const t = String(preview.value.device_type || "");
  if (t === "light") return "light";
  if (t === "air_conditioner") return "air-conditioner";
  if (t === "curtain") return "curtain";
  if (t === "socket") return "plug";
  if (t === "lock") return "lock";
  if (t === "camera") return "camera";
  if (t === "sensor") return "sensor";
  return "device-management";
});
</script>

<template>
  <article class="approval-card">
    <header class="approval-header">
      <div>
        <strong>{{ title }}</strong>
        <p v-if="summary">{{ summary }}</p>
        <p v-else-if="automationName">{{ automationName }}</p>
        <p v-else-if="sceneName">{{ sceneName }}</p>
      </div>

      <span
        class="risk-badge"
        :class="`risk-${approval.risk_level}`"
      >
        {{
          approval.risk_level === "high"
            ? "高风险"
            : approval.risk_level === "unknown"
              ? "未知风险"
              : "低风险"
        }}
      </span>
    </header>

    <ul v-if="approval.reasons.length" class="reason-list">
      <li v-for="reason in approval.reasons" :key="reason">
        {{ reason }}
      </li>
    </ul>

    <!-- 场景执行步骤 -->
    <div v-if="isSceneExecution && sceneSteps.length" class="step-list">
      <div
        v-for="step in sceneSteps"
        :key="step.step_id"
        class="scene-step"
      >
        <span class="step-order">{{ step.order }}</span>
        <div>
          <strong>{{ step.name }}</strong>
          <p>
            {{ step.device_name || step.device_id }}
            <template v-if="step.description">
              · {{ step.description }}
            </template>
          </p>
        </div>
      </div>
    </div>

    <!-- 自动化创建预览 -->
    <div v-if="isAutomationCreate" class="auto-detail">
      <div v-if="triggerCount > 0" class="detail-row">
        <span class="detail-label">触发器</span>
        <span class="detail-value">{{ triggerCount }} 个</span>
      </div>
      <div v-if="conditionCount > 0" class="detail-row">
        <span class="detail-label">条件</span>
        <span class="detail-value">{{ conditionCount }} 个</span>
      </div>
      <div v-if="actionCount > 0" class="detail-row">
        <span class="detail-label">动作</span>
        <span class="detail-value">{{ actionCount }} 个</span>
      </div>
      <div v-if="affectedDeviceNames.length" class="detail-row">
        <span class="detail-label">影响设备</span>
        <span class="detail-value">{{ affectedDeviceNames.join("、") }}</span>
      </div>
    </div>

    <!-- 自动化修改预览 -->
    <div v-if="isAutomationUpdate && changedFields.length" class="auto-detail">
      <div class="detail-row">
        <span class="detail-label">修改字段</span>
        <span class="detail-value">{{ changedFields.join("、") }}</span>
      </div>
    </div>

    <!-- 自动化启停预览 -->
    <div v-if="isAutomationToggle" class="auto-detail">
      <div class="detail-row">
        <span class="detail-label">目标状态</span>
        <span class="detail-value">{{ targetEnabled ? "启用" : "停用" }}</span>
      </div>
    </div>

    <!-- 设备命令预览（单设备操作）：📍 设备 / ⚡ 操作 / 影响 -->
    <div v-if="isDeviceCommand" class="device-command-detail">
      <div class="device-command-row">
        <span class="device-command-icon" aria-hidden="true">
          <SvgIcon :name="deviceTypeIcon" size="sm" />
        </span>
        <span class="device-command-label">设备</span>
        <span class="device-command-value">{{ deviceLabel }}</span>
      </div>
      <div class="device-command-row">
        <span class="device-command-icon" aria-hidden="true">
          <SvgIcon name="bolt" size="sm" />
        </span>
        <span class="device-command-label">操作</span>
        <span class="device-command-value">{{ operationLabel }}</span>
      </div>
      <div class="device-command-row">
        <span class="device-command-icon" aria-hidden="true">
          <SvgIcon name="info" size="sm" />
        </span>
        <span class="device-command-label">影响</span>
        <span class="device-command-value">{{ impact }}</span>
      </div>
    </div>

    <div class="approval-meta">
      <div class="meta-row">
        <span class="meta-label">确认 ID</span>
        <span class="meta-value">{{ approval.approval_id.slice(0, 12) }}...</span>
      </div>
      <div v-if="approval.resource_version" class="meta-row">
        <span class="meta-label">资源版本</span>
        <span class="meta-value">{{ approval.resource_version }}</span>
      </div>
    </div>

    <footer class="approval-actions">
      <button
        type="button"
        class="reject-button"
        :disabled="submitting"
        @click="$emit('reject')"
      >
        {{ submitting ? "处理中…" : "拒绝" }}
      </button>

      <button
        type="button"
        class="approve-button"
        :disabled="submitting || !canApprove"
        @click="$emit('approve')"
      >
        {{ submitting ? "处理中…" : "确认执行" }}
      </button>
    </footer>

    <p v-if="disabledTip" class="disabled-tip">
      {{ disabledTip }}
    </p>
  </article>
</template>

<style scoped>
.approval-card {
  margin: 12px 0 20px 54px;
  max-width: 520px;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  background: var(--color-card-bg);
  overflow: hidden;
}

.approval-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 16px 16px 0;
}

.approval-header strong {
  display: block;
  font-size: 15px;
  margin-bottom: 4px;
}

.approval-header p {
  margin: 0;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.risk-badge {
  flex-shrink: 0;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}

.risk-low {
  background: color-mix(in srgb, var(--color-success) 12%, transparent);
  color: var(--color-success);
}

.risk-high {
  background: color-mix(in srgb, var(--color-danger) 12%, transparent);
  color: var(--color-danger);
}

.risk-unknown {
  background: color-mix(in srgb, var(--color-warning) 15%, transparent);
  color: var(--color-warning);
}

.reason-list {
  margin: 12px 16px 0;
  padding: 0;
  list-style: none;
}

.reason-list li {
  position: relative;
  padding-left: 14px;
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.reason-list li::before {
  content: "•";
  position: absolute;
  left: 0;
  color: var(--color-text-tertiary);
}

.step-list {
  margin: 12px 16px 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.scene-step {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 8px;
  background: var(--color-surface);
}

.step-order {
  flex-shrink: 0;
  width: 22px;
  height: 22px;
  display: grid;
  place-items: center;
  border-radius: 999px;
  background: var(--color-primary-100);
  color: var(--color-primary-700);
  font-size: 11px;
  font-weight: 700;
}

.scene-step strong {
  display: block;
  font-size: 13px;
}

.scene-step p {
  margin: 0;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.auto-detail {
  margin: 12px 16px 0;
  display: grid;
  gap: 6px;
  padding: 10px 12px;
  border-radius: 8px;
  background: var(--color-surface-subtle);
}

.detail-row {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  font-size: 12px;
  line-height: 1.6;
}

.detail-label {
  color: var(--color-text-tertiary);
  font-weight: 600;
  flex-shrink: 0;
}

.detail-value {
  color: var(--color-text-primary);
  text-align: right;
}

.approval-meta {
  margin: 12px 16px 0;
  display: grid;
  gap: 6px;
  padding: 10px 12px;
  border-radius: 8px;
  background: var(--color-surface-subtle);
}

.meta-row {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  font-size: 12px;
}

.meta-label {
  color: var(--color-text-tertiary);
  font-weight: 600;
}

.meta-value {
  font-weight: 700;
  color: var(--color-text-primary);
  font-family: monospace;
}

.approval-actions {
  display: flex;
  gap: 8px;
  padding: 16px;
}

.approval-actions button {
  flex: 1;
  padding: 8px 0;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s;
}

.approval-actions button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.reject-button {
  background: var(--color-surface);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border);
}

.approve-button {
  background: var(--color-primary-500);
  color: white;
}

.disabled-tip {
  margin: 0 16px 16px;
  font-size: 12px;
  color: var(--color-danger);
}

/* === 设备命令预览（单设备） === */
.device-command-detail {
  margin: 12px 16px 0;
  display: grid;
  gap: 6px;
  padding: 10px 12px;
  border-radius: 8px;
  background: var(--color-surface-subtle);
}

.device-command-row {
  display: grid;
  grid-template-columns: 18px 28px minmax(0, 1fr);
  align-items: center;
  gap: 8px;
  font-size: 13px;
  line-height: 1.5;
}

.device-command-icon {
  display: grid;
  width: 18px;
  height: 18px;
  place-items: center;
  color: var(--color-text-tertiary);
  flex-shrink: 0;
}

.device-command-label {
  color: var(--color-text-tertiary);
  font-weight: 600;
  font-size: 12px;
}

.device-command-value {
  color: var(--color-text-primary);
  font-weight: 700;
  min-width: 0;
  word-break: break-word;
}
</style>