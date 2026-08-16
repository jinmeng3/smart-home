<script setup lang="ts">
import { ref, watch } from "vue";
import SvgIcon from "./SvgIcon.vue";
import { useCollapsePhase } from "../../composables/useCollapsePhase";
import { useScrollFade } from "../../composables/useScrollFade";

const props = withDefaults(
    defineProps<{
        /** 面板标题（可为响应式字符串表达式） */
        title: string;
        subtitle?: string;
        /** localStorage 持久化键；折叠状态变化时写入 */
        storageKey?: string;
        /** v-model：外部可读取当前折叠状态 */
        collapsed?: boolean;
        /** 展开/收起宽度（CSS 变量覆盖，默认 330px / 46px） */
        expandedWidth?: string;
        collapsedWidth?: string;
    }>(),
    {
        subtitle: "",
        storageKey: "",
        collapsed: undefined,
        expandedWidth: "",
        collapsedWidth: "",
    },
);

const emit = defineEmits<{
    "update:collapsed": [value: boolean];
}>();

const isMediumScreen = () =>
    window.matchMedia("(min-width: 1024px) and (max-width: 1279px)").matches;

/** 初始折叠状态：优先 localStorage，其次外部 v-model，最后中等屏幕默认 */
const resolveInitial = (): boolean => {
    if (props.storageKey) {
        const saved = localStorage.getItem(props.storageKey);
        if (saved !== null) return saved === "true";
    }
    if (typeof props.collapsed === "boolean") return props.collapsed;
    return isMediumScreen();
};

const {
    collapsed,
    phase,
    toggle,
    skipAnimation,
} = useCollapsePhase(resolveInitial(), (value) => {
    if (props.storageKey) {
        localStorage.setItem(props.storageKey, String(value));
    }
    emit("update:collapsed", value);
});

skipAnimation();

/* === 中等屏幕（1024–1279px）且用户从未设置过时，进入时默认折叠一次 === */
const mediumMediaQuery = window.matchMedia(
    "(min-width: 1024px) and (max-width: 1279px)",
);
const handleMediumChange = (event: MediaQueryListEvent) => {
    if (event.matches && props.storageKey) {
        const saved = localStorage.getItem(props.storageKey);
        if (saved === null) {
            collapsed.value = true;
        }
    }
};
mediumMediaQuery.addEventListener("change", handleMediumChange);

/* 外部 v-model 变更时同步（避免与内部状态冲突：仅在折叠动画空闲时生效） */
watch(
    () => props.collapsed,
    (value) => {
        if (
            typeof value === "boolean" &&
            value !== collapsed.value &&
            !phase.value.includes("ing")
        ) {
            collapsed.value = value;
        }
    },
);

/* === 滚动渐隐 === */
const railScrollRef = ref<HTMLElement | null>(null);
const { canScroll, atBottom, refresh, schedule } = useScrollFade(railScrollRef, {
    deactivated: collapsed,
});
</script>

<template>
    <aside
        class="base-collapsible-rail flex min-h-0 min-w-0 flex-col overflow-hidden rounded-xl border border-[var(--color-border-subtle)] bg-[var(--color-rail-bg, var(--color-workspace-background))] shadow-soft"
        :class="[collapsed ? 'is-collapsed' : '', `phase-${phase}`]"
        :style="{
            '--rail-width-expanded': expandedWidth || undefined,
            '--rail-width-collapsed': collapsedWidth || undefined,
        }"
    >
        <!-- 收起状态：窄状态栏 -->
        <div v-if="collapsed" class="rail-collapsed">
            <button
                class="rail-toggle"
                type="button"
                title="展开侧栏"
                aria-label="展开侧栏"
                @click="toggle"
            >
                <SvgIcon name="chevron-left" size="sm" />
            </button>
            <slot name="collapsed" />
        </div>

        <!-- 展开状态 -->
        <template v-else>
            <header class="rail-header shrink-0 rail-detail">
                <div class="min-w-0">
                    <h2>{{ title }}</h2>
                    <p v-if="subtitle" class="rail-subtitle">{{ subtitle }}</p>
                </div>
                <button
                    class="rail-toggle"
                    type="button"
                    title="收起侧栏"
                    aria-label="收起侧栏"
                    @click="toggle"
                >
                    <SvgIcon name="chevron-right" size="sm" />
                </button>
            </header>

            <div
                ref="railScrollRef"
                class="rail-scroll min-h-0 flex-1 overflow-y-auto rail-detail"
                @scroll.passive="schedule"
            >
                <slot />
            </div>

            <div
                class="rail-fade"
                :class="{ 'is-visible': canScroll && !atBottom }"
                aria-hidden="true"
            ></div>
        </template>
    </aside>
</template>

<style scoped>
.base-collapsible-rail {
    position: relative;
    width: var(--rail-width-expanded, 330px);
    transition:
        width 300ms cubic-bezier(0.22, 1, 0.36, 1),
        border-radius 300ms cubic-bezier(0.22, 1, 0.36, 1),
        box-shadow 300ms cubic-bezier(0.22, 1, 0.36, 1);
}

.base-collapsible-rail.is-collapsed {
    width: var(--rail-width-collapsed, 46px);
}

/* === 收起状态 === */
.rail-collapsed {
    display: flex;
    width: 46px;
    flex-direction: column;
    align-items: center;
    gap: 12px;
    padding-top: 16px;
    margin: 0 auto;
}

.rail-toggle {
    display: grid;
    width: 28px;
    height: 28px;
    flex: 0 0 28px;
    place-items: center;
    border-radius: 8px;
    color: var(--color-text-tertiary);
    transition:
        background 160ms var(--motion-ease),
        color 160ms var(--motion-ease);
}

.rail-toggle:hover {
    background: var(--color-surface-hover);
    color: var(--color-text-primary);
}

/* === 展开头部 === */
.rail-header {
    display: flex;
    min-height: 40px;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    border-bottom: 1px solid var(--color-border-subtle);
    padding: 10px 12px 9px;
    background: color-mix(
        in srgb,
        var(--color-panel-background) 72%,
        transparent
    );
}

.rail-header h2 {
    margin: 0;
    font-size: 15px;
    font-weight: 900;
    color: var(--color-text-primary);
    line-height: 1.3;
}

.rail-subtitle {
    margin: 2px 0 0;
    overflow: hidden;
    font-size: 11px;
    color: var(--color-text-muted);
    text-overflow: ellipsis;
    white-space: nowrap;
}

.rail-scroll {
    overscroll-behavior: contain;
    scrollbar-gutter: stable;
}

.rail-scroll::-webkit-scrollbar {
    width: 4px;
}

.rail-scroll::-webkit-scrollbar-thumb {
    border-radius: 999px;
    background: transparent;
    transition: background 180ms ease;
}

.base-collapsible-rail:hover .rail-scroll::-webkit-scrollbar-thumb {
    background: var(--color-border);
}

/* === 底部渐隐遮罩 === */
.rail-fade {
    position: absolute;
    right: 0;
    bottom: 0;
    left: 0;
    z-index: 2;
    height: 26px;
    pointer-events: none;
    opacity: 0;
    transition: opacity 200ms ease;
    background: linear-gradient(
        to top,
        var(--color-rail-bg, var(--color-workspace-background)),
        transparent
    );
}

.rail-fade.is-visible {
    opacity: 1;
}

/* === 三阶段折叠动画 === */
aside.phase-collapsing {
    overflow: hidden;
}

aside.phase-collapsing .rail-detail,
aside.phase-expanding .rail-detail {
    transition:
        opacity 140ms ease,
        transform 180ms cubic-bezier(0.22, 1, 0.36, 1);
}

aside.phase-collapsing .rail-detail {
    opacity: 0;
    transform: translateX(8px);
}

aside.phase-collapsed .rail-detail,
aside.phase-collapsing .rail-detail {
    pointer-events: none;
}

aside.phase-expanding .rail-detail {
    opacity: 1;
    transform: translateX(0);
}

aside.phase-collapsed .rail-detail {
    display: none;
}

@media (prefers-reduced-motion: reduce) {
    .base-collapsible-rail,
    .rail-collapsed,
    .rail-header,
    .rail-scroll {
        animation: none;
        transition-duration: 1ms;
    }
}
</style>