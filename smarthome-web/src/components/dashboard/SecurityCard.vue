<script setup lang="ts">
import { ref } from "vue";
import { useHomeStore } from "../../stores/home";
import SvgIcon from "../common/SvgIcon.vue";

const store = useHomeStore();
const expanded = ref(false);
const knowledgeItems = [
    "如何创建回家模式",
    "空调节能设置指南",
    "智能门锁使用说明",
];
</script>

<template>
    <section
        class="motion-card page-enter-stagger min-w-0 rounded-xl border border-[var(--color-border)] bg-[var(--color-card-bg)] p-3 shadow-soft"
        style="animation-delay: 420ms"
    >
        <div class="mb-3 flex items-center justify-between">
            <h2
                class="flex items-center gap-2 text-sm font-extrabold text-slate-800"
            >
                <SvgIcon name="security" size="sm" />
                安防与知识库
            </h2>
            <a class="motion-button text-xs font-bold text-blue-600" href="#"
                >更多</a
            >
        </div>

        <button
            class="alert-once mb-4 flex w-full gap-2 rounded-lg border p-3 text-left transition"
            :class="
                store.securityAlertHandled
                    ? 'border-[var(--color-success-border)] bg-[var(--color-success-soft)]'
                    : 'border-[var(--color-warning-border)] bg-[var(--color-warning-soft)]'
            "
            type="button"
            @click="expanded = !expanded"
        >
            <span
                class="grid h-6 w-6 shrink-0 place-items-center"
                :class="
                    store.securityAlertHandled
                        ? 'text-[var(--color-success)]'
                        : 'warning-shake text-[var(--color-warning)]'
                "
            >
                <SvgIcon
                    :name="
                        store.securityAlertHandled ? 'check-circle' : 'warning'
                    "
                    size="sm"
                />
            </span>
            <div class="min-w-0">
                <strong class="block text-sm text-slate-800">{{
                    store.securityAlertHandled ? "告警已处理" : "门窗传感器异常"
                }}</strong>
                <p class="mt-1 text-xs text-slate-500">厨房窗户 · 10:15</p>
                <Transition name="expand">
                    <div
                        v-if="expanded"
                        class="mt-2 overflow-hidden text-xs leading-5 text-slate-600"
                    >
                        <p>位置：厨房东侧窗户</p>
                        <p>建议：检查窗户闭合状态，并确认传感器电量。</p>
                        <button
                            class="motion-button mt-2 rounded-lg border border-[var(--color-success-border)] bg-[var(--color-panel-background)] px-2 py-1 text-[var(--color-success)]"
                            type="button"
                            @click.stop="store.markAlertHandled"
                        >
                            已处理
                        </button>
                    </div>
                </Transition>
            </div>
        </button>

        <div class="mb-2 text-xs text-slate-500">
            告警数量：
            <Transition name="status-crossfade" mode="out-in">
                <strong :key="store.alertCount" class="text-slate-800">{{
                    store.alertCount
                }}</strong>
            </Transition>
        </div>

        <h3 class="mb-2 text-sm font-bold">知识库</h3>
        <a
            v-for="item in knowledgeItems"
            :key="item"
            class="motion-button mb-2 block truncate text-xs text-slate-600 hover:text-blue-600"
            href="#"
        >
            {{ item }}
        </a>
    </section>
</template>
