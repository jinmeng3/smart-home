<script setup lang="ts">
withDefaults(
    defineProps<{
        name: string;
        size?: "sm" | "md" | "lg";
    }>(),
    {
        size: "md",
    },
);
</script>

<template>
    <svg class="orion-icon" :class="`is-${size}`" aria-hidden="true">
        <use :href="`#icon-${name}`" />
    </svg>
</template>

<style scoped>
.orion-icon {
    display: inline-block;
    width: 20px;
    height: 20px;
    flex-shrink: 0;
    color: currentColor;
    vertical-align: middle;
}

.orion-icon.is-sm {
    width: 16px;
    height: 16px;
}

.orion-icon.is-lg {
    width: 24px;
    height: 24px;
}
</style>
