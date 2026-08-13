<script setup lang="ts">
import { useHomeStore } from "../../stores/home";
import AnimatedNumber from "../animation/AnimatedNumber.vue";
import SvgIcon from "../common/SvgIcon.vue";

const store = useHomeStore();
</script>

<template>
    <section
        class="energy-card motion-card page-enter-stagger min-w-0 rounded-xl border border-[var(--color-border)] bg-[var(--color-card-bg)] px-4 py-2.5 shadow-soft"
        style="animation-delay: 340ms"
    >
        <!-- 标题 + 主数值 同行 -->
        <div class="flex items-center justify-between gap-2">
            <h2
                class="flex items-center gap-1.5 text-[14px] font-extrabold text-slate-800"
            >
                <SvgIcon name="energy" size="sm" />
                能耗
            </h2>
            <strong class="text-lg leading-none text-slate-900">
                <AnimatedNumber :value="store.energyToday" :decimals="2" />
                <small class="text-[11px] font-bold text-slate-400"> kWh</small>
            </strong>
        </div>
        <!-- 次要结论：单行 -->
        <p class="mt-2 flex flex-wrap items-center gap-x-1 text-xs text-slate-500">
            较昨日下降 <b class="text-[var(--color-success)]">8.7%</b>
            <span class="mx-1 text-slate-300">·</span>
            本月 <b class="text-slate-700">326.8</b> kWh
        </p>
    </section>
</template>
