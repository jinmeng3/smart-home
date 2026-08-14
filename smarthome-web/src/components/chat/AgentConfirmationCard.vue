<script setup lang="ts">
import type { PendingApproval } from "../../types/chat";

defineProps<{
  approval: PendingApproval;
  submitting?: boolean;
}>();

defineEmits<{
  approve: [];
  reject: [];
}>();
</script>

<template>
  <article class="approval-card">
    <header class="approval-header">
      <div>
        <strong>需要确认场景执行</strong>
        <p>{{ approval.preview.scene_name }}</p>
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

    <div class="step-list">
      <div
        v-for="step in approval.preview.steps"
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

    <footer class="approval-actions">
      <button
        type="button"
        class="reject-button"
        :disabled="submitting"
        @click="$emit('reject')"
      >
        拒绝
      </button>

      <button
        type="button"
        class="approve-button"
        :disabled="submitting || !approval.preview.enabled"
        @click="$emit('approve')"
      >
        {{ submitting ? "处理中…" : "确认执行" }}
      </button>
    </footer>

    <p v-if="!approval.preview.enabled" class="disabled-tip">
      当前场景已停用，无法执行。
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
</style>