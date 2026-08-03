<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import BaseSmartModal from "../common/BaseSmartModal.vue";
import SvgIcon from "../common/SvgIcon.vue";

export type AutomationDialog =
    "create" | "edit" | "import" | "logs" | "schedule" | "batch" | null;

interface Rule {
    id: number;
    name: string;
    description: string;
    trigger: string;
    devices: number;
    icon: string;
    tone: string;
    enabled: boolean;
}

const props = defineProps<{
    modelValue: AutomationDialog;
    rule?: Rule;
    rules: Rule[];
}>();

const emit = defineEmits<{
    "update:modelValue": [value: AutomationDialog];
    save: [
        payload: {
            mode: "create" | "edit";
            name: string;
            description: string;
            trigger: string;
        },
    ];
    batch: [ids: number[]];
    imported: [count: number];
    scheduled: [
        payload: { weekdays: number[]; time: string; ruleIds: number[] },
    ];
}>();

const form = reactive({
    name: "",
    description: "",
    trigger: "设备状态变化",
    triggerDevice: "门磁传感器",
    triggerState: "打开",
    rooms: ["玄关", "客厅", "餐厅"] as string[],
    devices: ["玄关灯", "客厅灯带", "空调"] as string[],
    delay: 0,
    priority: "中（默认）",
    repeat: "不限制",
    note: "",
});
const imported = ref(false);
const preserveIds = ref(true);
const smartMerge = ref(false);
const conflictMode = ref("跳过冲突规则");
const batchQuery = ref("");
const batchTab = ref("全部");
const selectedIds = ref<number[]>([]);
const weekdays = ref([1, 2, 3, 4, 5]);
const scheduleTime = ref("07:30");
const scheduleRuleIds = ref<number[]>([2, 3]);
const expandedLog = ref(1);

const isForm = computed(
    () => props.modelValue === "create" || props.modelValue === "edit",
);
const dialogTitle = computed(() =>
    props.modelValue === "edit" ? "编辑规则" : "创建自动化",
);
const filteredRules = computed(() =>
    props.rules.filter((rule) => {
        const matchesQuery = rule.name.includes(batchQuery.value);
        const matchesTab =
            batchTab.value === "全部" ||
            (batchTab.value === "已启用" && rule.enabled) ||
            (batchTab.value === "未启用" && !rule.enabled);
        return matchesQuery && matchesTab;
    }),
);
const logs = [
    {
        id: 1,
        time: "2026-08-08 10:15:23",
        name: "回家联动",
        source: "位置触发",
        result: "成功",
        duration: "2.4s",
    },
    {
        id: 2,
        time: "2026-08-08 07:00:11",
        name: "晨间唤醒联动",
        source: "定时触发",
        result: "成功",
        duration: "3.1s",
    },
    {
        id: 3,
        time: "2026-08-07 23:00:05",
        name: "夜间回家照明",
        source: "手动触发",
        result: "成功",
        duration: "1.8s",
    },
    {
        id: 4,
        time: "2026-08-07 19:42:12",
        name: "离家安防联动",
        source: "位置触发",
        result: "失败",
        duration: "0.9s",
    },
];

watch(
    () => props.modelValue,
    (value) => {
        if (!value) return;
        imported.value = false;
        if (value === "edit" && props.rule) {
            form.name = props.rule.name;
            form.description = props.rule.description;
            form.trigger = props.rule.trigger;
        } else if (value === "create") {
            form.name = "";
            form.description = "";
            form.trigger = "设备状态变化";
        }
        if (value === "batch")
            selectedIds.value = props.rules
                .filter((rule) => !rule.enabled)
                .map((rule) => rule.id);
    },
    { immediate: true },
);

const close = () => emit("update:modelValue", null);
const toggleValue = <T,>(items: T[], value: T) => {
    const index = items.indexOf(value);
    if (index >= 0) items.splice(index, 1);
    else items.push(value);
};
const submitForm = () => {
    if (!form.name.trim()) return;
    emit("save", {
        mode: props.modelValue === "edit" ? "edit" : "create",
        name: form.name.trim(),
        description:
            form.description.trim() ||
            `${form.trigger} · ${form.triggerDevice}${form.triggerState}`,
        trigger: form.trigger,
    });
    close();
};
const confirm = () => {
    if (isForm.value) return submitForm();
    if (props.modelValue === "import") {
        if (!imported.value) return;
        emit("imported", 4);
    }
    if (props.modelValue === "batch") emit("batch", selectedIds.value);
    if (props.modelValue === "schedule")
        emit("scheduled", {
            weekdays: weekdays.value,
            time: scheduleTime.value,
            ruleIds: scheduleRuleIds.value,
        });
    close();
};
</script>

<template>
    <BaseSmartModal
        v-if="isForm"
        :model-value="Boolean(modelValue)"
        :title="dialogTitle"
        :icon="modelValue === 'edit' ? 'edit' : 'automation'"
        description="设置触发条件和执行动作，让设备在合适的时机自动响应"
        width="980px"
        :confirm-text="modelValue === 'edit' ? '保存修改' : '创建'"
        @update:model-value="close"
        @confirm="confirm"
    >
        <div class="form-grid">
            <div class="form-column">
                <section>
                    <h3><SvgIcon name="info" />1. 基本信息</h3>
                    <label
                        >自动化名称 <b>*</b
                        ><input
                            v-model="form.name"
                            maxlength="30"
                            placeholder="例如：回家自动开灯"
                        /><small>{{ form.name.length }}/30</small></label
                    ><label
                        >描述（可选）<textarea
                            v-model="form.description"
                            maxlength="100"
                            placeholder="补充说明该自动化的用途与效果"
                        ></textarea
                        ><small>{{ form.description.length }}/100</small></label
                    >
                </section>
                <section>
                    <h3><SvgIcon name="sensor" />2. 触发条件</h3>
                    <label
                        >触发类型 <b>*</b
                        ><select v-model="form.trigger">
                            <option>设备状态变化</option>
                            <option>位置触发</option>
                            <option>时间触发</option>
                            <option>手动触发</option>
                        </select></label
                    >
                    <div class="inline">
                        <select v-model="form.triggerDevice">
                            <option>门磁传感器</option>
                            <option>人体传感器</option>
                            <option>温度传感器</option></select
                        ><select>
                            <option>状态变为</option></select
                        ><select v-model="form.triggerState">
                            <option>打开</option>
                            <option>关闭</option>
                        </select>
                    </div>
                    <button class="outline" type="button">＋ 添加条件</button
                    ><label
                        >生效时间段<select>
                            <option>全天有效</option>
                            <option>自定义时间</option>
                        </select></label
                    >
                </section>
                <section>
                    <h3><SvgIcon name="location" />3. 关联范围</h3>
                    <p class="label">关联房间</p>
                    <div class="chips">
                        <button
                            v-for="room in [
                                '玄关',
                                '客厅',
                                '餐厅',
                                '主卧',
                                '次卧',
                            ]"
                            :key="room"
                            :class="{ active: form.rooms.includes(room) }"
                            type="button"
                            @click="toggleValue(form.rooms, room)"
                        >
                            {{ room }}</button
                        ><button type="button">＋ 选择房间</button>
                    </div>
                    <p class="label">关联设备（可选）</p>
                    <div class="chips">
                        <button
                            v-for="device in ['玄关灯', '客厅灯带', '空调']"
                            :key="device"
                            class="active"
                            type="button"
                        >
                            {{ device }}⌄</button
                        ><button type="button">＋ 选择设备</button>
                    </div>
                </section>
            </div>
            <div class="form-column">
                <section>
                    <h3><SvgIcon name="automation" />4. 执行动作</h3>
                    <div
                        v-for="(device, index) in form.devices"
                        :key="device"
                        class="action-row"
                    >
                        <i>{{ index + 1 }}</i
                        ><SvgIcon
                            :name="index === 2 ? 'air-conditioner' : 'light'"
                        /><span
                            ><b>{{ device }}</b
                            ><small>{{
                                index === 2
                                    ? "开启｜制冷｜温度：26°C"
                                    : "开灯｜亮度 80%｜色温 4000K"
                            }}</small></span
                        ><button
                            type="button"
                            @click="form.devices.splice(index, 1)"
                        >
                            ×
                        </button>
                    </div>
                    <button
                        class="outline"
                        type="button"
                        @click="form.devices.push('智能设备')"
                    >
                        ＋ 添加动作</button
                    ><label
                        >执行延迟（可选）
                        <div class="suffix">
                            <input
                                v-model.number="form.delay"
                                type="number"
                                min="0"
                            /><span>秒</span>
                        </div></label
                    >
                </section>
                <section>
                    <h3><SvgIcon name="settings" />5. 高级设置</h3>
                    <label
                        >优先级<select v-model="form.priority">
                            <option>中（默认）</option>
                            <option>高</option>
                            <option>低</option>
                        </select></label
                    ><label
                        >重复触发间隔<select v-model="form.repeat">
                            <option>不限制</option>
                            <option>5 分钟</option>
                            <option>30 分钟</option>
                        </select></label
                    ><label
                        >备注（可选）<textarea
                            v-model="form.note"
                            maxlength="100"
                            placeholder="可填写更多备注信息"
                        ></textarea>
                    </label>
                </section>
            </div>
        </div>
    </BaseSmartModal>

    <BaseSmartModal
        v-else-if="modelValue === 'import'"
        :model-value="true"
        icon="upload"
        title="导入规则"
        description="从文件中导入自动化规则，快速复用或分享你的智能场景配置"
        width="760px"
        confirm-text="开始导入"
        @update:model-value="close"
        @confirm="confirm"
    >
        <button class="upload" type="button" @click="imported = true">
            <SvgIcon name="upload" size="lg" /><b>{{
                imported ? "automation-rules.yaml" : "点击上传或拖拽文件到此处"
            }}</b
            ><span>支持 JSON、YAML、模板包格式，单个文件最大 10MB</span>
        </button>
        <div class="format-row">
            支持的文件格式： <b>JSON</b><b>YAML</b><b>模板包</b
            ><a>查看示例模板 ›</a>
        </div>
        <div class="two-cols">
            <label
                >导入范围<select>
                    <option>仅导入到当前家庭</option>
                    <option>导入到全部家庭</option>
                </select></label
            ><label
                >冲突处理方式<select v-model="conflictMode">
                    <option>跳过冲突规则</option>
                    <option>覆盖现有规则</option>
                    <option>创建副本</option>
                </select></label
            >
        </div>
        <div class="check-row">
            <label
                ><input v-model="preserveIds" type="checkbox" />
                保留导入规则的原始 ID</label
            ><label
                ><input v-model="smartMerge" type="checkbox" />
                智能合并相似规则</label
            >
        </div>
        <h3>检测到的规则（共 4 条）</h3>
        <div class="import-list">
            <div v-for="rule in rules.slice(0, 4)" :key="rule.id">
                <SvgIcon :name="rule.icon" /><span
                    ><b>{{ rule.name }}</b
                    ><small>{{ rule.description }}</small></span
                ><em>待导入</em>
            </div>
        </div>
    </BaseSmartModal>

    <BaseSmartModal
        v-else-if="modelValue === 'logs'"
        :model-value="true"
        icon="log"
        title="执行日志"
        description="查看自动化规则的执行记录与结果，便于排查与优化"
        width="860px"
        confirm-text="关闭"
        @update:model-value="close"
        @confirm="close"
    >
        <div class="log-filters">
            <input type="date" value="2026-08-08" /><select>
                <option>规则名称</option></select
            ><select>
                <option>执行结果：全部</option></select
            ><button type="button">搜索</button>
        </div>
        <div class="log-table">
            <header>
                <span>执行时间</span><span>规则名称</span><span>触发来源</span
                ><span>执行结果</span><span>耗时</span><span>详情</span>
            </header>
            <template v-for="log in logs" :key="log.id"
                ><button
                    class="log-row"
                    type="button"
                    @click="expandedLog = expandedLog === log.id ? 0 : log.id"
                >
                    <span>{{ log.time }}</span
                    ><b>{{ log.name }}</b
                    ><span>{{ log.source }}</span
                    ><em :class="{ fail: log.result === '失败' }"
                        >◉ {{ log.result }}</em
                    ><span>{{ log.duration }}</span
                    ><span>{{ expandedLog === log.id ? "⌃" : "⌄" }}</span>
                </button>
                <div v-if="expandedLog === log.id" class="log-detail">
                    <div>
                        <b>触发详情</b>
                        <p>设备“小明的手机”到达“家”半径 100m</p>
                        <b>条件检查</b>
                        <p>✓ 时间条件　✓ 设备在线　✓ 位置条件</p>
                    </div>
                    <div>
                        <b>执行动作（共 4 个）</b>
                        <p>✓ 玄关灯开启　✓ 客厅灯带开启</p>
                        <p>✓ 空调 26°C　✓ 客厅窗帘打开</p>
                    </div>
                </div></template
            >
        </div>
    </BaseSmartModal>

    <BaseSmartModal
        v-else-if="modelValue === 'schedule'"
        :model-value="true"
        icon="calendar"
        title="定时设置"
        description="设置自动化的执行时间和重复规则"
        width="620px"
        confirm-text="保存设置"
        @update:model-value="close"
        @confirm="confirm"
    >
        <div class="schedule">
            <section>
                <h3><SvgIcon name="refresh" />1. 重复设置</h3>
                <div class="weekdays">
                    <button
                        v-for="(day, index) in [
                            '一',
                            '二',
                            '三',
                            '四',
                            '五',
                            '六',
                            '日',
                        ]"
                        :key="day"
                        :class="{ active: weekdays.includes(index + 1) }"
                        type="button"
                        @click="toggleValue(weekdays, index + 1)"
                    >
                        {{ day }}
                    </button>
                </div>
                <p>已选择 {{ weekdays.length }} 天，将在每周对应日期执行</p>
            </section>
            <section>
                <h3><SvgIcon name="clock" />2. 时间设置</h3>
                <label
                    >执行时间<input v-model="scheduleTime" type="time"
                /></label>
            </section>
            <section>
                <h3><SvgIcon name="calendar" />3. 日期类型</h3>
                <div class="date-types">
                    <button class="active" type="button">
                        工作日<small>周一至周五</small></button
                    ><button type="button">每天<small>包括周末</small></button>
                </div>
            </section>
            <section>
                <h3><SvgIcon name="layers" />4. 执行频率</h3>
                <div class="two-cols">
                    <select>
                        <option>每天执行</option></select
                    ><select>
                        <option>1 次</option>
                    </select>
                </div>
            </section>
            <section>
                <h3><SvgIcon name="automation" />5. 关联规则</h3>
                <label
                    v-for="rule in rules.slice(1, 3)"
                    :key="rule.id"
                    class="scheduled-rule"
                    ><input
                        v-model="scheduleRuleIds"
                        :value="rule.id"
                        type="checkbox"
                    /><SvgIcon :name="rule.icon" /><span
                        ><b>{{ rule.name }}</b
                        ><small>07:30 · 每天 · 工作日</small></span
                    ><em>已关联</em></label
                >
            </section>
        </div>
    </BaseSmartModal>

    <BaseSmartModal
        v-else-if="modelValue === 'batch'"
        :model-value="true"
        icon="power"
        title="批量启用规则"
        description="选择要启用的自动化规则，已启用的规则将保持原状态"
        width="820px"
        :confirm-text="`批量启用 (${selectedIds.length})`"
        @update:model-value="close"
        @confirm="confirm"
    >
        <input
            v-model="batchQuery"
            class="search"
            placeholder="搜索规则名称或关键词"
        />
        <div class="tabs">
            <button
                v-for="tab in ['全部', '已启用', '未启用']"
                :key="tab"
                :class="{ active: batchTab === tab }"
                type="button"
                @click="batchTab = tab"
            >
                {{ tab }}
            </button>
        </div>
        <div class="batch-table">
            <header>
                <span></span><span>规则名称</span><span>状态</span
                ><span>关联房间</span><span>关联设备</span>
            </header>
            <label v-for="rule in filteredRules" :key="rule.id"
                ><input
                    v-model="selectedIds"
                    :value="rule.id"
                    type="checkbox"
                /><span class="rule-name"
                    ><SvgIcon :name="rule.icon" /><span
                        ><b>{{ rule.name }}</b
                        ><small>{{ rule.description }}</small></span
                    ></span
                ><em>{{ rule.enabled ? "已启用" : "未启用" }}</em
                ><span>玄关、客厅</span
                ><span>{{ rule.devices }} 个设备</span></label
            >
        </div>
        <div class="batch-settings">
            <b>已选择 {{ selectedIds.length }} 条规则</b><span>执行设置</span
            ><label><input checked type="radio" /> 立即执行</label
            ><label><input type="radio" /> 仅启用，不立即执行</label>
        </div>
    </BaseSmartModal>
</template>

<style scoped>
h3 {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 0 0 14px;
    color: #17243a;
    font-size: 15px;
}
h3 > svg {
    width: 19px;
    height: 19px;
    padding: 3px;
    border-radius: 6px;
    color: #1769ff;
    background: #edf4ff;
}
.form-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    border: 1px solid #e2e8f2;
    border-radius: 14px;
    background: #fff;
}
.form-column + .form-column {
    border-left: 1px solid #e6ebf2;
}
.form-column section,
.schedule section {
    padding: 18px;
    border-bottom: 1px solid #e8edf4;
}
.form-column section:last-child,
.schedule section:last-child {
    border-bottom: 0;
}
label {
    position: relative;
    display: flex;
    gap: 7px;
    flex-direction: column;
    margin: 12px 0;
    color: #40516a;
    font-size: 12px;
    font-weight: 700;
}
label b {
    color: #ef4444;
}
input,
select,
textarea {
    width: 100%;
    border: 1px solid #d9e3f0;
    border-radius: 8px;
    background: #fff;
    padding: 10px;
    color: #26364d;
    outline: 0;
}
textarea {
    min-height: 58px;
    resize: none;
}
label > small {
    position: absolute;
    right: 9px;
    bottom: 8px;
    color: #8493a8;
    font-weight: 400;
}
.inline,
.two-cols {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
}
.inline {
    grid-template-columns: 1.3fr 1fr 1fr;
}
.outline {
    margin-top: 8px;
    border: 1px solid #cbdaf1;
    border-radius: 7px;
    padding: 8px 12px;
    color: #1769ff;
    background: #fff;
    font-weight: 700;
}
.label {
    margin: 10px 0 7px;
    color: #40516a;
    font-size: 12px;
    font-weight: 700;
}
.chips {
    display: flex;
    flex-wrap: wrap;
    gap: 7px;
}
.chips button,
.tabs button {
    border: 1px solid #dce5f1;
    border-radius: 7px;
    padding: 7px 10px;
    color: #52637a;
    background: #fff;
}
.chips button.active,
.tabs button.active,
.weekdays button.active,
.date-types button.active {
    border-color: #1769ff;
    color: #1769ff;
    background: #edf4ff;
}
.action-row {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 8px;
    border: 1px solid #dde6f1;
    border-radius: 9px;
    padding: 9px;
}
.action-row > i {
    display: grid;
    width: 21px;
    height: 21px;
    place-items: center;
    border: 1px solid #dbe4f0;
    border-radius: 50%;
    font-size: 11px;
    font-style: normal;
}
.action-row > svg {
    color: #1769ff;
}
.action-row > span {
    display: flex;
    flex: 1;
    flex-direction: column;
}
.action-row small {
    color: #718198;
}
.suffix {
    display: flex;
}
.suffix input {
    border-radius: 8px 0 0 8px;
}
.suffix span {
    display: grid;
    width: 48px;
    place-items: center;
    border: 1px solid #d9e3f0;
    border-left: 0;
    border-radius: 0 8px 8px 0;
}
.upload {
    display: flex;
    width: 100%;
    height: 165px;
    align-items: center;
    justify-content: center;
    gap: 7px;
    flex-direction: column;
    border: 1px dashed #8eb7ff;
    border-radius: 10px;
    color: #1769ff;
    background: #f9fbff;
}
.upload span {
    color: #718198;
    font-size: 12px;
}
.format-row {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 13px 0;
    border-bottom: 1px solid #e4eaf2;
    font-size: 12px;
}
.format-row b {
    border-radius: 5px;
    padding: 4px 10px;
    color: #1769ff;
    background: #eef4ff;
}
.format-row a {
    margin-left: auto;
    color: #1769ff;
}
.check-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    margin: 14px 0;
    border: 1px solid #e1e8f1;
    border-radius: 9px;
    padding: 12px;
}
.check-row label {
    display: block;
    margin: 0;
}
.check-row input {
    width: auto;
}
.import-list,
.log-table,
.batch-table {
    overflow: hidden;
    border: 1px solid #dce5f1;
    border-radius: 10px;
}
.import-list > div {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 9px 13px;
    border-bottom: 1px solid #e7ecf3;
}
.import-list span {
    display: flex;
    flex: 1;
    flex-direction: column;
}
.import-list small {
    color: #7b899c;
}
.import-list em {
    border-radius: 6px;
    padding: 4px 9px;
    color: #19a55d;
    background: #e9f8ef;
    font-style: normal;
}
.log-filters {
    display: grid;
    grid-template-columns: 1.4fr 1fr 1fr auto;
    gap: 8px;
    margin-bottom: 14px;
}
.log-filters button {
    border-radius: 8px;
    padding: 0 18px;
    color: #fff;
    background: #1769ff;
}
.log-table header,
.log-row {
    display: grid;
    width: 100%;
    grid-template-columns: 1.35fr 1.3fr 1fr 0.8fr 0.5fr 0.35fr;
    align-items: center;
    gap: 8px;
    padding: 11px 14px;
    text-align: left;
}
.log-table header {
    color: #677890;
    background: #f7f9fc;
    font-size: 12px;
    font-weight: 700;
}
.log-row {
    border-top: 1px solid #e5eaf1;
    background: #fff;
    font-size: 12px;
}
.log-row em {
    color: #19a45d;
    font-style: normal;
}
.log-row em.fail {
    color: #ef4444;
}
.log-detail {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin: 0 10px 10px;
    padding: 16px;
    border: 1px solid #b8d0ff;
    border-radius: 9px;
    background: #fbfdff;
    font-size: 12px;
}
.log-detail p {
    margin: 8px 0;
    color: #61718a;
}
.schedule {
    overflow: hidden;
    border: 1px solid #e1e8f1;
    border-radius: 12px;
    background: #fff;
}
.weekdays {
    display: flex;
    gap: 12px;
}
.weekdays button {
    width: 42px;
    height: 35px;
    border: 1px solid #dbe4ef;
    border-radius: 20px;
    background: #fff;
}
.schedule p {
    margin-top: 8px;
    color: #718198;
    font-size: 12px;
}
.date-types {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
}
.date-types button {
    display: flex;
    gap: 4px;
    flex-direction: column;
    border: 1px solid #dce5f1;
    border-radius: 8px;
    padding: 12px;
    text-align: left;
    background: #fff;
}
.date-types small {
    color: #7a899d;
}
.scheduled-rule {
    display: grid;
    grid-template-columns: auto auto 1fr auto;
    align-items: center;
    padding: 9px;
    border: 1px solid #e2e8f1;
    border-radius: 8px;
}
.scheduled-rule input {
    width: auto;
}
.scheduled-rule span {
    display: flex;
    flex-direction: column;
}
.scheduled-rule em {
    color: #19a45d;
    font-style: normal;
}
.search {
    max-width: 300px;
}
.tabs {
    display: flex;
    gap: 8px;
    margin: 12px 0;
}
.batch-table header,
.batch-table label {
    display: grid;
    grid-template-columns: 28px 2fr 0.7fr 1fr 0.7fr;
    align-items: center;
    gap: 10px;
    margin: 0;
    padding: 10px 12px;
    border-bottom: 1px solid #e5ebf2;
}
.batch-table header {
    color: #718198;
    background: #f8fafd;
    font-size: 12px;
}
.batch-table input {
    width: auto;
}
.rule-name {
    display: flex;
    align-items: center;
    gap: 9px;
}
.rule-name > span {
    display: flex;
    flex-direction: column;
}
.rule-name small {
    color: #7d8c9f;
}
.batch-table em {
    width: max-content;
    border-radius: 5px;
    padding: 3px 7px;
    color: #19a45d;
    background: #e7f8ed;
    font-style: normal;
}
.batch-settings {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-top: 14px;
    border: 1px solid #e1e8f1;
    border-radius: 9px;
    padding: 14px;
}
.batch-settings b {
    margin-right: auto;
}
.batch-settings label {
    display: block;
    margin: 0;
}
.batch-settings input {
    width: auto;
}
@media (max-width: 760px) {
    .form-grid {
        grid-template-columns: 1fr;
    }
    .form-column + .form-column {
        border-left: 0;
    }
    .two-cols,
    .log-detail {
        grid-template-columns: 1fr;
    }
    .batch-table header,
    .batch-table label {
        grid-template-columns: 24px 2fr 0.8fr;
    }
    .batch-table header span:nth-child(n + 4),
    .batch-table label > span:nth-child(n + 4) {
        display: none;
    }
}
</style>
