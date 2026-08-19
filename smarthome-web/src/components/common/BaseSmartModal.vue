<script setup lang="ts">
import {
    computed,
    nextTick,
    onBeforeUnmount,
    shallowRef,
    useId,
    watch,
} from "vue";
import { gsap } from "../../motion/gsap";
import { useMotionMode } from "../../motion/motionMode";
import { motionDuration, motionEase } from "../../motion/tokens";
import BaseButton from "./BaseButton.vue";
import SvgIcon from "./SvgIcon.vue";

const modalStack: symbol[] = [];
let bodyOverflow = "";

const registerModal = (id: symbol) => {
    if (!modalStack.length) {
        bodyOverflow = document.body.style.overflow;
        document.body.style.overflow = "hidden";
    }
    if (!modalStack.includes(id)) modalStack.push(id);
};

const unregisterModal = (id: symbol) => {
    const index = modalStack.indexOf(id);
    if (index >= 0) modalStack.splice(index, 1);
    if (!modalStack.length) document.body.style.overflow = bodyOverflow;
};

type SmartModalWidth = "small" | "medium" | "large" | "xlarge" | string | number;

interface SmartModalProps {
    modelValue: boolean;
    title?: string;
    description?: string;
    icon?: string;
    width?: SmartModalWidth;
    loading?: boolean;
    closable?: boolean;
    closeOnOverlay?: boolean;
    confirmText?: string;
    cancelText?: string;
    draftText?: string;
    showDraft?: boolean;
    beforeClose?: () => boolean | Promise<boolean>;
    closeButtonDisabled?: boolean;
    dirty?: boolean;
    dirtyText?: string;
    sheet?: boolean;
    bodyScrollable?: boolean;
    bodyTone?: "subtle" | "neutral";
    tone?: "primary" | "indigo" | "orange" | "teal" | "green" | "purple" | "red";
}

const focusableSelector = [
    "a[href]",
    "button:not([disabled])",
    "input:not([disabled])",
    "select:not([disabled])",
    "textarea:not([disabled])",
    "[tabindex]:not([tabindex='-1'])",
].join(",");

const { isReduced } = useMotionMode();

const props = withDefaults(defineProps<SmartModalProps>(), {
    description: "",
    icon: "ai",
    title: "",
    width: "medium",
    loading: false,
    closable: true,
    closeOnOverlay: true,
    confirmText: "应用设置",
    cancelText: "取消",
    draftText: "保存草稿",
    showDraft: false,
    closeButtonDisabled: false,
    dirty: false,
    dirtyText: "有尚未保存的更改",
    sheet: false,
    bodyScrollable: true,
    bodyTone: "subtle",
    tone: "primary",
});

const emit = defineEmits<{
    "update:modelValue": [value: boolean];
    confirm: [];
    cancel: [];
    "save-draft": [];
}>();

const dialogRef = shallowRef<HTMLElement | null>(null);
const lastFocusedElement = shallowRef<HTMLElement | null>(null);
const modalId = Symbol("smart-modal");
const titleId = `smart-modal-title-${useId()}`;
const isPresetWidth = computed(
    () =>
        props.width === "small" ||
        props.width === "medium" ||
        props.width === "large" ||
        props.width === "xlarge",
);
const widthClass = computed(() =>
    isPresetWidth.value ? `is-${props.width}` : "",
);
const widthStyle = computed(() => {
    if (isPresetWidth.value) {
        return undefined;
    }

    return {
        width:
            typeof props.width === "number" ? `${props.width}px` : props.width,
    };
});

const close = async () => {
    if (!props.closable || props.loading) return;
    if (props.beforeClose && !(await props.beforeClose())) return;
    emit("update:modelValue", false);
    emit("cancel");
};

const confirm = () => {
    if (props.loading) return;
    emit("confirm");
};

const saveDraft = () => {
    if (props.loading) return;
    emit("save-draft");
};

const focusDialog = async () => {
    await nextTick();
    const dialog = dialogRef.value;
    if (!dialog) return;
    const focusable = dialog.querySelector<HTMLElement>(focusableSelector);
    (focusable ?? dialog).focus();
};

const handleKeydown = (event: KeyboardEvent) => {
    if (!props.modelValue || modalStack.at(-1) !== modalId) return;

    if (event.key === "Escape") {
        event.preventDefault();
        void close();
        return;
    }

    if (event.key !== "Tab") return;

    const dialog = dialogRef.value;
    if (!dialog) return;

    const focusable: HTMLElement[] = [];
    const nodes = dialog.querySelectorAll<HTMLElement>(focusableSelector);

    for (let i = 0; i < nodes.length; i++) {
        const element = nodes[i];
        if (element && element.offsetParent !== null) {
            focusable.push(element);
        }
    }

    if (!focusable.length) {
        event.preventDefault();
        dialog.focus();
        return;
    }

    const first = focusable.at(0);
    const last = focusable.at(-1);

    if (!first || !last) {
        event.preventDefault();
        dialog.focus();
        return;
    }

    if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
    }
};

watch(
    () => props.modelValue,
    (visible) => {
        if (visible) {
            lastFocusedElement.value =
                document.activeElement as HTMLElement | null;
            document.addEventListener("keydown", handleKeydown);
            registerModal(modalId);
            void focusDialog();
            return;
        }

        document.removeEventListener("keydown", handleKeydown);
        unregisterModal(modalId);
        lastFocusedElement.value?.focus();
        lastFocusedElement.value = null;
    },
);

onBeforeUnmount(() => {
    document.removeEventListener("keydown", handleKeydown);
    unregisterModal(modalId);
    activeTimeline?.kill();
    activeTimeline = null;
});

/* === GSAP 统一时间轴：遮罩 + 面板入场/退场 === */
let activeTimeline: gsap.core.Timeline | null = null;
/** 标记 done() 是否已被调用，防止快速切换时重复调用 */
let doneCalled = false;

const safeDone = (done: () => void) => {
    if (doneCalled) return;
    doneCalled = true;
    done();
};

const onBeforeEnter = (el: Element) => {
    if (isReduced.value) return;
    // 快速关闭时先 kill 旧 Timeline
    if (activeTimeline) {
        activeTimeline.kill();
        activeTimeline = null;
    }
    doneCalled = false;
    const overlay = el as HTMLElement;
    const panel = overlay.querySelector<HTMLElement>(".smart-modal");
    gsap.set(overlay, { autoAlpha: 0 });
    if (panel) gsap.set(panel, { autoAlpha: 0, y: 12, scale: 0.98 });
};

const onEnter = (el: Element, done: () => void) => {
    if (isReduced.value) {
        safeDone(done);
        return;
    }
    // 快速关闭时先 kill 旧 Timeline
    if (activeTimeline) {
        activeTimeline.kill();
        activeTimeline = null;
    }
    doneCalled = false;
    const overlay = el as HTMLElement;
    const panel = overlay.querySelector<HTMLElement>(".smart-modal");
    const staggerEls = overlay.querySelectorAll<HTMLElement>("[data-modal-stagger]");
    const tl = gsap.timeline({
        defaults: { ease: motionEase.ease },
        onComplete: () => {
            activeTimeline = null;
            safeDone(done);
        },
    });
    activeTimeline = tl;
    tl.to(overlay, { autoAlpha: 1, duration: motionDuration.modalIn / 1000 }, 0);
    if (panel) {
        tl.to(
            panel,
            {
                autoAlpha: 1,
                y: 0,
                scale: 1,
                duration: motionDuration.modalIn / 1000,
            },
            0.04,
        );
    }
    // 内容分段入场：GSAP stagger 替代硬编码 CSS 延迟
    if (staggerEls.length) {
        tl.from(
            staggerEls,
            {
                autoAlpha: 0,
                y: 6,
                duration: 0.24,
                stagger: 0.06,
            },
            0.1,
        );
    }
};

const onAfterEnter = (el: Element) => {
    // 交还 CSS 控制，避免 GSAP 内联样式残留
    gsap.set(el as HTMLElement, { clearProps: "all" });
};

const onBeforeLeave = (el: Element) => {
    if (isReduced.value) return;
    // 快速关闭时先 kill 旧 Timeline
    if (activeTimeline) {
        activeTimeline.kill();
        activeTimeline = null;
    }
    doneCalled = false;
    const overlay = el as HTMLElement;
    const panel = overlay.querySelector<HTMLElement>(".smart-modal");
    gsap.set(overlay, { autoAlpha: 1 });
    if (panel) gsap.set(panel, { autoAlpha: 1, y: 0, scale: 1 });
};

const onLeave = (el: Element, done: () => void) => {
    if (isReduced.value) {
        safeDone(done);
        return;
    }
    // 快速关闭时先 kill 旧 Timeline
    if (activeTimeline) {
        activeTimeline.kill();
        activeTimeline = null;
    }
    doneCalled = false;
    const overlay = el as HTMLElement;
    const panel = overlay.querySelector<HTMLElement>(".smart-modal");
    const tl = gsap.timeline({
        defaults: { ease: motionEase.easeIn },
        onComplete: () => {
            activeTimeline = null;
            safeDone(done);
        },
    });
    activeTimeline = tl;
    tl.to(overlay, { autoAlpha: 0, duration: motionDuration.modalOut / 1000 }, 0);
    if (panel) {
        tl.to(
            panel,
            {
                autoAlpha: 0,
                y: 12,
                scale: 0.97,
                duration: motionDuration.modalOut / 1000,
            },
            0,
        );
    }
};

const onAfterLeave = () => {
    // 无需额外清理
};
</script>

<template>
    <Teleport to="body">
        <Transition
            :css="false"
            @before-enter="onBeforeEnter"
            @enter="onEnter"
            @after-enter="onAfterEnter"
            @before-leave="onBeforeLeave"
            @leave="onLeave"
            @after-leave="onAfterLeave"
        >
            <div
                v-if="modelValue"
                class="smart-modal-overlay"
                @click.self="closeOnOverlay && close()"
            >
                <article
                    ref="dialogRef"
                    class="smart-modal"
                        :class="[
                            widthClass,
                            `tone-${tone}`,
                            {
                                'is-sheet': sheet,
                                'has-neutral-body': bodyTone === 'neutral',
                            },
                        ]"
                        :style="widthStyle"
                        role="dialog"
                        aria-modal="true"
                        :aria-labelledby="titleId"
                        tabindex="-1"
                    >
                        <slot name="header">
                            <header
                                class="dialog-header"
                                data-modal-stagger="1"
                            >
                                <slot name="icon">
                                    <span
                                        class="dialog-icon"
                                        aria-hidden="true"
                                    >
                                        <SvgIcon :name="icon" size="sm" />
                                    </span>
                                </slot>
                                <div>
                                    <h2 :id="titleId">{{ title }}</h2>
                                    <p v-if="description">{{ description }}</p>
                                </div>
                                <BaseButton
                                    v-if="closable"
                                    class="smart-modal-close"
                                    variant="text"
                                    aria-label="关闭"
                                    :disabled="loading || closeButtonDisabled"
                                    @click="close"
                                >
                                    <SvgIcon name="close" size="sm" />
                                </BaseButton>
                            </header>
                        </slot>

                        <main
                            class="smart-modal-body"
                            :class="{ 'is-scroll-locked': !bodyScrollable }"
                        >
                            <div
                                v-if="$slots.status"
                                class="smart-modal-status"
                                data-modal-stagger="2"
                            >
                                <slot name="status" />
                            </div>
                            <div
                                class="smart-modal-content"
                                data-modal-stagger="3"
                            >
                                <slot />
                            </div>
                            <div
                                v-if="$slots.warning"
                                class="smart-modal-warning"
                                data-modal-stagger="4"
                            >
                                <slot name="warning" />
                            </div>
                            <div
                                v-if="$slots.preview"
                                class="smart-modal-preview"
                                data-modal-stagger="5"
                            >
                                <slot name="preview" />
                            </div>
                        </main>

                        <slot name="footer">
                            <footer
                                class="smart-modal-footer"
                                :class="{ 'has-dirty': dirty }"
                            >
                                <span class="smart-modal-footer-note">
                                    <slot name="footerHint" />
                                </span>
                                <span
                                    v-if="dirty && !$slots.footerHint"
                                    class="smart-modal-dirty"
                                >
                                    {{ dirtyText }}
                                </span>
                                <div class="smart-modal-actions">
                                    <BaseButton
                                        :disabled="loading"
                                        @click="close"
                                    >
                                        {{ cancelText }}
                                    </BaseButton>
                                    <BaseButton
                                        v-if="showDraft"
                                        :disabled="loading"
                                        @click="saveDraft"
                                    >
                                        {{ draftText }}
                                    </BaseButton>
                                    <BaseButton
                                        class="smart-modal-primary"
                                        variant="primary"
                                        :loading="loading"
                                        @click="confirm"
                                    >
                                        {{ confirmText }}
                                    </BaseButton>
                                </div>
                            </footer>
                        </slot>
                    </article>
            </div>
        </Transition>
    </Teleport>
</template>

<style scoped>
.smart-modal-overlay {
    position: fixed;
    inset: 0;
    z-index: 2200;
    display: grid;
    place-items: center;
    padding: 24px;
    background: var(--color-overlay);
    backdrop-filter: blur(2px);
}

.smart-modal {
    position: relative;
    --modal-accent: var(--color-primary-600);
    --modal-accent-soft: var(--color-primary-50);
    display: flex;
    width: min(100%, 720px);
    max-width: min(900px, calc(100vw - 48px));
    max-height: min(80dvh, 760px);
    flex-direction: column;
    overflow: hidden;
    border: 1px solid var(--color-border-strong);
    border-radius: 20px;
    background: var(--color-card-bg);
    box-shadow: var(--shadow-card-hover);
}
.smart-modal::before {
    position: absolute;
    inset: 0 0 auto;
    height: 3px;
    background: linear-gradient(90deg, var(--modal-accent), color-mix(in srgb, var(--modal-accent) 28%, transparent));
    content: "";
    z-index: 2;
}
.smart-modal.tone-indigo { --modal-accent: var(--tone-purple); --modal-accent-soft: var(--tone-purple-soft); }
.smart-modal.tone-orange { --modal-accent: var(--tone-orange); --modal-accent-soft: var(--tone-orange-soft); }
.smart-modal.tone-teal { --modal-accent: var(--tone-teal); --modal-accent-soft: var(--tone-teal-soft); }
.smart-modal.tone-green { --modal-accent: var(--color-success); --modal-accent-soft: var(--color-success-soft); }
.smart-modal.tone-purple { --modal-accent: var(--tone-purple); --modal-accent-soft: var(--tone-purple-soft); }
.smart-modal.tone-red { --modal-accent: var(--color-danger); --modal-accent-soft: var(--color-danger-soft); }

.smart-modal.is-small {
    width: min(100%, 440px);
}
.smart-modal.is-medium {
    width: min(100%, 560px);
}
.smart-modal.is-large {
    width: min(100%, 720px);
}
.smart-modal.is-xlarge {
    width: min(100%, 900px);
}

.smart-modal-header {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 18px 24px;
    border-bottom: 1px solid var(--color-border);
    background: linear-gradient(
        135deg,
        var(--color-card-bg),
        var(--color-primary-50)
    );
    flex: 0 0 auto;
}

.smart-modal-icon {
    display: grid;
    width: 44px;
    height: 44px;
    flex: 0 0 44px;
    place-items: center;
    border-radius: 12px;
    color: var(--color-text-on-primary);
    background: linear-gradient(
        135deg,
        var(--color-primary-600),
        var(--color-primary-500)
    );
    box-shadow: 0 6px 16px var(--color-focus-ring);
}

.smart-modal-title {
    min-width: 0;
    flex: 1;
}

.smart-modal-title h2 {
    color: var(--color-text-primary);
    font-size: 18px;
    font-weight: 800;
    line-height: 1.25;
}

.smart-modal-title p {
    margin-top: 3px;
    color: var(--color-text-secondary);
    font-size: 13px;
}

.smart-modal-status {
    margin: 0 0 20px;
}

.smart-modal-body {
    min-height: 0;
    flex: 1 1 auto;
    overflow-y: auto;
    padding: 20px 24px;
    background: var(--color-surface-subtle);
    scrollbar-color: var(--color-border-strong) transparent;
    scrollbar-width: thin;
}

.smart-modal.has-neutral-body .smart-modal-body {
    background: color-mix(
        in srgb,
        var(--color-card-bg) 94%,
        var(--modal-accent-soft)
    );
}

.smart-modal-body.is-scroll-locked {
    overflow: hidden;
}

.smart-modal-content {
    display: block;
    min-width: 0;
}

.smart-modal-warning,
.smart-modal-preview {
    margin-top: 16px;
}

.smart-modal-footer {
    position: sticky;
    bottom: 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    padding: 14px 24px;
    border-top: 1px solid var(--color-border);
    background: var(--color-card-bg);
    flex: 0 0 auto;
}

.smart-modal-footer-note {
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 700;
}

.smart-modal-dirty {
    color: var(--color-warning);
    font-size: 12px;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 6px;
}

.smart-modal-actions {
    display: flex;
    flex-shrink: 0;
    gap: 12px;
}

.smart-modal-actions :deep(.base-button) {
    height: 42px;
    min-width: 96px;
    margin-left: 0;
    border-radius: 10px;
    transition:
        background-color 160ms var(--motion-ease),
        border-color 160ms var(--motion-ease),
        color 160ms var(--motion-ease),
        box-shadow 160ms var(--motion-ease),
        transform 160ms var(--motion-ease);
}

.smart-modal-actions :deep(.base-button:hover) {
    transform: translateY(-1px);
}

.smart-modal-actions :deep(.base-button:active) {
    transform: scale(0.98);
}

.smart-modal-actions :deep(.smart-modal-primary) {
    border-color: var(--color-primary-600);
    color: var(--color-text-on-primary);
    background: var(--color-primary-600);
}

.smart-modal-actions :deep(.smart-modal-primary:hover) {
    border-color: var(--color-primary-700);
    background: linear-gradient(
        135deg,
        var(--color-primary-700),
        var(--color-primary-600)
    );
    box-shadow: 0 8px 18px var(--color-focus-ring);
}

.smart-modal :deep(input:not(.el-input__inner)),
.smart-modal :deep(select),
.smart-modal :deep(textarea),
.smart-modal :deep(.el-input__wrapper) {
    min-height: 40px;
    border-color: var(--color-border);
    border-radius: 10px;
    background: var(--color-card-bg);
}

.smart-modal :deep(.settings-input) {
    transition: border-color 160ms var(--motion-ease), box-shadow 160ms var(--motion-ease), background-color 160ms;
}
.smart-modal :deep(.settings-input:hover:not(:disabled)) {
    border-color: color-mix(in srgb, var(--modal-accent) 45%, var(--color-border));
}
.smart-modal :deep(.modal-field > span),
.smart-modal :deep(.account-field > span) {
    color: var(--color-text-secondary);
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 0.01em;
}
.smart-modal :deep(.device-status-label),
.smart-modal :deep(.role-badge) {
    border: 1px solid color-mix(in srgb, var(--modal-accent) 22%, transparent);
}

.smart-modal :deep(input:not(.el-input__inner):focus),
.smart-modal :deep(select:focus),
.smart-modal :deep(textarea:focus),
.smart-modal :deep(.el-input__wrapper.is-focus) {
    border-color: var(--color-primary-500);
    box-shadow: 0 0 0 3px var(--color-focus-ring);
}

.smart-modal :deep(.dialog-header) {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 18px 24px !important;
    border-bottom: 1px solid var(--color-border) !important;
    background: linear-gradient(
        135deg,
        var(--color-card-bg),
        var(--modal-accent-soft)
    ) !important;
}

.smart-modal :deep(.dialog-icon),
.smart-modal :deep(.ai-icon) {
    display: grid;
    width: 40px !important;
    height: 40px !important;
    flex: 0 0 40px !important;
    place-items: center;
    border-radius: 12px;
    color: var(--color-text-on-primary) !important;
    background: linear-gradient(
        135deg,
        color-mix(in srgb, var(--modal-accent) 88%, white),
        var(--modal-accent)
    ) !important;
    box-shadow: 0 6px 16px color-mix(in srgb, var(--modal-accent) 22%, transparent);
}

.smart-modal :deep(.base-button.is-primary:not(.is-plain)) {
    border-color: var(--modal-accent);
    background: var(--modal-accent);
}

.smart-modal :deep(.base-button.is-primary:not(.is-plain):hover:not(:disabled)) {
    border-color: color-mix(in srgb, var(--modal-accent) 82%, black);
    background: linear-gradient(
        135deg,
        color-mix(in srgb, var(--modal-accent) 82%, black),
        var(--modal-accent)
    );
    box-shadow: 0 8px 18px color-mix(in srgb, var(--modal-accent) 20%, transparent);
}

.smart-modal :deep(.base-button.is-plain.is-primary) {
    border-color: var(--modal-accent);
    color: var(--modal-accent);
}

.smart-modal :deep(.base-button.is-plain.is-primary:hover:not(:disabled)) {
    border-color: var(--modal-accent);
    background: var(--modal-accent-soft);
    color: var(--modal-accent);
}

.smart-modal :deep(.dialog-header h2) {
    color: var(--color-text-primary);
    font-size: 18px;
    font-weight: 800;
    line-height: 1.25;
}

.smart-modal :deep(.dialog-header p) {
    margin-top: 3px;
    color: var(--color-text-secondary);
    font-size: 13px;
}

.smart-modal-close {
    display: grid;
    width: 32px !important;
    min-width: 32px !important;
    height: 32px !important;
    margin-left: auto;
    place-items: center;
    border-radius: 8px !important;
    padding: 0 !important;
    color: var(--color-text-tertiary);
    transition:
        background-color 160ms var(--motion-ease),
        color 160ms var(--motion-ease),
        transform 160ms var(--motion-ease);
}

.smart-modal-close:hover {
    color: var(--color-text-primary);
    background: var(--color-surface-hover);
}

.smart-modal-close:focus-visible {
    outline: 2px solid var(--color-primary-500);
    outline-offset: 2px;
}

.smart-modal-close:active {
    transform: scale(0.92);
}

.smart-modal :deep(.dialog-footer) {
    position: sticky;
    bottom: 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    padding: 16px 28px !important;
    border-top: 1px solid var(--color-border) !important;
    background: var(--color-card-bg) !important;
}

.smart-modal :deep(.dialog-footer > span),
.smart-modal :deep(.dialog-footer > p) {
    color: var(--color-text-tertiary);
    font-size: 13px;
}

.smart-modal :deep(.dialog-footer > div) {
    display: flex;
    gap: 12px;
}

.smart-modal :deep(.el-button:not(.close-button)) {
    min-width: 92px;
    height: 42px;
    margin-left: 0;
    border-radius: 10px;
    transition:
        background-color 160ms var(--motion-ease),
        border-color 160ms var(--motion-ease),
        color 160ms var(--motion-ease),
        box-shadow 160ms var(--motion-ease),
        transform 160ms var(--motion-ease);
}

.smart-modal :deep(.el-button:not(.close-button):hover) {
    transform: translateY(-1px);
}

.smart-modal :deep(.el-button:not(.close-button):active) {
    transform: scale(0.98);
}

/* 遮罩 + 面板过渡由 BaseSmartModal 的 GSAP 统一时间轴驱动 */
/* 内容分段入场由 GSAP stagger 替代 */

@media (max-width: 720px) {
    .smart-modal-overlay {
        padding: 16px;
        align-items: center;
    }

    .smart-modal-footer {
        align-items: stretch;
        flex-direction: column;
    }

    .smart-modal-actions {
        justify-content: flex-end;
    }

    .smart-modal :deep(.dialog-header) {
        padding: 16px 18px !important;
    }

    .smart-modal-body {
        padding: 16px 18px;
    }

    .smart-modal :deep(.dialog-footer) {
        align-items: stretch;
        flex-direction: column;
        padding: 12px 18px !important;
    }

    .smart-modal :deep(.dialog-footer > div) {
        justify-content: flex-end;
    }
}

/* 底部抽屉模式（移动端复杂弹窗） */
.smart-modal.is-sheet {
    border-radius: 20px 20px 0 0;
    max-height: min(90dvh, 800px);
    margin-top: auto;
}

.is-sheet .smart-modal-body {
    padding-bottom: calc(20px + env(safe-area-inset-bottom, 0px));
}

@media (max-width: 720px) {
    .smart-modal-overlay:has(.is-sheet) {
        align-items: flex-end;
        padding: 0;
    }

    .smart-modal.is-sheet {
        width: 100%;
        max-width: 100%;
        border-radius: 20px 20px 0 0;
        border-bottom: none;
    }
}

@media (prefers-reduced-motion: reduce) {
    .smart-modal-actions :deep(.base-button:hover),
    .smart-modal-close:hover {
        transform: none;
    }
}
</style>
