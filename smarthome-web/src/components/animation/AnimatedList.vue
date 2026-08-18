<script setup lang="ts">
import { ref } from "vue";

const root = ref<HTMLElement | null>(null);
defineExpose({ root });

withDefaults(
    defineProps<{
        tag?: string;
        name?: string;
    }>(),
    {
        tag: "div",
        name: "animated-list",
    },
);
</script>

<template>
    <TransitionGroup ref="root" :tag="tag" :name="name">
        <slot />
    </TransitionGroup>
</template>
