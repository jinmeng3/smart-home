<script setup lang="ts">
import { computed, onBeforeUnmount, reactive, ref, watch } from "vue";
import { ElMessage } from "element-plus";
import BaseSmartModal from "../common/BaseSmartModal.vue";
import SvgIcon from "../common/SvgIcon.vue";
import { devicePlatformOptions, deviceTypeIconMap, deviceTypeOptions } from "./deviceMeta";
import { uploadDeviceImage } from "../../api/device";
import type {
    Device,
    DeviceCreatePayload,
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

const platforms = devicePlatformOptions;
const form = reactive<DeviceCreatePayload>({
    name: "",
    room: "",
    type: "light",
    brand: "",
    connection: "Home Assistant",
    firmware: "1.0.0",
    imageUrl: "",
});
const imagePreviewUrl = ref("");
const imageFileName = ref("");
const pendingImageFile = ref<File | null>(null);

const selectedTypeMeta = computed(() =>
    deviceTypeOptions.find((item) => item.value === form.type),
);
const selectedTypeIcon = computed(() => deviceTypeIconMap[form.type]);
const canSubmit = computed(
    () =>
        Boolean(form.name.trim()) &&
        Boolean(form.room.trim()) &&
        Boolean(form.brand.trim()) &&
        !props.loading,
);

const releasePreviewUrl = () => {
    if (imagePreviewUrl.value.startsWith("blob:")) {
        URL.revokeObjectURL(imagePreviewUrl.value);
    }
};

const resetForm = () => {
    releasePreviewUrl();
    pendingImageFile.value = null;
    form.name = props.device?.name ?? "";
    form.room = props.device?.room ?? "";
    form.type = props.device?.type ?? "light";
    form.brand = props.device?.brand ?? "";
    form.connection = props.device?.connection ?? "Home Assistant";
    form.firmware = props.device?.firmware ?? "1.0.0";
    form.imageUrl = props.device?.image ?? "";
    imagePreviewUrl.value = props.device?.image ?? "";
    imageFileName.value = props.device?.image ? "已上传设备图片" : "";
};

const handleImageChange = (event: Event) => {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];

    if (!file) {
        return;
    }

    releasePreviewUrl();
    pendingImageFile.value = file;
    imagePreviewUrl.value = URL.createObjectURL(file);
    imageFileName.value = file.name;
};

const clearImage = () => {
    releasePreviewUrl();
    pendingImageFile.value = null;
    imagePreviewUrl.value = "";
    imageFileName.value = "";
    form.imageUrl = "";
};

const close = () => {
    if (props.loading) {
        return;
    }

    pendingImageFile.value = null;
    emit("update:modelValue", false);
};

const submit = async () => {
    if (!form.name.trim() || !form.room.trim() || !form.brand.trim()) {
        return;
    }

    if (pendingImageFile.value) {
        try {
            form.imageUrl = await uploadDeviceImage(pendingImageFile.value);
        } catch (error) {
            ElMessage.error(
                error instanceof Error ? error.message : "图片上传失败",
            );
            return;
        }
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

onBeforeUnmount(releasePreviewUrl);
</script>

<template>
    <BaseSmartModal
        :confirm-text="device ? '保存修改' : '添加设备'"
        :description="
            device ? '更新设备属性和接入信息' : '填写设备基础信息并接入家庭'
        "
        :loading="loading"
        :model-value="modelValue"
        :title="device ? '编辑设备' : '添加设备'"
        width="720px"
        @confirm="submit"
        @update:model-value="emit('update:modelValue', $event)"
    >
        <template #header>
            <header class="device-dialog-header">
                <span class="device-dialog-icon" aria-hidden="true">
                    <SvgIcon :name="selectedTypeIcon" />
                </span>
                <div>
                    <h2>{{ device ? "编辑设备" : "添加设备" }}</h2>
                    <p>
                        {{
                            device
                                ? "更新设备属性和接入信息"
                                : "填写设备信息并上传设备图片"
                        }}
                    </p>
                </div>
                <button
                    class="device-dialog-close"
                    :disabled="loading"
                    type="button"
                    aria-label="关闭"
                    @click="close"
                >
                    <SvgIcon name="close" />
                </button>
            </header>
        </template>

        <form class="device-form" @submit.prevent="submit">
            <section class="device-editor-hero">
                <div class="device-upload-preview">
                    <img v-if="imagePreviewUrl" :src="imagePreviewUrl" alt="" />
                    <SvgIcon v-else :name="selectedTypeIcon" size="lg" />
                </div>
                <div class="device-editor-summary">
                    <span>{{ device ? "正在编辑" : "新建设备" }}</span>
                    <strong>{{ form.name || "未命名设备" }}</strong>
                    <p>
                        {{ form.room || "未设置房间" }} ·
                        {{ selectedTypeMeta?.label ?? "设备" }}
                    </p>
                    <div class="device-upload-actions">
                        <label class="device-upload-button">
                            <SvgIcon name="plus" />
                            上传图片
                            <input
                                accept="image/png,image/jpeg,image/webp"
                                type="file"
                                @change="handleImageChange"
                            />
                        </label>
                        <button
                            class="device-clear-button"
                            :disabled="!imagePreviewUrl"
                            type="button"
                            @click="clearImage"
                        >
                            移除
                        </button>
                    </div>
                    <small>{{
                        imageFileName ||
                        "支持 PNG、JPG、WEBP，保存后关联设备图片"
                    }}</small>
                </div>
            </section>

            <section class="device-form-section">
                <header>
                    <h3>基础信息</h3>
                    <span>用于设备清单、筛选和详情展示</span>
                </header>
                <div class="device-type-picker">
                    <span class="device-type-label">设备类型 <em>*</em></span>
                    <div class="device-type-grid">
                        <button
                            v-for="item in deviceTypeOptions.filter(
                                (item) => item.value,
                            )"
                            :key="item.value"
                            :class="{ active: form.type === item.value }"
                            type="button"
                            @click="form.type = item.value as DeviceType"
                        >
                            <i>
                                <SvgIcon
                                    :name="
                                        deviceTypeIconMap[
                                            item.value as DeviceType
                                        ]
                                    "
                                />
                            </i>
                            <b>{{ item.label }}</b>
                        </button>
                    </div>
                </div>
                <div class="device-form-grid">
                    <label>
                        <span>设备名称 <em>*</em></span>
                        <input
                            v-model="form.name"
                            maxlength="80"
                            placeholder="例如：客厅主灯"
                        />
                    </label>
                    <label>
                        <span>所在房间 <em>*</em></span>
                        <input
                            v-model="form.room"
                            maxlength="80"
                            placeholder="例如：客厅"
                        />
                    </label>
                    <label>
                        <span>品牌 <em>*</em></span>
                        <input
                            v-model="form.brand"
                            maxlength="64"
                            placeholder="例如：Aqara"
                        />
                    </label>
                </div>
            </section>

            <section class="device-form-section">
                <header>
                    <h3>接入信息</h3>
                    <span>同步平台和固件版本会显示在设备详情中</span>
                </header>
                <div class="device-form-grid">
                    <label>
                        <span>接入平台</span>
                        <select v-model="form.connection">
                            <option
                                v-for="platform in platforms"
                                :key="platform"
                                :value="platform"
                            >
                                {{ platform }}
                            </option>
                        </select>
                    </label>
                    <label>
                        <span>固件版本</span>
                        <input
                            v-model="form.firmware"
                            maxlength="64"
                            placeholder="1.0.0"
                        />
                    </label>
                </div>
            </section>
        </form>

        <template #footer>
            <footer class="device-dialog-footer">
                <span>{{
                    form.imageUrl
                        ? "图片将在保存设备时关联"
                        : "未上传图片时使用设备类型 SVG 图标"
                }}</span>
                <div>
                    <button
                        class="device-cancel-button"
                        :disabled="loading"
                        type="button"
                        @click="close"
                    >
                        取消
                    </button>
                    <button
                        class="device-submit-button"
                        :disabled="!canSubmit"
                        type="button"
                        @click="submit"
                    >
                        <SvgIcon :name="loading ? 'refresh' : 'check-circle'" />
                        {{
                            loading
                                ? "保存中"
                                : device
                                  ? "保存修改"
                                  : "添加设备"
                        }}
                    </button>
                </div>
            </footer>
        </template>
    </BaseSmartModal>
</template>

<style scoped>
.device-dialog-header {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 18px 22px;
    border-bottom: 1px solid var(--color-border-subtle);
    background: linear-gradient(
        180deg,
        var(--color-card-bg),
        var(--color-page-bg)
    );
}

.device-dialog-icon {
    display: grid;
    width: 46px;
    height: 46px;
    flex: 0 0 46px;
    place-items: center;
    border-radius: 12px;
    color: var(--color-primary-700);
    background: var(--color-primary-50);
}

.device-dialog-header h2,
.device-dialog-header p {
    margin: 0;
}

.device-dialog-header h2 {
    color: var(--color-text-primary);
    font-size: 22px;
    font-weight: 800;
}

.device-dialog-header p {
    margin-top: 4px;
    color: var(--color-text-secondary);
    font-size: 14px;
}

.device-dialog-close {
    display: grid;
    width: 38px;
    height: 38px;
    margin-left: auto;
    place-items: center;
    border-radius: 999px;
    color: var(--color-text-tertiary);
    transition:
        transform 160ms var(--motion-ease),
        background-color 160ms var(--motion-ease),
        color 160ms var(--motion-ease);
}

.device-dialog-close:hover {
    background: var(--color-surface-hover);
    color: var(--color-text-primary);
    transform: translateY(-1px);
}

.device-form {
    display: grid;
    gap: 16px;
}

.device-editor-hero {
    display: grid;
    grid-template-columns: 128px minmax(0, 1fr);
    align-items: center;
    gap: 16px;
    border: 1px solid var(--color-border);
    border-radius: 12px;
    background: linear-gradient(
        135deg,
        var(--color-card-bg),
        var(--color-primary-50)
    );
    padding: 16px;
}

.device-upload-preview {
    display: grid;
    width: 128px;
    height: 112px;
    place-items: center;
    overflow: hidden;
    border: 1px dashed var(--color-border-strong);
    border-radius: 10px;
    background: var(--color-card-bg);
    color: var(--color-primary-600);
}

.device-upload-preview img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.device-editor-summary {
    display: grid;
    min-width: 0;
    gap: 5px;
}

.device-editor-summary > span {
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 900;
}

.device-editor-summary strong {
    overflow: hidden;
    color: var(--color-text-primary);
    font-size: 19px;
    font-weight: 900;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.device-editor-summary p,
.device-editor-summary small {
    margin: 0;
    overflow: hidden;
    color: var(--color-text-tertiary);
    font-size: 13px;
    font-weight: 700;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.device-editor-summary small {
    margin-top: 2px;
    color: var(--color-text-muted);
    font-size: 12px;
}

.device-upload-actions,
.device-dialog-footer,
.device-dialog-footer div {
    display: flex;
    align-items: center;
}

.device-upload-actions {
    margin-top: 8px;
    gap: 8px;
}

.device-form-section {
    display: grid;
    gap: 14px;
    border: 1px solid var(--color-border);
    border-radius: 12px;
    background: var(--color-card-bg);
    padding: 16px;
}

.device-form-section header {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 16px;
    border-bottom: 1px solid var(--color-border-subtle);
    padding-bottom: 12px;
}

.device-form-section h3 {
    margin: 0;
    color: var(--color-text-primary);
    font-size: 15px;
    font-weight: 900;
}

.device-form-section header span {
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 700;
    text-align: right;
}

.device-type-picker {
    display: grid;
    gap: 10px;
    margin-bottom: 14px;
}

.device-type-label {
    color: var(--color-text-secondary);
    font-size: 13px;
    font-weight: 800;
}

.device-type-label em {
    color: var(--color-danger);
    font-style: normal;
}

.device-type-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 8px;
}

.device-type-grid button {
    display: grid;
    place-items: center;
    gap: 6px;
    border: 1px solid var(--color-border-subtle);
    border-radius: 10px;
    background: var(--color-surface-subtle);
    padding: 10px 4px 8px;
    color: var(--color-text-secondary);
    font-size: 11px;
    font-weight: 800;
    transition: 160ms var(--motion-ease);
}

.device-type-grid button:hover {
    border-color: var(--color-primary-300);
    transform: translateY(-1px);
}

.device-type-grid button.active {
    border-color: var(--color-primary-600);
    background: linear-gradient(
        135deg,
        var(--color-primary-50),
        var(--color-primary-100)
    );
    color: var(--color-primary-700);
    box-shadow: 0 0 0 2px var(--color-focus-ring);
}

.device-type-grid i {
    font-style: normal;
}

.device-type-grid b {
    font-weight: 800;
}

.device-form-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 14px;
}

.device-form-grid label {
    display: grid;
    gap: 7px;
}

.device-form-grid span {
    color: var(--color-text-secondary);
    font-size: 13px;
    font-weight: 800;
}

.device-form-grid em {
    color: var(--color-danger);
    font-style: normal;
}

.device-form-grid input,
.device-form-grid select {
    width: 100%;
    height: 42px;
    border: 1px solid var(--color-border-default);
    border-radius: 9px;
    background: var(--color-panel-background);
    color: var(--color-text-primary);
    padding: 0 12px;
    outline: none;
    transition:
        border-color 160ms var(--motion-ease),
        box-shadow 160ms var(--motion-ease);
}

.device-form-grid select option {
    background: var(--color-panel-background);
    color: var(--color-text-primary);
}

.device-form-grid input:focus,
.device-form-grid select:focus {
    border-color: var(--color-primary-400);
    box-shadow: 0 0 0 3px var(--color-focus-ring);
}

.device-upload-button,
.device-clear-button,
.device-cancel-button,
.device-submit-button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 7px;
    height: 38px;
    border-radius: 9px;
    padding: 0 12px;
    font-size: 13px;
    font-weight: 900;
    transition:
        transform 160ms var(--motion-ease),
        background-color 160ms var(--motion-ease),
        border-color 160ms var(--motion-ease),
        box-shadow 160ms var(--motion-ease);
}

.device-upload-button {
    position: relative;
    overflow: hidden;
    border: 1px solid var(--color-primary-600);
    background: var(--color-primary-600);
    color: var(--color-text-on-primary);
    cursor: pointer;
}

.device-upload-button input {
    position: absolute;
    inset: 0;
    opacity: 0;
    cursor: pointer;
}

.device-clear-button,
.device-cancel-button {
    border: 1px solid var(--color-border);
    background: var(--color-card-bg);
    color: var(--color-text-secondary);
}

.device-submit-button {
    border: 1px solid var(--color-primary-600);
    background: var(--color-primary-600);
    color: var(--color-text-on-primary);
    box-shadow: 0 6px 16px var(--color-focus-ring);
}

.device-submit-button:disabled svg {
    animation: device-dialog-spin 900ms linear infinite;
}

.device-dialog-footer {
    justify-content: space-between;
    gap: 14px;
    padding: 14px 22px;
    border-top: 1px solid var(--color-border-subtle);
    background: var(--color-workspace-background);
}

.device-dialog-footer span {
    color: var(--color-text-tertiary);
    font-size: 13px;
    font-weight: 700;
}

.device-dialog-footer div {
    gap: 10px;
}

button:not(:disabled):hover,
.device-upload-button:hover {
    transform: translateY(-1px);
}

button:disabled {
    cursor: default;
    opacity: 0.55;
}

@keyframes device-dialog-spin {
    to {
        transform: rotate(360deg);
    }
}

@media (max-width: 640px) {
    .device-editor-hero,
    .device-form-grid {
        grid-template-columns: 1fr;
    }

    .device-type-grid {
        grid-template-columns: repeat(3, minmax(0, 1fr));
    }

    .device-upload-preview {
        width: 100%;
    }

    .device-dialog-footer {
        align-items: stretch;
        flex-direction: column;
    }

    .device-dialog-footer div {
        justify-content: flex-end;
    }

    .device-form-section header {
        display: grid;
    }

    .device-form-section header span {
        text-align: left;
    }
}

@media (prefers-reduced-motion: reduce) {
    button,
    .device-upload-button,
    .device-form-grid input,
    .device-form-grid select {
        transition-duration: 1ms;
    }

    button:not(:disabled):hover,
    .device-upload-button:hover {
        transform: none;
    }
}
</style>
