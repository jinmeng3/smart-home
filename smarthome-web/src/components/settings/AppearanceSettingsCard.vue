<script setup lang="ts">
import type {
    AppearanceSettings,
    FontSize,
    ThemeMode,
} from "../../types/settings";
import SettingsSectionCard from "./SettingsSectionCard.vue";
import BaseSwitch from "../BaseSwitch.vue";

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
    <SettingsSectionCard id="appearance" icon="▣" title="界面">
        <div class="settings-field">
            <span>主题模式</span>
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
            <span>字体大小</span>
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
            <span>动画效果</span
            ><BaseSwitch v-model="appearance.animationsEnabled" />
        </div>
        <div class="settings-field">
            <span>侧边栏折叠</span
            ><BaseSwitch v-model="appearance.sidebarCollapsed" />
        </div>
    </SettingsSectionCard>
</template>
