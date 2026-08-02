<script setup lang="ts">
import { onBeforeUnmount, ref } from "vue";
import type { ChatMessage } from "../../types/chat";
import AnimatedList from "../animation/AnimatedList.vue";
import DeviceCard from "./DeviceCard.vue";

defineProps<{
    message: ChatMessage;
}>();

const copied = ref(false);
const recommendations = [
    "开启回家模式",
    "晚上10点切换睡眠模式",
    "无人活动自动关闭灯光",
    "空调节能运行",
];
let copyTimer = 0;

const copyMessage = async (content: string) => {
    await navigator.clipboard?.writeText(content);
    copied.value = true;

    window.clearTimeout(copyTimer);
    copyTimer = window.setTimeout(() => {
        copied.value = false;
    }, 1500);
};

onBeforeUnmount(() => {
    window.clearTimeout(copyTimer);
});
</script>

<template>
    <article
        class="ai-message-enter group mb-5 grid grid-cols-[42px_minmax(0,720px)] gap-3"
    >
        <div
            class="grid h-10 w-10 place-items-center rounded-full bg-gradient-to-br from-blue-600 to-sky-400 text-white"
        >
            <img src="/orion-sidebar-icon.svg" alt="Orion Home" />
        </div>

        <div
            class="motion-card rounded-xl border border-[var(--color-border)] bg-[var(--color-card-bg)] px-5 py-4"
        >
            <p
                class="mb-4 block whitespace-pre-wrap break-words text-sm font-medium leading-6 text-slate-600 first-line-stream"
            >
                {{ message.content }}
            </p>
            <div
                v-if="message.content.includes('当前状态')"
                class="grid grid-cols-[1fr_1.2fr] gap-3"
            >
                <DeviceCard />
                <section
                    class="motion-card rounded-lg border border-[var(--color-border-default)] bg-[var(--color-panel-background)] p-4"
                >
                    <h2 class="mb-3 text-base font-bold">🌙 今晚建议</h2>
                    <AnimatedList
                        tag="ol"
                        name="suggestion-list"
                        class="grid gap-3"
                    >
                        <li
                            v-for="(item, index) in recommendations"
                            :key="item"
                            class="grid grid-cols-[24px_minmax(0,1fr)] items-center gap-2 text-sm font-medium text-slate-700"
                            :style="{ transitionDelay: `${index * 70}ms` }"
                        >
                            <span
                                class="grid h-5 w-5 place-items-center rounded-full bg-blue-600 text-xs font-bold text-white"
                                >{{ index + 1 }}</span
                            >
                            {{ item }}
                        </li>
                    </AnimatedList>
                </section>
            </div>
            <div
                class="mt-4 flex gap-4 text-slate-500 opacity-30 transition group-hover:opacity-100"
            >
                <button class="motion-button" type="button">♡</button>
                <button class="motion-button" type="button">♧</button>
                <button
                    class="motion-button"
                    type="button"
                    @click="copyMessage(message.content)"
                >
                    {{ copied ? "✓" : "□" }}
                </button>
                <button class="motion-button" type="button">⟳</button>
            </div>
        </div>
    </article>
</template>

<style scoped>
.first-line-stream {
    animation: stream-line 480ms steps(18, end) both;
}

@keyframes stream-line {
    from {
        max-width: 0;
    }
    to {
        max-width: 100%;
    }
}
</style>
