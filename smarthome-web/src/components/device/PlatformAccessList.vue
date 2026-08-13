<script setup lang="ts">
import { computed, ref } from "vue";
import SvgIcon from "../common/SvgIcon.vue";
import PlatformAccessItem from "./PlatformAccessItem.vue";
import { devicePlatformOptions } from "./deviceMeta";
import type { DevicePlatformInfo } from "../../types/device";

const props = defineProps<{
    platforms: DevicePlatformInfo[];
    syncing?: boolean;
}>();

const emit = defineEmits<{
    sync: [];
}>();

/** 仅展示已配置（有设备接入）的平台，未配置平台不再罗列 */
const visiblePlatforms = computed(() =>
    props.platforms.filter((p) => p.connected),
);

/** 当前展开的平台（一次只展开一个） */
const expandedName = ref<string | null>(null);
const addMenuOpen = ref(false);

const togglePlatform = (name: string) => {
    expandedName.value = expandedName.value === name ? null : name;
};

/** 添加平台菜单：未配置的核心平台 + 预留平台；编辑器未实现，统一标记“即将支持” */
const addOptions = computed(() => {
    const configured = new Set(visiblePlatforms.value.map((p) => p.name));
    const unconfigured = devicePlatformOptions.filter(
        (name) => !configured.has(name),
    );
    return [
        ...unconfigured.map((name) => ({
            name,
            supported: name === "Home Assistant",
        })),
        { name: "米家", supported: false },
        { name: "Apple Home", supported: false },
    ];
});
</script>

<template>
    <section class="platform-access">
        <h3 class="rail-section-title">接入平台</h3>

        <div v-if="visiblePlatforms.length" class="platform-list">
            <PlatformAccessItem
                v-for="platform in visiblePlatforms"
                :key="platform.name"
                :platform="platform"
                :expanded="expandedName === platform.name"
                :syncing="syncing"
                @toggle="togglePlatform(platform.name)"
                @sync="$emit('sync')"
                @manage="addMenuOpen = false"
            />
        </div>

        <!-- 空状态 -->
        <div v-else class="platform-empty">
            <SvgIcon name="platform" size="sm" />
            <span>尚未接入平台，点击下方按钮添加</span>
        </div>

        <!-- 添加平台入口 -->
        <div class="platform-add">
            <button
                class="platform-add-btn"
                type="button"
                :class="{ 'is-open': addMenuOpen }"
                @click="addMenuOpen = !addMenuOpen"
            >
                <SvgIcon name="plus" size="sm" />
                添加接入平台
            </button>

            <Transition name="platform-menu">
                <div v-if="addMenuOpen" class="platform-add-menu">
                    <button
                        v-for="option in addOptions"
                        :key="option.name"
                        class="platform-add-option"
                        type="button"
                    >
                        <span>{{ option.name }}</span>
                        <em v-if="!option.supported" class="coming-soon">即将支持</em>
                        <SvgIcon v-else name="chevron-right" size="sm" />
                    </button>
                </div>
            </Transition>
        </div>
    </section>
</template>

<style scoped>
.platform-access {
    margin: 12px 14px 16px;
    border: 1px solid var(--color-border-subtle);
    border-radius: 14px;
    background: var(--color-panel-background);
    padding: 13px;
    box-shadow: var(--shadow-card);
}

.rail-section-title {
    margin: 0 0 10px;
    padding-bottom: 0;
    border-bottom: 0;
    font-size: 13px;
    font-weight: 900;
    color: var(--color-text-primary);
}

.platform-list {
    display: grid;
    gap: 6px;
}

.platform-empty {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px;
    border: 1px dashed var(--color-border);
    border-radius: 10px;
    color: var(--color-text-muted);
    font-size: 12px;
    font-weight: 700;
    line-height: 1.5;
}

.platform-empty svg {
    flex: 0 0 auto;
    opacity: 0.6;
}

.platform-add {
    margin-top: 12px;
}

.platform-add-btn {
    display: inline-flex;
    width: 100%;
    align-items: center;
    justify-content: center;
    gap: 5px;
    height: 36px;
    border: 1px dashed var(--color-border);
    border-radius: 10px;
    background: color-mix(in srgb, var(--color-panel-background) 78%, transparent);
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 800;
    transition:
        border-color 140ms ease,
        color 140ms ease,
        background-color 140ms ease;
}

.platform-add-btn:hover,
.platform-add-btn.is-open {
    border-color: var(--color-primary-400);
    color: var(--color-primary-600);
    background: var(--color-primary-50);
}

.platform-add-menu {
    display: grid;
    gap: 2px;
    margin-top: 6px;
    border: 1px solid var(--color-border-subtle);
    border-radius: 10px;
    background: var(--color-panel-secondary);
    padding: 4px;
}

.platform-add-option {
    display: flex;
    width: 100%;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    border-radius: 7px;
    padding: 8px 10px;
    text-align: left;
    font-size: 12px;
    font-weight: 800;
    color: var(--color-text-secondary);
    transition: background-color 120ms ease;
}

.platform-add-option:hover {
    background: var(--color-surface-hover);
}

.coming-soon {
    font-size: 10px;
    font-style: normal;
    font-weight: 800;
    color: var(--color-text-muted);
    background: var(--color-surface-subtle);
    border-radius: 999px;
    padding: 2px 8px;
}

.platform-menu-enter-active,
.platform-menu-leave-active {
    transition: opacity 160ms ease, transform 160ms var(--motion-ease);
    transform-origin: top center;
}

.platform-menu-enter-from,
.platform-menu-leave-to {
    opacity: 0;
    transform: translateY(-4px);
}

@media (prefers-reduced-motion: reduce) {
    .platform-menu-enter-active,
    .platform-menu-leave-active {
        transition-duration: 1ms;
    }
}
</style>
