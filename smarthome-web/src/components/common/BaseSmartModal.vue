<script setup lang="ts">
import {
    computed,
    nextTick,
    onBeforeUnmount,
    shallowRef,
    useId,
    watch,
} from "vue";
import { ElButton } from "element-plus";
import SvgIcon from "./SvgIcon.vue";
import "element-plus/theme-chalk/el-button.css";

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

type SmartModalWidth = "small" | "medium" | "large" | string | number;

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
}

const focusableSelector = [
    "a[href]",
    "button:not([disabled])",
    "input:not([disabled])",
    "select:not([disabled])",
    "textarea:not([disabled])",
    "[tabindex]:not([tabindex='-1'])",
].join(",");

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
        props.width === "large",
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
});
</script>

<template>
    <Teleport to="body">
        <Transition name="smart-modal-overlay">
            <div
                v-if="modelValue"
                class="smart-modal-overlay"
                @click.self="closeOnOverlay && close()"
            >
                <Transition name="smart-modal" appear>
                    <article
                        ref="dialogRef"
                        class="smart-modal"
                        :class="widthClass"
                        :style="widthStyle"
                        role="dialog"
                        aria-modal="true"
                        :aria-labelledby="titleId"
                        tabindex="-1"
                    >
                        <slot name="header">
                            <header
                                class="dialog-header smart-modal-stagger-1"
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
                                <ElButton
                                    v-if="closable"
                                    class="close-button"
                                    text
                                    aria-label="关闭"
                                    :disabled="loading || closeButtonDisabled"
                                    @click="close"
                                >
                                    <SvgIcon name="close" size="sm" />
                                </ElButton>
                            </header>
                        </slot>

                        <main class="smart-modal-body">
                            <div
                                v-if="$slots.status"
                                class="smart-modal-status smart-modal-stagger-2"
                            >
                                <slot name="status" />
                            </div>
                            <div
                                class="smart-modal-content smart-modal-stagger-3"
                            >
                                <slot />
                            </div>
                            <div
                                v-if="$slots.warning"
                                class="smart-modal-warning smart-modal-stagger-4"
                            >
                                <slot name="warning" />
                            </div>
                            <div
                                v-if="$slots.preview"
                                class="smart-modal-preview smart-modal-stagger-5"
                            >
                                <slot name="preview" />
                            </div>
                        </main>

                        <slot name="footer">
                            <footer
                                class="smart-modal-footer smart-modal-stagger-6"
                            >
                                <span class="smart-modal-footer-note">
                                    <slot name="footerHint" />
                                </span>
                                <div class="smart-modal-actions">
                                    <ElButton
                                        :disabled="loading"
                                        @click="close"
                                    >
                                        {{ cancelText }}
                                    </ElButton>
                                    <ElButton
                                        v-if="showDraft"
                                        :disabled="loading"
                                        @click="saveDraft"
                                    >
                                        {{ draftText }}
                                    </ElButton>
                                    <ElButton
                                        class="smart-modal-primary"
                                        :loading="loading"
                                        type="primary"
                                        @click="confirm"
                                    >
                                        {{ confirmText }}
                                    </ElButton>
                                </div>
                            </footer>
                        </slot>
                    </article>
                </Transition>
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
    display: flex;
    width: min(100%, 720px);
    max-width: min(980px, calc(100vw - 48px));
    max-height: 88vh;
    flex-direction: column;
    overflow: hidden;
    border: 1px solid var(--color-border-strong);
    border-radius: 20px;
    background: var(--color-card-bg);
    box-shadow: var(--shadow-card-hover);
}

.smart-modal.is-small {
    width: min(100%, 560px);
}
.smart-modal.is-medium {
    width: min(100%, 760px);
}
.smart-modal.is-large {
    width: min(100%, 980px);
}

.smart-modal-header {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 22px 28px;
    border-bottom: 1px solid var(--color-border);
    background: linear-gradient(
        135deg,
        var(--color-card-bg),
        var(--color-primary-50)
    );
}

.smart-modal-icon {
    display: grid;
    width: 56px;
    height: 56px;
    flex: 0 0 56px;
    place-items: center;
    border-radius: 16px;
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
    font-size: 24px;
    font-weight: 700;
    line-height: 1.2;
}

.smart-modal-title p {
    margin-top: 5px;
    color: var(--color-text-secondary);
    font-size: 14px;
}

.smart-modal-status {
    margin: 0 0 20px;
}

.smart-modal-body {
    min-height: 0;
    overflow-y: auto;
    padding: 22px 24px;
    background: var(--color-surface-subtle);
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
    padding: 16px 28px;
    border-top: 1px solid var(--color-border);
    background: var(--color-card-bg);
}

.smart-modal-footer-note {
    color: var(--color-text-tertiary);
    font-size: 13px;
}

.smart-modal-actions {
    display: flex;
    flex-shrink: 0;
    gap: 12px;
}

.smart-modal-actions :deep(.el-button) {
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

.smart-modal-actions :deep(.el-button:hover) {
    transform: translateY(-1px);
}

.smart-modal-actions :deep(.el-button:active) {
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
    min-height: 42px;
    border-color: var(--color-border);
    border-radius: 10px;
    background: var(--color-card-bg);
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
    gap: 16px;
    padding: 22px 28px !important;
    border-bottom: 1px solid var(--color-border) !important;
    background: linear-gradient(
        135deg,
        var(--color-card-bg),
        var(--color-primary-50)
    ) !important;
}

.smart-modal :deep(.dialog-icon),
.smart-modal :deep(.ai-icon) {
    display: grid;
    width: 48px !important;
    height: 48px !important;
    flex: 0 0 48px !important;
    place-items: center;
    border-radius: 14px;
    color: var(--color-text-on-primary) !important;
    background: linear-gradient(
        135deg,
        var(--color-primary-600),
        var(--color-primary-500)
    ) !important;
    box-shadow: 0 6px 16px var(--color-focus-ring);
}

.smart-modal :deep(.dialog-header h2) {
    color: var(--color-text-primary);
    font-size: 21px;
    font-weight: 800;
    line-height: 1.2;
}

.smart-modal :deep(.dialog-header p) {
    margin-top: 4px;
    color: var(--color-text-secondary);
    font-size: 14px;
}

.smart-modal :deep(.close-button) {
    display: grid;
    width: 38px;
    min-width: 38px;
    height: 38px;
    margin-left: auto;
    place-items: center;
    border-radius: 50%;
    color: var(--color-text-tertiary);
    transition:
        background-color 160ms var(--motion-ease),
        color 160ms var(--motion-ease),
        transform 160ms var(--motion-ease);
}

.smart-modal :deep(.close-button:hover) {
    color: var(--color-text-primary);
    background: var(--color-surface-hover);
}

.smart-modal :deep(.close-button:active) {
    transform: scale(0.94);
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

.smart-modal-overlay-enter-active,
.smart-modal-overlay-leave-active {
    transition: opacity 260ms cubic-bezier(0.16, 1, 0.3, 1);
}

.smart-modal-overlay-enter-from,
.smart-modal-overlay-leave-to {
    opacity: 0;
}

.smart-modal-enter-active {
    transition:
        opacity 260ms cubic-bezier(0.16, 1, 0.3, 1),
        transform 260ms cubic-bezier(0.16, 1, 0.3, 1);
}

.smart-modal-leave-active {
    transition:
        opacity 180ms cubic-bezier(0.16, 1, 0.3, 1),
        transform 180ms cubic-bezier(0.16, 1, 0.3, 1);
}

.smart-modal-enter-from,
.smart-modal-leave-to {
    opacity: 0;
    transform: translateY(18px) scale(0.97);
}

.smart-modal-stagger-1,
.smart-modal-stagger-2,
.smart-modal-stagger-3,
.smart-modal-stagger-4,
.smart-modal-stagger-5,
.smart-modal-stagger-6 {
    animation: smart-modal-content-enter 220ms cubic-bezier(0.16, 1, 0.3, 1)
        both;
}

.smart-modal-stagger-1 {
    animation-delay: 35ms;
}
.smart-modal-stagger-2 {
    animation-delay: 75ms;
}
.smart-modal-stagger-3 {
    animation-delay: 115ms;
}
.smart-modal-stagger-4 {
    animation-delay: 155ms;
}
.smart-modal-stagger-5 {
    animation-delay: 195ms;
}
.smart-modal-stagger-6 {
    animation-delay: 235ms;
}

@keyframes smart-modal-content-enter {
    from {
        opacity: 0;
        transform: translateY(6px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@media (max-width: 720px) {
    .smart-modal-overlay {
        padding: 16px;
    }

    .smart-modal-footer {
        align-items: stretch;
        flex-direction: column;
    }

    .smart-modal-actions {
        justify-content: flex-end;
    }
}

@media (prefers-reduced-motion: reduce) {
    .smart-modal-enter-active,
    .smart-modal-leave-active,
    .smart-modal-overlay-enter-active,
    .smart-modal-overlay-leave-active {
        transition-duration: 80ms;
    }

    .smart-modal-enter-from,
    .smart-modal-leave-to {
        transform: none;
    }

    .smart-modal-stagger-1,
    .smart-modal-stagger-2,
    .smart-modal-stagger-3,
    .smart-modal-stagger-4,
    .smart-modal-stagger-5,
    .smart-modal-stagger-6 {
        animation-duration: 1ms;
        animation-delay: 0ms;
    }
}
</style>
