<script setup lang="ts">
import { computed } from "vue";
import type {
    BackupSettings,
    NotificationSettings,
    SecuritySettings,
    SettingsSectionId,
} from "../../types/settings";
import SvgIcon from "../common/SvgIcon.vue";

const props = defineProps<{
    security: SecuritySettings;
    backup: BackupSettings;
    notifications: NotificationSettings;
    accountStatus: string;
    homeAssistantConnected: boolean;
}>();

const emit = defineEmits<{
    navigate: [section: SettingsSectionId];
}>();

interface HealthItem {
    label: string;
    healthy: boolean;
    section: SettingsSectionId;
    hint: string;
}

const healthItems = computed<HealthItem[]>(() => [
    {
        label: "账户状态正常",
        healthy: props.accountStatus === "正常" || props.accountStatus === "normal",
        section: "account",
        hint: props.accountStatus === "正常" || props.accountStatus === "normal" ? "" : "账户异常需处理",
    },
    {
        label: "Home Assistant 已连接",
        healthy: props.homeAssistantConnected,
        section: "homeAssistant",
        hint: props.homeAssistantConnected ? "" : "平台未连接",
    },
    {
        label: "双重验证" + (props.security.twoFactorEnabled ? "已开启" : "未开启"),
        healthy: props.security.twoFactorEnabled,
        section: "security",
        hint: props.security.twoFactorEnabled ? "" : "建议开启双重验证",
    },
    {
        label: "自动备份" + (props.backup.autoBackup ? "已开启" : "已关闭"),
        healthy: props.backup.autoBackup,
        section: "backup",
        hint: props.backup.autoBackup ? "" : "建议启用自动备份",
    },
]);

const healthyCount = computed(() => healthItems.value.filter((item) => item.healthy).length);
const totalCount = computed(() => healthItems.value.length);
const healthPercent = computed(() => Math.round((healthyCount.value / totalCount.value) * 100));

const allHealthy = computed(() => healthyCount.value === totalCount.value);
</script>

<template>
    <section
        class="health-card rounded-xl border border-[var(--color-border-default)] bg-[var(--color-panel-background)] p-4"
    >
        <div class="flex items-center justify-between gap-2">
            <h2 class="flex items-center gap-2 text-sm font-extrabold text-[var(--color-text-primary)]">
                <span
                    class="grid h-7 w-7 place-items-center rounded-lg"
                    :class="allHealthy ? 'bg-[var(--color-success-soft)] text-[var(--color-success)]' : 'bg-[var(--color-warning-soft)] text-[var(--color-warning)]'"
                >
                    <SvgIcon name="security" size="sm" />
                </span>
                配置健康度
            </h2>
            <span
                class="text-sm font-extrabold tabular-nums"
                :class="healthPercent >= 80 ? 'text-[var(--color-success)]' : healthPercent >= 50 ? 'text-[var(--color-warning)]' : 'text-[var(--color-danger)]'"
            >
                {{ healthPercent }}%
            </span>
        </div>

        <!-- 进度条 -->
        <div class="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-[var(--color-surface-subtle)]">
            <div
                class="h-full rounded-full transition-all duration-500"
                :class="healthPercent >= 80 ? 'bg-[var(--color-success)]' : healthPercent >= 50 ? 'bg-[var(--color-warning)]' : 'bg-[var(--color-danger)]'"
                :style="{ width: healthPercent + '%' }"
            ></div>
        </div>

        <!-- 状态列表 -->
        <div v-if="!allHealthy" class="mt-3 grid gap-1">
            <button
                v-for="item in healthItems"
                :key="item.section"
                v-show="!item.healthy"
                class="health-item"
                type="button"
                @click="emit('navigate', item.section)"
            >
                <span
                    class="health-dot"
                    :class="item.healthy ? 'is-ok' : 'is-warn'"
                ></span>
                <span class="health-label">{{ item.label }}</span>
                <span v-if="item.hint" class="health-hint">{{ item.hint }}</span>
            </button>
        </div>

        <!-- 全部正常 -->
        <div v-else class="mt-3 flex items-center gap-2 text-xs font-bold text-[var(--color-success)]">
            <SvgIcon name="check-circle" size="sm" />
            所有配置正常
        </div>
    </section>
</template>

<style scoped>
.health-card {
    box-shadow: var(--shadow-card);
}

.health-item {
    display: flex;
    width: 100%;
    align-items: center;
    gap: 8px;
    border-radius: 8px;
    padding: 7px 8px;
    text-align: left;
    font-size: 12px;
    font-weight: 700;
    color: var(--color-text-secondary);
    transition: background-color 150ms ease;
}

.health-item:hover {
    background: var(--color-surface-hover);
}

.health-dot {
    display: block;
    width: 6px;
    height: 6px;
    flex: 0 0 6px;
    border-radius: 999px;
}

.health-dot.is-ok {
    background: var(--color-success);
}

.health-dot.is-warn {
    background: var(--color-warning);
}

.health-label {
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.health-hint {
    margin-left: auto;
    flex-shrink: 0;
    font-size: 11px;
    font-weight: 700;
    color: var(--color-text-tertiary);
}
</style>
