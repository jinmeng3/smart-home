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
/* 分段控件：列布局由卡片控制，视觉样式复用全局 .segmented 胶囊样式 */
.segmented {
    width: auto;
    min-width: 0;
    grid-template-columns: repeat(3, minmax(0, 1fr));
}

@media (max-width: 767px) {
    .segmented {
        width: 100%;
    }
}
</style>
