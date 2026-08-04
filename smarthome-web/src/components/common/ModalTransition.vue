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
    <Transition
        :appear="appear"
        :mode="mode === 'default' ? undefined : mode"
        :name="name"
    >
        <slot />
    </Transition>
</template>

<style>
.fade-scale-enter-active,
.fade-scale-leave-active,
.slide-up-enter-active,
.slide-up-leave-active {
    transition:
        opacity 250ms cubic-bezier(0.16, 1, 0.3, 1),
        transform 250ms cubic-bezier(0.16, 1, 0.3, 1);
    will-change: opacity, transform;
}

.fade-scale-enter-from {
    opacity: 0;
    transform: translateY(20px) scale(0.96);
}

.fade-scale-leave-to {
    opacity: 0;
    transform: translateY(12px) scale(0.97);
}

.slide-up-enter-from,
.slide-up-leave-to {
    opacity: 0;
    transform: translateY(14px) scale(0.985);
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
</style>
