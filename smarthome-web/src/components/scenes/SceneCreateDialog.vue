<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import { ElMessage } from "element-plus";
import BaseSmartModal from "../common/BaseSmartModal.vue";
import SvgIcon from "../common/SvgIcon.vue";
import { listDevices } from "../../api/device";
import { fetchRooms } from "../../api/room";
import { getDeviceTypeIcon } from "../device/deviceMeta";
import type { Device } from "../../types/device";
import type { Room } from "../../types/room";
import type { Scene, SceneInput, SceneTriggerType } from "../../types/scene";

interface ActionItem {
    id: string;
    icon: string;
    name: string;
    target: string;
}

const props = defineProps<{
    /** 编辑模式下传入待编辑场景；为空时进入创建模式。 */
    scene?: Scene | null;
}>();

const model = defineModel<boolean>({ required: true });

/** 是否处于编辑模式（传入待编辑场景时）。 */
const editing = computed(() => !!props.scene);

const emit = defineEmits<{
    create: [payload: SceneInput];
    update: [scene: Scene, payload: SceneInput];
    draft: [payload: SceneInput];
}>();

interface FormState {
    name: string;
    description: string;
    icon: string;
    color: string;
    triggerType: SceneTriggerType;
    triggerLabel: string;
    rooms: string[];
    enabled: boolean;
}

const defaultForm: FormState = {
    name: "",
    description: "",
    icon: "home",
    color: "var(--color-primary-600)",
    triggerType: "location",
    triggerLabel: "",
    rooms: [],
    enabled: true,
};

const form = reactive<FormState>({ ...defaultForm });

const defaultActions: ActionItem[] = [];

const actions = ref<ActionItem[]>(defaultActions.map((action) => ({ ...action })));
const availableRooms = ref<Room[]>([]);
const availableDevices = ref<Device[]>([]);
const optionsLoading = ref(false);
const roomPickerOpen = ref(false);
const devicePickerOpen = ref(false);

const visibleDevices = computed(() =>
    form.rooms.length
        ? availableDevices.value.filter((device) => form.rooms.includes(device.room))
        : availableDevices.value,
);

const loadAssociationOptions = async () => {
    optionsLoading.value = true;
    try {
        const [roomResult, deviceResult] = await Promise.all([
            fetchRooms(),
            listDevices({
                page: 1,
                pageSize: 100,
                keyword: "",
                type: "",
                status: "",
                room: "",
            }),
        ]);
        availableRooms.value = roomResult.items;
        availableDevices.value = deviceResult.items;
    } catch (error) {
        ElMessage.error(error instanceof Error ? error.message : "房间与设备加载失败");
    } finally {
        optionsLoading.value = false;
    }
};

const toggleRoom = (room: Room) => {
    form.rooms = form.rooms.includes(room.name)
        ? form.rooms.filter((name) => name !== room.name)
        : [...form.rooms, room.name];
};

const removeRoom = (roomName: string) => {
    form.rooms = form.rooms.filter((name) => name !== roomName);
};

const toggleDevice = (device: Device) => {
    const deviceId = device.deviceId ?? String(device.id);
    if (actions.value.some((action) => action.id === deviceId)) {
        actions.value = actions.value.filter((action) => action.id !== deviceId);
        return;
    }
    actions.value = [
        ...actions.value,
        {
            id: deviceId,
            icon: device.icon || getDeviceTypeIcon(device.type),
            name: device.name,
            target: `${device.room} · 执行设备动作`,
        },
    ];
};

const iconOptions = [
    { value: "home", label: "回家" },
    { value: "eye", label: "安防" },
    { value: "group", label: "聚会" },
    { value: "clock", label: "定时" },
    { value: "energy", label: "节能" },
    { value: "room", label: "房间" },
    { value: "automation", label: "联动" },
    { value: "light", label: "灯光" },
    { value: "moon", label: "睡眠" },
    { value: "sun", label: "白天" },
];

const colorOptions = [
    { value: "var(--color-primary-600)", label: "蓝色" },
    { value: "var(--color-success)", label: "绿色" },
    { value: "var(--color-warning)", label: "橙色" },
    { value: "var(--color-scene-sleep)", label: "紫色" },
    { value: "var(--color-danger)", label: "红色" },
    { value: "var(--color-teal-600)", label: "青色" },
    { value: "var(--color-pink-600)", label: "粉色" },
    { value: "var(--color-gray-600)", label: "灰色" },
];

// 根据步骤名称推断一个已存在图标名，保证编辑时动作列表可视化一致。
const deriveActionIcon = (name: string): string => {
    const map: Array<[RegExp, string]> = [
        [/灯|照明|亮度|光/i, "light"],
        [/空調|空调|温度|暖|制冷/i, "air-conditioner"],
        [/窗帘|遮阳/i, "curtain"],
        [/摄像|监控|镜头/i, "camera"],
        [/门锁|锁/i, "lock"],
        [/开关|插座|电源/i, "plug"],
        [/传感|传感器|感应|探测/i, "sensor"],
        [/安防|报警|安全/i, "security"],
        [/湿度|加湿|除湿/i, "humidity"],
        [/空气质量|新风|净化/i, "air-quality"],
        [/音乐|音响|播放/i, "motion"],
        [/模式|场景|联动|自动/i, "automation"],
        [/节能|能耗|省电/i, "energy"],
    ];
    const matched = map.find(([pattern]) => pattern.test(name));
    return matched ? matched[1] : "device-management";
};

const resetForm = () => {
    Object.assign(form, defaultForm);
    actions.value = defaultActions.map((action) => ({ ...action }));
};

const populateScene = (scene: Scene) => {
    form.name = scene.name;
    form.description = scene.description;
    form.icon = scene.icon;
    form.color = scene.color;
    form.triggerType = scene.triggerType;
    // 存储的 triggerLabel 已带触发方式前缀，编辑时还原为纯详情。
    form.triggerLabel =
        scene.triggerType === "location"
            ? scene.triggerLabel.replace(/^位置触发（/, "").replace(/）$/, "")
            : "";
    form.rooms = [...(scene.roomLabels ?? [])];
    form.enabled = scene.enabled;
    actions.value = scene.steps.map((step) => ({
        id: step.deviceId,
        icon: deriveActionIcon(step.name),
        name: step.name,
        target: step.description,
    }));
};

// 弹窗打开时按当前模式（创建 / 编辑）初始化表单。
watch(
    () => model.value,
    (open) => {
        if (!open) return;
        if (props.scene) populateScene(props.scene);
        else resetForm();
        roomPickerOpen.value = false;
        devicePickerOpen.value = false;
        void loadAssociationOptions();
    },
    { immediate: true },
);

const triggerLabel = computed(() => {
    if (form.triggerType === "location") return `位置触发（${form.triggerLabel}）`;
    if (form.triggerType === "schedule") return "定时触发";
    if (form.triggerType === "device") return "设备触发";
    return "手动执行";
});

const triggerIcon = computed(() => {
    if (form.triggerType === "schedule") return "calendar";
    if (form.triggerType === "location") return "home";
    if (form.triggerType === "device") return "device-management";
    return "automation";
});

const formValid = computed(() => form.name.trim().length > 0);

const payload = computed<SceneInput>(() => ({
    name: form.name.trim(),
    description: form.description.trim(),
    icon: form.icon,
    color: form.color,
    triggerType: form.triggerType,
    triggerLabel: triggerLabel.value,
    roomLabels: [...form.rooms],
    deviceIds: actions.value.map((action) => action.id),
    enabled: form.enabled,
    steps: actions.value.map((action, index) => ({
        name: action.name,
        description: action.target,
        deviceId: action.id,
        order: index + 1,
    })),
}));

const createScene = () => {
    if (!formValid.value) return;
    emit("create", payload.value);
    model.value = false;
};

const saveScene = () => {
    if (!formValid.value || !props.scene) return;
    emit("update", props.scene, payload.value);
    model.value = false;
};

const saveDraft = () => {
    emit("draft", payload.value);
};

const dialogTitle = computed(() => (editing.value ? "编辑场景" : "创建场景"));
const dialogDescription = computed(() =>
    editing.value
        ? "修改场景信息、触发条件与执行动作，保存后立即生效"
        : "配置场景信息、触发条件与执行动作，一键创建智能场景",
);
const dialogConfirmText = computed(() => (editing.value ? "保存修改" : "创建场景"));
const dialogFooterHint = computed(() =>
    editing.value
        ? "修改会覆盖原场景并立即生效，可在列表中继续调整。"
        : "场景创建后可在列表中找到并继续编辑。",
);
</script>

<template>
    <BaseSmartModal
        v-model="model"
        :title="dialogTitle"
        :description="dialogDescription"
        icon="home"
        width="960px"
        :confirm-text="dialogConfirmText"
        cancel-text="取消"
        draft-text="保存草稿"
        :show-draft="!editing"
        show-footer
        @confirm="editing ? saveScene() : createScene()"
        @save-draft="saveDraft"
    >
        <div class="create-dialog">
            <section class="create-form">
                <!-- 步骤进度条 -->
                <nav class="create-steps" aria-label="创建步骤">
                    <span class="active">
                        <b>1</b>
                        <span class="step-label">基本信息</span>
                    </span>
                    <span class="step-connector" />
                    <span class="active">
                        <b>2</b>
                        <span class="step-label">触发条件</span>
                    </span>
                    <span class="step-connector" />
                    <span class="active">
                        <b>3</b>
                        <span class="step-label">执行动作</span>
                    </span>
                    <span class="step-connector" />
                    <span class="active">
                        <b>4</b>
                        <span class="step-label">预览发布</span>
                    </span>
                </nav>

                <!-- 1. 基本信息 -->
                <section class="form-block">
                    <div class="form-block-header">
                        <span class="form-block-step">01</span>
                        <h3>基本信息</h3>
                    </div>
                    <div class="form-grid">
                        <label class="form-field">
                            <span class="field-label">场景名称 <em class="required">*</em></span>
                            <input
                                v-model="form.name"
                                maxlength="32"
                                placeholder="例如：回家模式、睡眠模式"
                                :class="{ 'has-value': form.name.trim().length > 0 }"
                            />
                            <span class="field-hint">{{ form.name.length }}/32</span>
                        </label>
                        <label class="form-field">
                            <span class="field-label">场景描述</span>
                            <textarea
                                v-model="form.description"
                                rows="2"
                                placeholder="简单描述场景的用途和效果"
                                :class="{ 'has-value': form.description.trim().length > 0 }"
                            />
                        </label>
                    </div>
                    <div class="option-row">
                        <span class="option-label">场景图标</span>
                        <div class="icon-picker">
                            <button
                                v-for="item in iconOptions"
                                :key="item.value"
                                :class="{ active: form.icon === item.value }"
                                type="button"
                                :title="item.label"
                                @click="form.icon = item.value"
                            >
                                <SvgIcon :name="item.value" />
                                <small>{{ item.label }}</small>
                            </button>
                        </div>
                    </div>
                    <div class="option-row">
                        <span class="option-label">场景主色</span>
                        <div class="color-picker">
                            <button
                                v-for="item in colorOptions"
                                :key="item.value"
                                :class="{ active: form.color === item.value }"
                                type="button"
                                :title="item.label"
                                :style="{ '--color-swatch': item.value }"
                                @click="form.color = item.value"
                            >
                                <span class="color-swatch" />
                                <small>{{ item.label }}</small>
                            </button>
                        </div>
                    </div>
                </section>

                <!-- 2. 触发条件 -->
                <section class="form-block">
                    <div class="form-block-header">
                        <span class="form-block-step">02</span>
                        <h3>触发条件</h3>
                    </div>
                    <div class="trigger-tabs">
                        <button
                            :class="{ active: form.triggerType === 'manual' }"
                            type="button"
                            @click="form.triggerType = 'manual'"
                        >
                            <SvgIcon name="automation" />
                            <span class="trigger-label">手动执行</span>
                            <span class="trigger-desc">点击运行</span>
                        </button>
                        <button
                            :class="{ active: form.triggerType === 'schedule' }"
                            type="button"
                            @click="form.triggerType = 'schedule'"
                        >
                            <SvgIcon name="calendar" />
                            <span class="trigger-label">定时触发</span>
                            <span class="trigger-desc">指定时间自动运行</span>
                        </button>
                        <button
                            :class="{ active: form.triggerType === 'location' }"
                            type="button"
                            @click="form.triggerType = 'location'"
                        >
                            <SvgIcon name="home" />
                            <span class="trigger-label">位置触发</span>
                            <span class="trigger-desc">到达或离开时</span>
                        </button>
                        <button
                            :class="{ active: form.triggerType === 'device' }"
                            type="button"
                            @click="form.triggerType = 'device'"
                        >
                            <SvgIcon name="device-management" />
                            <span class="trigger-label">设备触发</span>
                            <span class="trigger-desc">设备状态变化时</span>
                        </button>
                    </div>
                    <label class="form-field inline-field">
                        <span class="field-label">触发条件详情</span>
                        <input v-model="form.triggerLabel" placeholder="例如：到达“家”半径 100m" />
                    </label>
                </section>

                <!-- 3. 关联房间与设备 -->
                <section class="form-block">
                    <div class="form-block-header">
                        <span class="form-block-step">03</span>
                        <h3>关联房间与设备</h3>
                    </div>
                    <div class="room-device-row">
                        <label class="form-field">
                            <span class="field-label">关联房间</span>
                            <div class="chips">
                                <em v-for="room in form.rooms" :key="room">
                                    {{ room }}
                                    <button type="button" class="chip-remove" title="移除" @click="removeRoom(room)">×</button>
                                </em>
                                <button type="button" class="chip-add" @click="roomPickerOpen = !roomPickerOpen">+ 添加房间</button>
                            </div>
                            <div v-if="roomPickerOpen" class="association-picker">
                                <span v-if="optionsLoading" class="picker-empty">正在加载房间...</span>
                                <span v-else-if="availableRooms.length === 0" class="picker-empty">暂无可关联房间</span>
                                <button
                                    v-for="room in availableRooms"
                                    v-else
                                    :key="room.id"
                                    type="button"
                                    :class="{ active: form.rooms.includes(room.name) }"
                                    @click="toggleRoom(room)"
                                >
                                    <SvgIcon name="room" size="sm" />
                                    <span>{{ room.name }}</span>
                                    <small>{{ room.deviceCount }} 个设备</small>
                                </button>
                            </div>
                        </label>
                        <label class="form-field">
                            <span class="field-label">关联设备</span>
                            <button class="select-device" type="button" @click="devicePickerOpen = !devicePickerOpen">
                                <span class="device-count">
                                    <SvgIcon name="device-management" size="sm" />
                                    共 {{ actions.length }} 个设备
                                </span>
                                <SvgIcon name="chevron-right" size="sm" />
                            </button>
                            <div v-if="devicePickerOpen" class="association-picker device-picker">
                                <span v-if="optionsLoading" class="picker-empty">正在加载设备...</span>
                                <span v-else-if="visibleDevices.length === 0" class="picker-empty">当前房间暂无设备</span>
                                <button
                                    v-for="device in visibleDevices"
                                    v-else
                                    :key="device.id"
                                    type="button"
                                    :class="{ active: actions.some((action) => action.id === (device.deviceId ?? String(device.id))) }"
                                    @click="toggleDevice(device)"
                                >
                                    <SvgIcon :name="device.icon || getDeviceTypeIcon(device.type)" size="sm" />
                                    <span>{{ device.name }}</span>
                                    <small>{{ device.room }}</small>
                                </button>
                            </div>
                        </label>
                    </div>
                </section>

                <!-- 4. 执行动作 -->
                <section class="form-block">
                    <div class="form-block-header">
                        <span class="form-block-step">04</span>
                        <h3>执行动作</h3>
                        <span class="form-block-badge">共 {{ actions.length }} 步</span>
                    </div>
                    <ol class="action-list">
                        <li v-for="(action, index) in actions" :key="action.id">
                            <span class="action-order">{{ index + 1 }}</span>
                            <span class="action-icon">
                                <SvgIcon :name="action.icon" />
                            </span>
                            <div class="action-info">
                                <strong>{{ action.name }}</strong>
                                <small>{{ action.target }}</small>
                            </div>
                            <button type="button" class="action-more" title="移除动作" @click="actions = actions.filter((item) => item.id !== action.id)">
                                ×
                            </button>
                        </li>
                    </ol>
                    <button class="add-action" type="button" @click="devicePickerOpen = true">
                        <SvgIcon name="plus" size="sm" />
                        添加执行动作
                    </button>
                </section>
            </section>

            <aside class="create-preview">
                <div class="preview-header">
                    <SvgIcon name="eye" size="sm" />
                    <span>场景预览</span>
                </div>
                <article class="preview-card">
                    <div class="preview-card-icon" :style="{ background: form.color }">
                        <SvgIcon :name="form.icon" />
                    </div>
                    <div class="preview-card-body">
                        <strong>{{ form.name || "场景名称" }}</strong>
                        <p>{{ form.description || "场景描述" }}</p>
                    </div>
                    <span class="preview-card-badge" :style="{ background: form.color + '20', color: form.color }">
                        {{ form.triggerType === "manual" ? "手动" : "自动" }}
                    </span>
                </article>
                <div class="preview-details">
                    <div class="preview-detail-item">
                        <dt>
                            <SvgIcon name="room" size="sm" />
                            关联房间
                        </dt>
                        <dd>{{ form.rooms.length > 0 ? form.rooms.join("、") : "未设置" }}</dd>
                    </div>
                    <div class="preview-detail-item">
                        <dt>
                            <SvgIcon name="device-management" size="sm" />
                            关联设备
                        </dt>
                        <dd>{{ actions.length }} 个</dd>
                    </div>
                    <div class="preview-detail-item">
                        <dt>
                            <SvgIcon :name="triggerIcon" size="sm" />
                            触发方式
                        </dt>
                        <dd>{{ triggerLabel }}</dd>
                    </div>
                </div>
                <div class="preview-steps">
                    <h4>执行流程（{{ actions.length }} 步）</h4>
                    <ol>
                        <li v-for="(action, index) in actions" :key="action.id" class="preview-step-item">
                            <span class="step-index">{{ index + 1 }}</span>
                            <SvgIcon :name="action.icon" size="sm" />
                            <div class="step-info">
                                <strong>{{ action.name }}</strong>
                                <small>{{ action.target }}</small>
                            </div>
                        </li>
                    </ol>
                </div>
                <p class="preview-note">
                    <SvgIcon name="info" size="sm" />
                    预计影响 {{ actions.length }} 个设备
                </p>
            </aside>
        </div>
        <template #footerHint>
            {{ dialogFooterHint }}
        </template>
    </BaseSmartModal>
</template>

<style scoped>
/* ── 布局 ── */
.create-dialog {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 320px;
    gap: 20px;
    align-items: start;
}

.create-form {
    display: grid;
    min-width: 0;
    gap: 14px;
}

.create-preview {
    position: sticky;
    top: 0;
    display: grid;
    min-width: 0;
    gap: 14px;
}

/* ── 步骤进度条 ── */
.create-steps {
    display: flex;
    align-items: center;
    gap: 0;
    padding: 4px 0;
}

.create-steps > span:not(.step-connector) {
    display: flex;
    align-items: center;
    gap: 6px;
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 800;
    white-space: nowrap;
}

.create-steps b {
    display: grid;
    width: 22px;
    height: 22px;
    flex-shrink: 0;
    place-items: center;
    border-radius: 999px;
    background: var(--color-surface-subtle);
    font-size: 11px;
    transition: background 200ms, color 200ms;
}

.create-steps .active b {
    background: var(--color-primary-600);
    color: var(--color-text-on-primary);
}

.create-steps .active .step-label {
    color: var(--color-text-primary);
}

.step-connector {
    flex: 1;
    height: 2px;
    margin: 0 8px;
    border-radius: 2px;
    background: var(--color-border);
    min-width: 16px;
}

.create-steps .active + .step-connector {
    background: var(--color-primary-300);
}

/* ── 表单区块 ── */
.form-block {
    border: 1px solid var(--color-border);
    border-radius: 12px;
    background: var(--color-card-bg);
    padding: 16px;
    transition: border-color 200ms;
}

.form-block:focus-within {
    border-color: var(--color-primary-300);
}

.form-block-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 14px;
}

.form-block-step {
    display: grid;
    width: 28px;
    height: 28px;
    place-items: center;
    border-radius: 8px;
    background: var(--color-primary-50);
    color: var(--color-primary-600);
    font-size: 12px;
    font-weight: 900;
}

.form-block-header h3 {
    margin: 0;
    flex: 1;
    color: var(--color-text-primary);
    font-size: 15px;
    font-weight: 900;
}

.form-block-badge {
    border-radius: 999px;
    background: var(--color-surface-subtle);
    padding: 3px 10px;
    color: var(--color-text-secondary);
    font-size: 11px;
    font-weight: 800;
}

/* ── 表单字段 ── */
.form-grid,
.room-device-row {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 14px;
}

.room-device-row {
    align-items: start;
}

.room-device-row .form-field {
    min-width: 0;
    align-content: start;
}

.form-field {
    display: grid;
    gap: 6px;
}

.field-label {
    color: var(--color-text-secondary);
    font-size: 12px;
    font-weight: 800;
}

.field-label .required {
    color: var(--color-danger);
    font-style: normal;
}

.field-hint {
    justify-self: end;
    color: var(--color-text-tertiary);
    font-size: 11px;
    font-weight: 700;
    margin-top: -2px;
}

input,
textarea {
    width: 100%;
    border: 1px solid var(--color-border);
    border-radius: 8px;
    background: var(--color-input-bg);
    padding: 9px 12px;
    color: var(--color-text-primary);
    font: inherit;
    font-size: 13px;
    outline: 0;
    transition: border-color 200ms, box-shadow 200ms;
    box-sizing: border-box;
}

input:focus,
textarea:focus {
    border-color: var(--color-primary-500);
    box-shadow: 0 0 0 3px var(--color-focus-ring);
}

input.has-value,
textarea.has-value {
    border-color: var(--color-primary-200);
}

textarea {
    resize: vertical;
    min-height: 56px;
}

/* ── 图标选择器 ── */
.option-row {
    display: flex;
    gap: 12px;
    margin-top: 14px;
    align-items: flex-start;
}

.option-label {
    width: 72px;
    flex-shrink: 0;
    padding-top: 6px;
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 800;
}

.icon-picker {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    flex: 1;
}

.icon-picker button {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    width: 52px;
    padding: 6px 0 4px;
    border: 1px solid var(--color-border);
    border-radius: 8px;
    background: var(--color-card-bg);
    color: var(--color-text-secondary);
    cursor: pointer;
    transition: all 160ms;
}

.icon-picker button:hover {
    border-color: var(--color-primary-300);
    background: var(--color-primary-50);
    color: var(--color-primary-600);
}

.icon-picker button.active {
    border-color: var(--color-primary-500);
    background: var(--color-primary-50);
    color: var(--color-primary-700);
    box-shadow: 0 0 0 2px var(--color-focus-ring);
}

.icon-picker button small {
    font-size: 10px;
    font-weight: 700;
    line-height: 1;
}

/* ── 颜色选择器 ── */
.color-picker {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    flex: 1;
}

.color-picker button {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 5px 10px 5px 6px;
    border: 1px solid var(--color-border);
    border-radius: 8px;
    background: var(--color-card-bg);
    cursor: pointer;
    transition: all 160ms;
}

.color-picker button:hover {
    border-color: var(--color-text-secondary);
}

.color-picker button.active {
    border-color: var(--color-primary-500);
    box-shadow: 0 0 0 2px var(--color-focus-ring);
}

.color-swatch {
    display: block;
    width: 16px;
    height: 16px;
    border-radius: 999px;
    background: var(--color-swatch);
    flex-shrink: 0;
}

.color-picker button small {
    font-size: 11px;
    font-weight: 800;
    color: var(--color-text-secondary);
}

.color-picker button.active small {
    color: var(--color-text-primary);
}

/* ── 触发条件选项卡 ── */
.trigger-tabs {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 8px;
    margin-bottom: 12px;
}

.trigger-tabs button {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    padding: 12px 8px;
    border: 1px solid var(--color-border);
    border-radius: 10px;
    background: var(--color-card-bg);
    color: var(--color-text-secondary);
    cursor: pointer;
    transition: all 180ms;
}

.trigger-tabs button:hover {
    border-color: var(--color-primary-300);
    background: var(--color-primary-50);
}

.trigger-tabs button.active {
    border-color: var(--color-primary-500);
    background: var(--color-primary-50);
    color: var(--color-primary-700);
    box-shadow: 0 0 0 2px var(--color-focus-ring);
}

.trigger-tabs button svg {
    color: var(--color-text-tertiary);
    transition: color 180ms;
}

.trigger-tabs button.active svg {
    color: var(--color-primary-600);
}

.trigger-label {
    font-size: 13px;
    font-weight: 900;
}

.trigger-desc {
    font-size: 11px;
    font-weight: 700;
    color: var(--color-text-tertiary);
    opacity: 0;
    max-height: 0;
    transition: opacity 200ms, max-height 200ms;
    overflow: hidden;
}

.trigger-tabs button:hover .trigger-desc,
.trigger-tabs button.active .trigger-desc {
    opacity: 1;
    max-height: 20px;
}

.inline-field {
    max-width: 100%;
}

/* ── 房间标签 ── */
.chips {
    display: flex;
    width: 100%;
    box-sizing: border-box;
    flex-wrap: wrap;
    gap: 6px;
    min-height: 36px;
    align-items: center;
    border: 1px solid var(--color-border);
    border-radius: 8px;
    background: var(--color-input-bg);
    padding: 5px 8px;
}

.chips em {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    border-radius: 6px;
    background: var(--color-primary-50);
    padding: 4px 8px;
    color: var(--color-primary-700);
    font-size: 12px;
    font-style: normal;
    font-weight: 800;
}

.chip-remove {
    display: inline-flex;
    width: 14px;
    height: 14px;
    align-items: center;
    justify-content: center;
    border-radius: 999px;
    background: transparent;
    color: var(--color-primary-500);
    font-size: 13px;
    line-height: 1;
    padding: 0;
    cursor: pointer;
    transition: background 150ms;
}

.chip-remove:hover {
    background: var(--color-primary-100);
}

.chip-add {
    border: 1px dashed var(--color-primary-300);
    border-radius: 6px;
    background: transparent;
    padding: 4px 8px;
    color: var(--color-primary-600);
    font-size: 12px;
    font-weight: 800;
    cursor: pointer;
    transition: background 150ms;
}

.chip-add:hover {
    background: var(--color-primary-50);
}

.select-device {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    height: 36px;
    padding: 0 12px;
    border: 1px solid var(--color-border);
    border-radius: 8px;
    background: var(--color-input-bg);
    color: var(--color-text-primary);
    font-size: 13px;
    font-weight: 800;
    cursor: pointer;
    transition: border-color 200ms;
}

.select-device:hover {
    border-color: var(--color-primary-400);
}

.device-count {
    display: flex;
    align-items: center;
    gap: 6px;
    color: var(--color-text-secondary);
}

.association-picker {
    display: grid;
    width: 100%;
    box-sizing: border-box;
    max-height: 180px;
    gap: 5px;
    overflow-y: auto;
    border: 1px solid var(--color-border);
    border-radius: 9px;
    background: var(--color-card-bg);
    padding: 6px;
    box-shadow: var(--shadow-card);
}

.association-picker button {
    display: grid;
    grid-template-columns: 18px minmax(0, 1fr) auto;
    align-items: center;
    gap: 7px;
    min-width: 0;
    border-radius: 7px;
    padding: 7px 8px;
    color: var(--color-text-secondary);
    text-align: left;
    transition: background 160ms var(--motion-ease), color 160ms var(--motion-ease), box-shadow 160ms var(--motion-ease);
}

.association-picker button:hover,
.association-picker button.active {
    background: var(--color-primary-50);
    color: var(--color-primary-700);
}

.association-picker button.active {
    box-shadow: inset 0 0 0 1px var(--color-primary-200);
}

.association-picker button span {
    min-width: 0;
    overflow: hidden;
    font-size: 12px;
    font-weight: 800;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.association-picker button small,
.picker-empty {
    color: var(--color-text-tertiary);
    font-size: 11px;
    font-weight: 700;
}

.picker-empty {
    padding: 12px;
    text-align: center;
}

/* ── 执行动作列表 ── */
.action-list {
    display: grid;
    gap: 6px;
    padding: 0;
    margin: 0;
    list-style: none;
}

.action-list li {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 10px;
    border-radius: 8px;
    background: var(--color-surface-subtle);
    transition: background 150ms, transform 150ms;
}

.action-list li:hover {
    background: var(--color-primary-50);
}

.action-order {
    display: grid;
    width: 22px;
    height: 22px;
    flex-shrink: 0;
    place-items: center;
    border-radius: 999px;
    background: var(--color-card-bg);
    color: var(--color-primary-600);
    font-size: 11px;
    font-weight: 900;
}

.action-icon {
    display: grid;
    width: 28px;
    height: 28px;
    flex-shrink: 0;
    place-items: center;
    border-radius: 8px;
    background: var(--color-card-bg);
    color: var(--color-text-secondary);
}

.action-info {
    min-width: 0;
    flex: 1;
}

.action-info strong {
    display: block;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 13px;
    font-weight: 900;
    color: var(--color-text-primary);
}

.action-info small {
    display: block;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 12px;
    color: var(--color-text-tertiary);
    font-weight: 700;
    margin-top: 1px;
}

.action-more {
    display: grid;
    width: 28px;
    height: 28px;
    flex-shrink: 0;
    place-items: center;
    border-radius: 6px;
    color: var(--color-text-tertiary);
    cursor: pointer;
    transition: background 150ms, color 150ms;
}

.action-more:hover {
    background: var(--color-card-bg);
    color: var(--color-text-primary);
}

.add-action {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    width: 100%;
    height: 38px;
    margin-top: 8px;
    border: 1px dashed var(--color-primary-300);
    border-radius: 8px;
    background: transparent;
    color: var(--color-primary-600);
    font-size: 13px;
    font-weight: 900;
    cursor: pointer;
    transition: background 150ms, border-color 150ms;
}

.add-action:hover {
    background: var(--color-primary-50);
    border-color: var(--color-primary-500);
}

/* ── 预览面板 ── */
.preview-header {
    display: flex;
    align-items: center;
    gap: 6px;
    color: var(--color-text-secondary);
    font-size: 13px;
    font-weight: 900;
}

.preview-card {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px;
    border: 1px solid var(--color-border);
    border-radius: 12px;
    background: var(--color-card-bg);
    transition: border-color 200ms;
}

.preview-card-icon {
    display: grid;
    width: 44px;
    height: 44px;
    flex-shrink: 0;
    place-items: center;
    border-radius: 999px;
    color: #fff;
    transition: background 200ms;
}

.preview-card-body {
    min-width: 0;
    flex: 1;
}

.preview-card-body strong {
    display: block;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 15px;
    font-weight: 900;
    color: var(--color-text-primary);
}

.preview-card-body p {
    display: block;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 12px;
    color: var(--color-text-tertiary);
    font-weight: 700;
    margin-top: 2px;
}

.preview-card-badge {
    flex-shrink: 0;
    border-radius: 999px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 900;
}

.preview-details {
    display: grid;
    gap: 8px;
    padding: 12px 14px;
    border: 1px solid var(--color-border);
    border-radius: 10px;
    background: var(--color-card-bg);
}

.preview-detail-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
}

.preview-detail-item dt {
    display: flex;
    align-items: center;
    gap: 6px;
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 800;
}

.preview-detail-item dd {
    margin: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: var(--color-text-primary);
    font-size: 12px;
    font-weight: 900;
}

.preview-steps {
    padding: 12px 14px;
    border: 1px solid var(--color-border);
    border-radius: 10px;
    background: var(--color-card-bg);
}

.preview-steps h4 {
    margin: 0 0 10px;
    font-size: 13px;
    font-weight: 900;
    color: var(--color-text-primary);
}

.preview-steps ol {
    display: grid;
    gap: 6px;
    padding: 0;
    margin: 0;
    list-style: none;
}

.preview-step-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px;
    border-radius: 8px;
    background: var(--color-surface-subtle);
    transition: background 150ms;
}

.preview-step-item:hover {
    background: var(--color-primary-50);
}

.step-index {
    display: grid;
    width: 20px;
    height: 20px;
    flex-shrink: 0;
    place-items: center;
    border-radius: 999px;
    background: var(--color-card-bg);
    color: var(--color-primary-600);
    font-size: 10px;
    font-weight: 900;
}

.preview-step-item svg {
    flex-shrink: 0;
    color: var(--color-text-secondary);
}

.step-info {
    min-width: 0;
    flex: 1;
}

.step-info strong {
    display: block;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 12px;
    font-weight: 900;
    color: var(--color-text-primary);
}

.step-info small {
    display: block;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 11px;
    color: var(--color-text-tertiary);
    font-weight: 700;
    margin-top: 1px;
}

.preview-note {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 10px 14px;
    border-radius: 8px;
    background: var(--color-primary-50);
    color: var(--color-primary-600);
    font-size: 12px;
    font-weight: 800;
    margin: 0;
}

/* ── 响应式 ── */
@media (max-width: 980px) {
    .create-dialog {
        grid-template-columns: 1fr;
    }

    .create-preview {
        position: static;
    }
}

@media (max-width: 680px) {
    .create-steps .step-label {
        display: none;
    }

    .form-grid,
    .room-device-row {
        grid-template-columns: 1fr;
    }

    .trigger-tabs {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}
</style>
