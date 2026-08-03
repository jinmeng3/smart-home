<script setup lang="ts">
import { ref } from "vue";
import { useHomeStore } from "../../stores/home";
import AutomationCard from "../chat/AutomationCard.vue";
import SvgIcon from "../common/SvgIcon.vue";

const store = useHomeStore();
const expandedId = ref<string | null>("arrive-home");
</script>

<template>
    <section
        class="motion-card page-enter-stagger shrink-0 rounded-xl border border-[var(--color-border)] bg-[var(--color-card-bg)] p-3 shadow-soft"
        style="animation-delay: 180ms"
    >
        <div class="mb-3 flex items-center justify-between">
            <h2
                class="flex items-center gap-2 text-sm font-extrabold text-slate-800"
            >
                <SvgIcon name="calendar" size="sm" />
                家庭日程 / 自动化计划
            </h2>
            <a class="motion-button text-xs font-bold text-blue-600" href="#"
                >更多</a
            >
        </div>

        <div class="mb-3 flex items-center justify-between text-sm">
            <button
                class="motion-button text-slate-400"
                type="button"
                aria-label="上一个日期"
            >
                <SvgIcon name="chevron-left" size="sm" />
            </button>
            <strong>2025年5月20日 星期二</strong>
            <button
                class="motion-button text-slate-400"
                type="button"
                aria-label="下一个日期"
            >
                <SvgIcon name="chevron-right" size="sm" />
            </button>
        </div>

        <div
            class="line-draw relative mb-3 grid gap-2 before:absolute before:left-[60px] before:top-2 before:h-[calc(100%-18px)] before:w-px before:bg-[var(--color-border-strong)]"
        >
            <article
                v-for="(automation, index) in store.automations"
                :key="automation.id"
                class="relative grid grid-cols-[54px_minmax(0,1fr)] gap-3"
                :style="{ animationDelay: `${220 + index * 80}ms` }"
                @mouseenter="expandedId = automation.id"
            >
                <time class="text-sm font-bold text-slate-700">{{
                    automation.time
                }}</time>
                <div
                    class="relative pl-4 before:absolute before:left-0 before:top-1.5 before:h-2 before:w-2 before:rounded-full"
                    :class="{
                        'before:bg-[var(--color-scene-energy)]':
                            automation.id === 'wake-up',
                        'before:bg-[var(--color-scene-home)]':
                            automation.id === 'arrive-home',
                        'before:bg-[var(--color-scene-sleep)]':
                            automation.id === 'sleep',
                    }"
                >
                    <span
                        v-if="automation.id === 'arrive-home'"
                        class="absolute left-[-3px] top-[-1px] h-4 w-4 rounded-full bg-[var(--color-primary-100)] status-pulse"
                    ></span>
                    <strong class="block text-sm">{{ automation.name }}</strong>
                    <p class="mt-1 text-xs leading-5 text-slate-500">
                        {{ automation.description }}
                    </p>
                    <Transition name="expand">
                        <p
                            v-if="expandedId === automation.id"
                            class="mt-2 overflow-hidden rounded-lg bg-[var(--color-surface-subtle)] px-2 py-1.5 text-xs text-[var(--color-text-secondary)]"
                        >
                            {{ automation.actions.join(" · ") }}
                        </p>
                    </Transition>
                </div>
            </article>
        </div>

        <div class="grid gap-2">
            <AutomationCard
                v-for="automation in store.automations.slice(0, 2)"
                :key="automation.id"
                :automation="automation"
            />
        </div>
    </section>
</template>
