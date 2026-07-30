<script setup lang="ts">
import { computed, toRef } from "vue";
import { useAnimatedNumber } from "../../composables/useAnimatedNumber";

const props = withDefaults(
    defineProps<{
        value: number;
        decimals?: number;
        suffix?: string;
        duration?: number;
    }>(),
    {
        decimals: 0,
        suffix: "",
        duration: 600,
    },
);

const targetValue = toRef(props, "value");
const { displayValue } = useAnimatedNumber({
    startValue: props.value,
    endValue: targetValue,
    decimals: props.decimals,
    suffix: props.suffix,
    duration: props.duration,
});

const renderedValue = computed(() => displayValue.value);
</script>

<template>
    <span>{{ renderedValue }}</span>
</template>
