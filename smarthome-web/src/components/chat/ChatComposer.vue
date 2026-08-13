<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import { useHomeStore } from "../../stores/home";
import { useAuthStore } from "../../stores/auth";

const emit = defineEmits<{
    send: [content: string];
    stop: [];
}>();

const store = useHomeStore();
const authStore = useAuthStore();
const inputValue = ref("");
const inputRef = ref<HTMLTextAreaElement | null>(null);
const modelMenuOpen = ref(false);
const modelMenuRef = ref<HTMLElement | null>(null);

const generating = computed(
    () => store.agentStatus === "thinking" || store.agentStatus === "executing",
);
const sendDisabled = computed(
    () =>
        !authStore.isAuthenticated ||
        (!generating.value && !inputValue.value.trim()),
);

/* ── 输入框自动增高 ─────────────────────────────────────────── */
const inputMaxHeight = 132;
const resizeInput = () => {
    const el = inputRef.value;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, inputMaxHeight)}px`;
};
const resetInputHeight = () => {
    const el = inputRef.value;
    if (!el) return;
    el.style.height = "auto";
};
watch(inputValue, () => void nextTick(resizeInput));

const onInputKeydown = (event: KeyboardEvent) => {
    if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
        event.preventDefault();
        submit();
        return;
    }
    void nextTick(resizeInput);
};

const submit = () => {
    if (generating.value) {
        emit("stop");
        return;
    }
    const trimmed = inputValue.value.trim();
    if (!trimmed) return;
    emit("send", trimmed);
    inputValue.value = "";
    resetInputHeight();
};

/* ── 模型菜单 ───────────────────────────────────────────────── */
const onClickOutside = (event: MouseEvent) => {
    if (
        modelMenuRef.value &&
        !modelMenuRef.value.contains(event.target as Node)
    ) {
        modelMenuOpen.value = false;
    }
};

const selectModel = (name: string) => {
    void store.selectModel(name);
    modelMenuOpen.value = false;
};

onMounted(() => {
    document.addEventListener("click", onClickOutside);
});

onUnmounted(() => {
    document.removeEventListener("click", onClickOutside);
});
</script>

<template>
    <form
        class="composer-form relative mt-4 flex shrink-0 items-center gap-3 rounded-[22px] border border-[var(--color-border)] bg-[var(--color-card-bg)] px-3 py-2 shadow-soft transition-colors duration-200 focus-within:border-[var(--color-primary-300)] focus-within:shadow-[0_0_0_3px_var(--color-focus-ring),0_10px_28px_rgba(15,23,42,0.08)]"
        @submit.prevent="submit"
    >
        <button
            :disabled="!authStore.isAuthenticated"
            class="composer-icon-button motion-button"
            type="button"
            title="添加附件"
        >
            <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12 5v14M5 12h14" />
            </svg>
        </button>

        <textarea
            ref="inputRef"
            v-model="inputValue"
            rows="1"
            class="composer-input min-w-0 flex-1 resize-none overflow-y-auto border-0 bg-transparent py-2.5 text-base leading-6 outline-none placeholder:text-[var(--color-text-muted)]"
            :disabled="!authStore.isAuthenticated"
            :placeholder="authStore.isAuthenticated ? '询问 Orion Home（Enter 发送，Shift + Enter 换行）' : '登录后可使用智能对话'"
            @keydown="onInputKeydown"
        ></textarea>

        <div class="model-menu relative min-w-0" ref="modelMenuRef">
            <button
                :disabled="!authStore.isAuthenticated"
                class="motion-button flex h-9 max-w-[126px] items-center gap-1.5 rounded-full px-2.5 text-sm font-medium text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-hover)]"
                type="button"
                @click="modelMenuOpen = !modelMenuOpen"
            >
                <span class="truncate">
                    {{ store.activeModel || "选择模型" }}
                </span>
                <svg viewBox="0 0 24 24" class="h-3 w-3 fill-none stroke-current transition-transform duration-200" :class="{ 'rotate-180': modelMenuOpen }" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5">
                    <path d="M6 9l6 6 6-6" />
                </svg>
            </button>
            <div
                v-if="modelMenuOpen"
                class="dropdown-enter absolute bottom-full right-0 z-20 mb-2 max-h-60 min-w-44 overflow-y-auto rounded-xl border border-[var(--color-border)] bg-[var(--color-card-bg)] p-1.5 shadow-lg"
            >
                <button
                    v-for="model in store.availableModels"
                    :key="model.id"
                    class="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-xs font-bold text-[var(--color-text-primary)] transition hover:bg-[var(--color-primary-50)] hover:text-[var(--color-primary-700)]"
                    :class="{
                        'bg-[var(--color-primary-50)] text-[var(--color-primary-700)]':
                            model.name === store.activeModel,
                    }"
                    type="button"
                    @click="selectModel(model.name)"
                >
                    <span
                        class="inline-block h-1.5 w-1.5 rounded-full bg-[var(--color-primary-400)]"
                        :class="{ 'pulse-ring': model.name === store.activeModel }"
                    ></span>
                    {{ model.name }}
                    <svg
                        v-if="model.name === store.activeModel"
                        viewBox="0 0 24 24"
                        class="ml-auto h-3.5 w-3.5 fill-none stroke-[var(--color-primary-600)]"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="3"
                    >
                        <path d="M5 13l4 4L19 7" />
                    </svg>
                </button>
                <div
                    v-if="store.availableModels.length === 0"
                    class="px-3 py-3 text-center text-xs text-[var(--color-text-disabled)]"
                >
                    暂无可用模型
                </div>
            </div>
        </div>

        <button class="composer-icon-button motion-button" type="button" title="语音输入">
            <svg viewBox="0 0 24 24" aria-hidden="true">
                <rect x="9" y="3" width="6" height="11" rx="3" />
                <path d="M5 11a7 7 0 0 0 14 0M12 18v3M9 21h6" />
            </svg>
        </button>

        <button
            class="send-btn motion-button grid h-11 w-11 shrink-0 place-items-center rounded-full bg-[var(--color-text-primary)] text-white shadow-md transition hover:scale-105 disabled:opacity-35"
            type="submit"
            :disabled="sendDisabled"
            :title="generating ? '停止生成' : '发送'"
        >
            <Transition name="send-icon" mode="out-in">
                <svg v-if="generating" key="stop" viewBox="0 0 24 24" aria-hidden="true">
                    <rect x="7" y="7" width="10" height="10" rx="1" />
                </svg>
                <svg v-else key="send" viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M7 12h10M13 8l4 4-4 4" />
                </svg>
            </Transition>
        </button>
    </form>
</template>

<style scoped>
.composer-icon-button {
    display: grid;
    width: 38px;
    height: 38px;
    flex: 0 0 38px;
    place-items: center;
    border-radius: 999px;
    color: var(--color-text-primary);
}

.composer-icon-button:hover {
    background: var(--color-surface-hover);
}

.composer-icon-button svg,
.send-btn svg {
    width: 22px;
    height: 22px;
    fill: none;
    stroke: currentColor;
    stroke-linecap: round;
    stroke-linejoin: round;
    stroke-width: 2;
}

.send-btn svg {
    width: 20px;
    height: 20px;
}

/* 发送/停止图标切换过渡 */
.send-icon-enter-active,
.send-icon-leave-active {
    transition:
        opacity 160ms ease,
        transform 160ms var(--motion-ease);
}
.send-icon-enter-from {
    opacity: 0;
    transform: rotate(-90deg) scale(0.6);
}
.send-icon-leave-to {
    opacity: 0;
    transform: rotate(90deg) scale(0.6);
}

.model-menu {
    max-width: min(240px, 42%);
}

@media (max-width: 560px) {
    .composer-form {
        gap: 5px;
        padding-right: 7px;
        padding-left: 7px;
    }

    .model-menu {
        display: none;
    }
}

@media (max-width: 520px) {
    .model-menu {
        max-width: none;
        flex: 1 1 0;
    }
}
</style>