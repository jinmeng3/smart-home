<script setup lang="ts">
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
    <TransitionGroup :tag="tag" :name="name">
        <slot />
    </TransitionGroup>
</template>
