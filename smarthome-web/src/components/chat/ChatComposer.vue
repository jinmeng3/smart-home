<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import SvgIcon from "../common/SvgIcon.vue";
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

/* === 输入框自动增高 === */
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

/* === 模型菜单 === */
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
            <SvgIcon name="plus" />
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
                <SvgIcon
                    name="chevron-down"
                    size="sm"
                    class="orion-chevron"
                    :class="{ 'rotate-180': modelMenuOpen }"
                />
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
                    <SvgIcon
                        v-if="model.name === store.activeModel"
                        name="check"
                        size="sm"
                    />
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
            <SvgIcon name="mic" />
        </button>

        <button
            class="send-btn motion-button grid h-11 w-11 shrink-0 place-items-center rounded-full bg-[var(--color-text-primary)] text-white shadow-md transition hover:scale-105 disabled:opacity-35"
            type="submit"
            :disabled="sendDisabled"
            :title="generating ? '停止生成' : '发送'"
        >
            <!-- 单个 SvgIcon 实例通过动态 name 切换实现连续 Morph 动画 -->
            <SvgIcon :name="generating ? 'square' : 'send'" />
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

/* 模型下拉箭头旋转 */
.orion-chevron.rotate-180 {
    transform: rotate(180deg);
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