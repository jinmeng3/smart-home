<script setup lang="ts">
import { ref } from "vue";
import { ElMessage } from "element-plus";
import BaseSmartModal from "../../common/BaseSmartModal.vue";
import SvgIcon from "../../common/SvgIcon.vue";
import { useModalConfirm } from "../../../composables/useModalConfirm";

defineProps<{ modelValue: boolean }>();
const emit = defineEmits<{ "update:modelValue": [value: boolean] }>();

const selectedMode = ref("home");
const selectedScope = ref("all");
const autoSync = ref(true);

const modes = [
    {
        key: "home",
        name: "回家模式",
        icon: "home",
        hint: "开启常用照明、舒适空调",
    },
    {
        key: "away",
        name: "离家模式",
        icon: "security",
        hint: "关闭灯光、开启安防",
    },
    {
        key: "sleep",
        name: "睡眠模式",
        icon: "air-quality",
        hint: "柔和灯光、关闭部分设备",
    },
    {
        key: "movie",
        name: "观影模式",
        icon: "scene",
        hint: "客厅灯光调暗、窗帘关闭",
    },
] as const;
const scopes = ["客厅", "主卧", "次卧", "厨房", "卫生间", "阳台"];

const { loading, confirm } = useModalConfirm(() => {
    ElMessage.success("切换全屋模式操作成功");
    emit("update:modelValue", false);
});
</script>

<template>
    <BaseSmartModal
        :model-value="modelValue"
        title="切换全屋模式"
        description="快速应用家庭场景模式到全屋设备"
        :width="720"
        :loading="loading"
        confirm-text="立即切换"
        @confirm="confirm"
        @update:model-value="emit('update:modelValue', false)"
    >
        <div class="mode-layout">
            <div class="mode-grid">
                <button
                    v-for="mode in modes"
                    :key="mode.key"
                    type="button"
                    class="mode-card"
                    :class="{ selected: selectedMode === mode.key }"
                    @click="selectedMode = mode.key"
                >
                    <span><SvgIcon :name="mode.icon" size="lg" /></span>
                    <b>{{ mode.name }}</b
                    ><small>{{ mode.hint }}</small>
                    <i v-if="selectedMode === mode.key">✓</i>
                </button>
            </div>
            <section class="side-stack">
                <div class="box">
                    <b>应用范围</b>
                    <div class="chips">
                        <button
                            v-for="scope in scopes"
                            :key="scope"
                            type="button"
                            :class="{ active: selectedScope === scope }"
                            @click="selectedScope = scope"
                        >
                            {{ scope }}
                        </button>
                    </div>
                </div>
                <label class="switch-row"
                    ><span
                        >同步执行自动化联动<small
                            >切换模式时同时运行关联自动化</small
                        ></span
                    ><input v-model="autoSync" type="checkbox"
                /></label>
                <div class="box impact">
                    <b>预览影响</b>
                    <p>
                        <SvgIcon name="light" size="sm" />灯光
                        <strong>12 台</strong>
                    </p>
                    <p>
                        <SvgIcon name="air-conditioner" size="sm" />空调
                        <strong>3 台</strong>
                    </p>
                    <p>
                        <SvgIcon name="curtain" size="sm" />窗帘
                        <strong>4 台</strong>
                    </p>
                    <small>共影响 20 台设备</small>
                </div>
            </section>
        </div>
    </BaseSmartModal>
</template>

<style scoped>
.box {
    border: 1px solid var(--color-border-default);
    border-radius: 12px;
    background: var(--color-panel-background);
    padding: 16px;
}
.mode-layout {
    display: grid;
    grid-template-columns: 1.65fr 1fr;
    gap: 16px;
}
.mode-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
}
.mode-card {
    position: relative;
    display: flex;
    min-height: 150px;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    gap: 8px;
    border: 1px solid var(--color-border-default);
    border-radius: 12px;
    background: var(--color-panel-background);
}
.mode-card.selected {
    border-color: var(--color-primary-500);
    box-shadow: 0 0 0 2px var(--color-primary-100);
}
.mode-card > span {
    display: grid;
    width: 54px;
    height: 54px;
    place-items: center;
    border-radius: 50%;
    background: var(--color-primary-100);
    color: var(--color-primary-600);
}
.mode-card small,
.switch-row small {
    display: block;
    color: var(--color-text-tertiary);
}
.mode-card i {
    position: absolute;
    right: 8px;
    top: 8px;
    width: 20px;
    border-radius: 50%;
    background: var(--color-primary-500);
    color: #fff;
}
.side-stack {
    display: flex;
    flex-direction: column;
    gap: 12px;
}
.chips {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 10px;
}
.chips button {
    border: 1px solid var(--color-border-default);
    border-radius: 8px;
    background: var(--color-panel-background);
    padding: 7px 12px;
}
.chips button.active {
    border-color: var(--color-primary-400);
    background: var(--color-primary-100);
    color: var(--color-primary-600);
}
.switch-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px;
}
.switch-row input {
    width: 38px;
    height: 20px;
    accent-color: var(--color-primary-500);
}
.impact p {
    display: flex;
    gap: 8px;
    margin: 10px 0;
}
.impact strong {
    margin-left: auto;
}
@media (max-width: 760px) {
    .mode-layout {
        grid-template-columns: 1fr;
    }
    .mode-grid {
        grid-template-columns: 1fr;
    }
}
</style>
