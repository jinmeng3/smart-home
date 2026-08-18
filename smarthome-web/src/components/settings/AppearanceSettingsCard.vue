<script setup lang="ts">
import type {
    AppearanceSettings,
    FontSize,
    ThemeMode,
} from "../../types/settings";
import SettingsSectionCard from "./SettingsSectionCard.vue";
import BaseSwitch from "../BaseSwitch.vue";
import SvgIcon from "../common/SvgIcon.vue";

defineProps<{
    appearance: AppearanceSettings;
}>();

const themeOptions: Array<{ value: ThemeMode; label: string }> = [
    { value: "light", label: "浅色" },
    { value: "dark", label: "深色" },
    { value: "system", label: "跟随系统" },
];

const fontOptions: Array<{ value: FontSize; label: string }> = [
    { value: "small", label: "小" },
    { value: "medium", label: "中" },
    { value: "large", label: "大" },
];
</script>

<template>
    <SettingsSectionCard id="appearance" icon="appearance" title="界面" tone="purple">
        <div class="settings-field">
            <span class="settings-field-icon is-purple"><SvgIcon name="sun" size="sm" /></span>
            <span class="settings-field-label">主题模式</span>
            <div class="segmented">
                <button
                    v-for="option in themeOptions"
                    :key="option.value"
                    :class="{ active: appearance.themeMode === option.value }"
                    type="button"
                    @click="appearance.themeMode = option.value"
                >
                    {{ option.label }}
                </button>
            </div>
        </div>
        <div class="settings-field">
            <span class="settings-field-icon is-purple"><SvgIcon name="eye" size="sm" /></span>
            <span class="settings-field-label">字体大小</span>
            <div class="segmented">
                <button
                    v-for="option in fontOptions"
                    :key="option.value"
                    :class="{ active: appearance.fontSize === option.value }"
                    type="button"
                    @click="appearance.fontSize = option.value"
                >
                    {{ option.label }}
                </button>
            </div>
        </div>
        <div class="settings-field">
            <span class="settings-field-icon is-purple"><SvgIcon name="rotate-cw" size="sm" /></span>
            <span class="settings-field-label">动画效果</span
            ><BaseSwitch v-model="appearance.animationsEnabled" />
        </div>
        <div class="settings-field">
            <span class="settings-field-icon is-purple"><SvgIcon name="speed" size="sm" /></span>
            <span class="settings-field-label">流畅模式</span
            ><BaseSwitch v-model="appearance.performanceMode" />
        </div>
    </SettingsSectionCard>
</template>

<style scoped>
/* 分段控件：轨道式背景 + 活动按钮隆起 */
.segmented {
    --seg-track: var(--color-surface-hover);
    display: grid;
    width: auto;
    min-width: 0;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 2px;
    padding: 3px;
    border: 1px solid var(--color-border-subtle);
    border-radius: 10px;
    background: var(--seg-track);
    overflow: hidden;
}

.segmented button {
    height: 28px;
    padding: 0 10px;
    border: 0;
    border-radius: 7px;
    background: transparent;
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 700;
    white-space: nowrap;
    transition:
        background-color 200ms var(--motion-ease),
        color 200ms var(--motion-ease),
        box-shadow 200ms var(--motion-ease);
}

.segmented button:hover {
    color: var(--color-text-primary);
}

.segmented button.active {
    background: var(--color-card-bg);
    color: var(--color-primary-700);
    box-shadow: 0 1px 3px color-mix(in srgb, var(--color-primary-900) 14%, transparent);
}

@media (max-width: 767px) {
    .segmented {
        width: 100%;
    }
}
</style>
