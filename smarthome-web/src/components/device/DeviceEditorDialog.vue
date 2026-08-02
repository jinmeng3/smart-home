<script setup lang="ts">
import { reactive, watch } from "vue";
import BaseModal from "../common/BaseModal.vue";
import { deviceTypeOptions } from "./deviceMeta";
import type {
    Device,
    DeviceCreatePayload,
    DevicePlatform,
    DeviceType,
} from "../../types/device";

const props = defineProps<{
    modelValue: boolean;
    device: Device | null;
    loading: boolean;
}>();

const emit = defineEmits<{
    "update:modelValue": [value: boolean];
    submit: [payload: DeviceCreatePayload];
}>();

const platforms: DevicePlatform[] = ["Home Assistant", "Matter", "Zigbee", "MQTT"];
const form = reactive<DeviceCreatePayload>({
    name: "",
    room: "",
    type: "light",
    brand: "",
    connection: "Home Assistant",
    firmware: "1.0.0",
    imageUrl: "",
});

const resetForm = () => {
    form.name = props.device?.name ?? "";
    form.room = props.device?.room ?? "";
    form.type = props.device?.type ?? "light";
    form.brand = props.device?.brand ?? "";
    form.connection = props.device?.connection ?? "Home Assistant";
    form.firmware = props.device?.firmware ?? "1.0.0";
    form.imageUrl = props.device?.image ?? "";
};

const submit = () => {
    if (!form.name.trim() || !form.room.trim() || !form.brand.trim()) {
        return;
    }

    emit("submit", {
        ...form,
        name: form.name.trim(),
        room: form.room.trim(),
        brand: form.brand.trim(),
        firmware: form.firmware?.trim() || "1.0.0",
        imageUrl: form.imageUrl?.trim() || undefined,
    });
};

watch(
    () => [props.modelValue, props.device] as const,
    ([open]) => {
        if (open) resetForm();
    },
    { immediate: true },
);
</script>

<template>
    <BaseModal
        :confirm-text="device ? '保存修改' : '添加设备'"
        :description="device ? '更新设备属性和接入信息' : '填写设备基础信息并接入家庭'"
        icon="⌁"
        :loading="loading"
        :model-value="modelValue"
        show-footer
        :title="device ? '编辑设备' : '添加设备'"
        width="560px"
        @confirm="submit"
        @update:model-value="emit('update:modelValue', $event)"
    >
        <form class="device-form" @submit.prevent="submit">
            <label>
                <span>设备名称</span>
                <input v-model="form.name" maxlength="80" placeholder="例如：客厅灯带" />
            </label>
            <label>
                <span>所在房间</span>
                <input v-model="form.room" maxlength="80" placeholder="例如：客厅" />
            </label>
            <label>
                <span>设备类型</span>
                <select v-model="form.type">
                    <option
                        v-for="item in deviceTypeOptions.filter((item) => item.value)"
                        :key="item.value"
                        :value="item.value as DeviceType"
                    >
                        {{ item.label }}
                    </option>
                </select>
            </label>
            <label>
                <span>品牌</span>
                <input v-model="form.brand" maxlength="64" placeholder="例如：Orion" />
            </label>
            <label>
                <span>接入平台</span>
                <select v-model="form.connection">
                    <option v-for="platform in platforms" :key="platform" :value="platform">
                        {{ platform }}
                    </option>
                </select>
            </label>
            <label>
                <span>固件版本</span>
                <input v-model="form.firmware" maxlength="64" placeholder="1.0.0" />
            </label>
            <label class="is-wide">
                <span>图片地址</span>
                <input v-model="form.imageUrl" maxlength="255" placeholder="/uploads/devices/example.png" />
            </label>
        </form>
    </BaseModal>
</template>

<style scoped>
.device-form {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
}

.device-form label {
    display: grid;
    gap: 7px;
}

.device-form label.is-wide {
    grid-column: 1 / -1;
}

.device-form span {
    color: var(--color-text-secondary);
    font-size: 13px;
    font-weight: 800;
}

.device-form input,
.device-form select {
    width: 100%;
    height: 40px;
    border: 1px solid var(--color-border-default);
    border-radius: 8px;
    background: var(--color-panel-background);
    color: var(--color-text-primary);
    padding: 0 12px;
    outline: none;
}

.device-form input:focus,
.device-form select:focus {
    border-color: var(--color-primary-400);
    box-shadow: 0 0 0 3px var(--color-focus-ring);
}
</style>
