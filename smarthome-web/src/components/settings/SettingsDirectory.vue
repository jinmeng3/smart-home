<script setup lang="ts">
import { computed } from "vue";
import { settingsGroups, settingsSections } from "../../constants/settingsSections";
import SvgIcon from "../common/SvgIcon.vue";
import type { SettingsSectionId } from "../../types/settings";

const props = defineProps<{
    active: SettingsSectionId;
    compact?: boolean;
    totalItems?: number;
    completedItems?: number;
}>();

const emit = defineEmits<{
    select: [section: SettingsSectionId];
}>();

const activeGroup = computed(() => {
    for (const group of settingsGroups) {
        if (group.sections.some((item) => item.id === props.active)) {
            return group.groupLabel;
        }
    }
    return null;
});

const showProgress = computed(
    () => props.totalItems !== undefined && props.totalItems > 0,
);
const progressPercent = computed(() => {
    if (!showProgress.value) return 0;
    return Math.round(((props.completedItems ?? 0) / props.totalItems!) * 100);
});
</script>

<template>
    <nav
        v-if="compact"
        class="settings-directory-compact"
        aria-label="设置分区导航"
    >
        <button
            v-for="item in settingsSections"
            :key="item.id"
            class="compact-directory-item"
            :class="{ 'is-active': active === item.id }"
            type="button"
            :title="item.label"
            :aria-label="item.label"
            @click="emit('select', item.id)"
        >
            <span class="compact-accent" :class="`is-${item.tone}`"></span>
            <SvgIcon :name="item.icon" size="sm" />
        </button>
    </nav>

    <nav v-else class="settings-directory" aria-label="设置分区导航">
        <div class="directory-header">
            <SvgIcon name="settings" size="sm" />
            <span>设置目录</span>
        </div>

        <div class="directory-scroll">
            <div class="directory-list">
                <template v-for="group in settingsGroups" :key="group.group">
                    <div
                        class="directory-group-label"
                        :class="{
                            'is-active-group': activeGroup === group.groupLabel,
                        }"
                    >
                        {{ group.groupLabel }}
                    </div>
                    <button
                        v-for="item in group.sections"
                        :key="item.id"
                        class="directory-item"
                        :class="{ 'is-active': active === item.id }"
                        type="button"
                        @click="emit('select', item.id)"
                    >
                        <span class="accent-bar"></span>
                        <span class="directory-dot" :class="`is-${item.tone}`"></span>
                        <span class="directory-label">{{ item.label }}</span>
                    </button>
                </template>
            </div>
        </div>

        <div v-if="showProgress" class="directory-progress">
            <div class="directory-progress-bar">
                <div
                    class="directory-progress-fill"
                    :style="{ width: progressPercent + '%' }"
                ></div>
            </div>
            <span class="directory-progress-text">
                已完成 {{ completedItems }}/{{ totalItems }} 项配置
            </span>
        </div>
    </nav>
</template>

<style scoped>
.settings-directory-compact {
    display: grid;
    width: 46px;
    gap: 5px;
    justify-items: center;
    padding: 2px 8px 10px;
}

.compact-directory-item {
    position: relative;
    display: grid;
    width: 30px;
    height: 30px;
    place-items: center;
    border-radius: 8px;
    color: var(--color-text-tertiary);
    transition:
        background-color 160ms var(--motion-ease),
        color 160ms var(--motion-ease);
}

.compact-directory-item:hover {
    background: var(--color-surface-hover);
    color: var(--color-text-primary);
}

.compact-directory-item.is-active {
    background: var(--color-primary-50);
    color: var(--color-primary-700);
}

.compact-accent {
    position: absolute;
    top: 8px;
    bottom: 8px;
    left: -8px;
    width: 3px;
    border-radius: 0 999px 999px 0;
    background: var(--color-primary-600);
    opacity: 0;
    transform: scaleY(0.5);
    transition: opacity 160ms ease, transform 180ms var(--motion-ease);
}

.compact-directory-item.is-active .compact-accent {
    opacity: 1;
    transform: scaleY(1);
}

.settings-directory {
    display: flex;
    flex-direction: column;
    background: var(--color-panel-background);
    border: 1px solid var(--color-border-default);
    border-radius: 12px;
    box-shadow: none;
}

.directory-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 0 14px;
    padding: 12px 0 8px;
    border-bottom: 1px solid var(--color-border-subtle);
    font-size: 12px;
    font-weight: 800;
    color: var(--color-text-tertiary);
    text-transform: uppercase;
    letter-spacing: 0.04em;
    flex: 0 0 auto;
}

.directory-scroll {
    padding: 6px 14px 10px;
}

.directory-list {
    display: grid;
    gap: 1px;
}

.directory-group-label {
    padding: 8px 10px 4px;
    font-size: 11px;
    font-weight: 800;
    color: var(--color-text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    transition: color 200ms ease;
}

.directory-group-label.is-active-group {
    color: var(--color-text-secondary);
}

.directory-item {
    display: flex;
    width: 100%;
    align-items: center;
    gap: 8px;
    border-radius: 6px;
    min-height: 36px;
    padding: 6px 10px;
    padding-left: 6px;
    text-align: left;
    font-size: 13px;
    font-weight: 700;
    color: var(--color-text-secondary);
    position: relative;
    transition:
        background-color 150ms ease,
        color 150ms ease;
}

.directory-item:hover {
    background: var(--color-surface-hover);
    color: var(--color-text-primary);
}

.directory-item.is-active {
    background: var(--color-primary-50);
    color: var(--color-primary-700);
}

.accent-bar {
    display: block;
    width: 3px;
    height: 0;
    flex: 0 0 3px;
    border-radius: 0 999px 999px 0;
    background: var(--color-primary-600);
    transition: height 180ms var(--motion-ease);
}

.directory-item.is-active .accent-bar {
    height: 18px;
}

.directory-dot {
    display: block;
    width: 6px;
    height: 6px;
    flex: 0 0 6px;
    border-radius: 999px;
    background: var(--color-border-strong);
    transition: background 200ms ease;
}

.directory-item.is-active .directory-dot {
    background: var(--color-primary-500);
}

.directory-dot.is-primary { background: var(--color-primary-500); }
.directory-dot.is-purple { background: var(--tone-purple); }
.directory-dot.is-indigo { background: var(--tone-indigo); }
.directory-dot.is-orange { background: var(--tone-orange); }
.directory-dot.is-warning { background: var(--color-warning); }
.directory-dot.is-danger { background: var(--color-danger); }
.directory-dot.is-success { background: var(--color-success); }

.directory-label {
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.directory-progress {
    flex: 0 0 auto;
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 0 14px;
    padding: 8px 0 12px;
    border-top: 1px solid var(--color-border-subtle);
}

.directory-progress-bar {
    flex: 1;
    height: 4px;
    overflow: hidden;
    border-radius: 999px;
    background: var(--color-surface-subtle);
}

.directory-progress-fill {
    height: 100%;
    border-radius: 999px;
    background: var(--color-primary-500);
    transition: width 400ms var(--motion-ease);
}

.directory-progress-text {
    flex-shrink: 0;
    font-size: 11px;
    font-weight: 700;
    color: var(--color-text-muted);
    white-space: nowrap;
}
</style>
