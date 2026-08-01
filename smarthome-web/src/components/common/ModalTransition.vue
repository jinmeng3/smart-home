<script setup lang="ts">
withDefaults(
    defineProps<{
        name?: "fade-scale" | "slide-up" | "dialog-enter" | "dialog-leave";
        mode?: "in-out" | "out-in" | "default";
        appear?: boolean;
    }>(),
    {
        name: "fade-scale",
        mode: "default",
        appear: false,
    },
);
</script>

<template>
    <Transition :appear="appear" :mode="mode === 'default' ? undefined : mode" :name="name">
        <slot />
    </Transition>
</template>

<style>
.fade-scale-enter-active,
.fade-scale-leave-active,
.slide-up-enter-active,
.slide-up-leave-active,
.dialog-enter-enter-active,
.dialog-enter-leave-active,
.dialog-leave-enter-active,
.dialog-leave-leave-active {
    transition:
        opacity 250ms cubic-bezier(0.16, 1, 0.3, 1),
        transform 250ms cubic-bezier(0.16, 1, 0.3, 1);
    will-change: opacity, transform;
}

.fade-scale-enter-from,
.dialog-enter-enter-from {
    opacity: 0;
    transform: translateY(20px) scale(0.96);
}

.fade-scale-leave-to,
.dialog-leave-leave-to,
.dialog-enter-leave-to {
    opacity: 0;
    transform: translateY(12px) scale(0.97);
}

.slide-up-enter-from,
.slide-up-leave-to {
    opacity: 0;
    transform: translateY(14px) scale(0.985);
}

.dialog-fade-enter-active,
.dialog-fade-leave-active {
    animation-duration: 250ms !important;
}

.dialog-fade-enter-from,
.dialog-fade-leave-to {
    opacity: 0;
}

.dialog-fade-enter-active .el-overlay,
.dialog-fade-leave-active .el-overlay {
    transition: opacity 250ms ease;
}

.el-overlay {
    background: rgb(15 23 42 / 35%) !important;
    backdrop-filter: blur(4px);
}

.dialog-fade-enter-active .el-overlay-dialog,
.dialog-fade-leave-active .el-overlay-dialog {
    animation: none !important;
}

.dialog-fade-enter-active .el-dialog {
    animation: orion-dialog-enter 250ms cubic-bezier(0.16, 1, 0.3, 1) both !important;
    transform-origin: 50% 50%;
    will-change: opacity, transform;
}

.dialog-fade-leave-active .el-dialog {
    animation: orion-dialog-leave 250ms cubic-bezier(0.4, 0, 1, 1) both !important;
    transform-origin: 50% 50%;
    will-change: opacity, transform;
}

.dialog-fade-enter-active .orion-base-modal .orion-modal-content > *,
.dialog-fade-enter-active .orion-base-modal .dialog-footer {
    animation: orion-dialog-content 250ms cubic-bezier(0.16, 1, 0.3, 1) both;
}

.dialog-fade-enter-active .orion-base-modal .orion-modal-content > :nth-child(1) {
    animation-delay: 70ms;
}

.dialog-fade-enter-active .orion-base-modal .orion-modal-content > :nth-child(2) {
    animation-delay: 110ms;
}

.dialog-fade-enter-active .orion-base-modal .dialog-footer {
    animation-delay: 150ms;
}

.dialog-fade-enter-active .el-dialog__header,
.dialog-fade-enter-active .el-dialog__body > :first-child,
.dialog-fade-enter-active .el-dialog__body > :nth-child(2),
.dialog-fade-enter-active .el-dialog__footer {
    animation: orion-dialog-content 240ms cubic-bezier(0.16, 1, 0.3, 1) both;
}

.dialog-fade-enter-active .el-dialog__header { animation-delay: 40ms; }
.dialog-fade-enter-active .el-dialog__body > :first-child { animation-delay: 90ms; }
.dialog-fade-enter-active .el-dialog__body > :nth-child(2) { animation-delay: 140ms; }
.dialog-fade-enter-active .el-dialog__footer { animation-delay: 190ms; }

.el-dialog button:not(:disabled) {
    transition:
        color 160ms ease,
        border-color 160ms ease,
        background-color 160ms ease,
        box-shadow 160ms ease,
        transform 140ms ease !important;
}

.el-dialog button:not(:disabled):hover { transform: translateY(-1px); }
.el-dialog button:not(:disabled):active { transform: scale(0.98); }

.el-dialog input:not(.el-input__inner),
.el-dialog textarea,
.el-dialog select,
.el-dialog .el-input__wrapper {
    transition:
        border-color 180ms ease,
        box-shadow 180ms ease !important;
}

.el-dialog input:not(.el-input__inner):focus,
.el-dialog textarea:focus,
.el-dialog select:focus,
.el-dialog .el-input__wrapper.is-focus {
    border-color: var(--color-primary-600) !important;
    box-shadow: 0 0 0 3px rgb(37 99 235 / 15%) !important;
}

.setting-card,
.settings-card,
.settings-section {
    transition:
        border-color 180ms ease,
        box-shadow 180ms ease,
        transform 180ms ease;
}

.setting-card:hover,
.settings-card:hover,
.settings-section:hover {
    border-color: var(--color-primary-300);
    box-shadow: 0 8px 20px rgb(15 23 42 / 7%);
    transform: translateY(-2px);
}

.primary-button,
.secondary-button,
.motion-button {
    transition:
        color 160ms ease,
        border-color 160ms ease,
        background-color 160ms ease,
        box-shadow 160ms ease,
        transform 140ms ease;
}

.primary-button:not(:disabled):hover,
.secondary-button:not(:disabled):hover,
.motion-button:not(:disabled):hover {
    transform: translateY(-1px);
}

.primary-button:not(:disabled):active,
.secondary-button:not(:disabled):active,
.motion-button:not(:disabled):active {
    transform: scale(0.98);
}

.button-loading {
    pointer-events: none;
}

.button-loading::before {
    display: inline-block;
    width: 14px;
    height: 14px;
    margin-right: 7px;
    border: 2px solid currentcolor;
    border-right-color: transparent;
    border-radius: 50%;
    vertical-align: -2px;
    animation: orion-loading-spin 700ms linear infinite;
    content: "";
}

@keyframes orion-dialog-enter {
    from { opacity: 0; transform: translateY(20px) scale(0.96); }
    to { opacity: 1; transform: translateY(0) scale(1); }
}

@keyframes orion-dialog-leave {
    from { opacity: 1; transform: translateY(0) scale(1); }
    to { opacity: 0; transform: translateY(12px) scale(0.97); }
}

@keyframes orion-dialog-content {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes orion-loading-spin {
    to { transform: rotate(360deg); }
}

@media (prefers-reduced-motion: reduce) {
    .fade-scale-enter-active,
    .fade-scale-leave-active,
    .slide-up-enter-active,
    .slide-up-leave-active,
    .dialog-enter-enter-active,
    .dialog-enter-leave-active,
    .dialog-leave-enter-active,
    .dialog-leave-leave-active,
    .dialog-fade-enter-active,
    .dialog-fade-leave-active,
    .dialog-fade-enter-active .el-dialog,
    .dialog-fade-leave-active .el-dialog,
    .dialog-fade-enter-active .el-dialog__header,
    .dialog-fade-enter-active .el-dialog__body > *,
    .dialog-fade-enter-active .el-dialog__footer {
        animation-duration: 1ms !important;
        animation-delay: 0ms !important;
        transition-duration: 1ms !important;
    }
}
</style>
