<script setup lang="ts">
import { computed, ref } from "vue";
import { ElMessage } from "element-plus";
import AutomationDialogs from "../components/automation/AutomationDialogs.vue";
import type { AutomationDialog } from "../components/automation/AutomationDialogs.vue";
import SvgIcon from "../components/common/SvgIcon.vue";
import PageHeader from "../components/common/PageHeader.vue";
import StatsCard from "../components/common/StatsCard.vue";
import { automationRules, type AutomationRule } from "../mock/automations";

const automations = ref<AutomationRule[]>(automationRules);
const selectedId = ref(1);
const query = ref("");
const triggerFilter = ref("");
const statusFilter = ref("");
const activeDialog = ref<AutomationDialog>(null);
const selected = computed(
    () =>
        automations.value.find((item) => item.id === selectedId.value) ??
        automations.value[0],
);
const visible = computed(() =>
    automations.value.filter(
        (item) =>
            item.name.includes(query.value) &&
            (!triggerFilter.value || item.trigger === triggerFilter.value) &&
            (!statusFilter.value ||
                String(item.enabled) === statusFilter.value),
    ),
);

const run = (item: AutomationRule) => ElMessage.success(`“${item.name}”已执行`);
const saveRule = (payload: {
    mode: "create" | "edit";
    name: string;
    description: string;
    trigger: string;
}) => {
    if (payload.mode === "edit" && selected.value)
        Object.assign(selected.value, payload);
    else {
        const rule: AutomationRule = {
            id: Date.now(),
            ...payload,
            devices: 3,
            icon: "automation",
            tone: "blue",
            enabled: true,
        };
        automations.value.unshift(rule);
        selectedId.value = rule.id;
    }
    ElMessage.success(payload.mode === "edit" ? "规则已保存" : "自动化已创建");
};
const batchEnable = (ids: number[]) => {
    automations.value.forEach((rule) => {
        if (ids.includes(rule.id)) rule.enabled = true;
    });
    ElMessage.success(`已启用 ${ids.length} 条规则`);
};
</script>

<template>
    <div class="contents">
        <main class="automation page-shell page-enter">
            <PageHeader title="自动化" description="管理家庭自动化规则、触发条件与执行状态">
                <label
                    ><SvgIcon name="search" size="sm" /><input
                        placeholder="搜索设备、场景或房间"
                /></label>
            </PageHeader>
            <div class="filters">
                <label
                    ><SvgIcon name="search" size="sm" /><input
                        v-model="query"
                        placeholder="搜索自动化规则" /></label
                ><span>触发类型</span
                ><select v-model="triggerFilter">
                    <option value="">全部</option>
                    <option>位置触发</option>
                    <option>时间触发</option>
                    <option>设备状态</option></select
                ><span>状态</span
                ><select v-model="statusFilter">
                    <option value="">全部</option>
                    <option value="true">已启用</option>
                    <option value="false">已停用</option></select
                ><button class="primary" @click="activeDialog = 'create'">
                    <SvgIcon name="plus" size="sm" />创建自动化</button
                ><button @click="activeDialog = 'import'">
                    <SvgIcon name="upload" size="sm" />导入规则
                </button>
            </div>
            <section class="stats card-grid-enter">
                <StatsCard
                    icon="check-circle"
                    label="已启用规则"
                    value="18"
                    detail="共 24 条规则"
                    tone="blue"
                />
                <StatsCard
                    icon="power"
                    label="运行中"
                    value="5"
                    detail="正在执行"
                    tone="green"
                />
                <StatsCard
                    icon="calendar"
                    label="今日执行次数"
                    value="36 次"
                    detail="较昨日 ↑ 15%"
                    tone="orange"
                />
                <StatsCard
                    icon="warning"
                    label="异常规则"
                    value="1"
                    detail="需要处理"
                    tone="red"
                />
            </section>
            <section class="cards card-grid-enter">
                <article
                    v-for="item in visible"
                    :key="item.id"
                    :class="{ selected: item.id === selectedId }"
                    @click="selectedId = item.id"
                >
                    <header>
                        <i :class="item.tone"><SvgIcon :name="item.icon" /></i
                        ><span
                            ><b>{{ item.name }}</b
                            ><em>{{ item.enabled ? "已启用" : "已停用" }}</em
                            ><small>{{ item.description }}</small></span
                        ><button>⋮</button>
                    </header>
                    <div class="devices">
                        <i class="dev-light"><SvgIcon name="light" size="sm" /></i
                        ><i class="dev-curtain"
                            ><SvgIcon name="curtain" size="sm" /></i
                        ><i class="dev-temp"
                            ><SvgIcon name="temperature" size="sm" /></i
                        ><span>等 {{ item.devices }} 个设备</span>
                    </div>
                    <footer>
                        <button @click.stop="run(item)">执行</button
                        ><button
                            @click.stop="
                                selectedId = item.id;
                                activeDialog = 'edit';
                            "
                        >
                            <SvgIcon name="edit" size="sm" />编辑</button
                        ><label class="switch"
                            ><input
                                v-model="item.enabled"
                                type="checkbox" /><span></span
                        ></label>
                    </footer>
                </article>
            </section>
            <section class="panel flow">
                <header>
                    <h2>自动化流程 / 最近执行</h2>
                    <a @click="activeDialog = 'logs'">查看更多 ›</a>
                </header>
                <div class="flow-body">
                    <div class="steps">
                        <div
                            v-for="(step, index) in [
                                ['位置触发', '到达家 100m 内', 'room', 'blue'],
                                ['打开灯光', '客厅灯、玄关灯', 'light', 'orange'],
                                ['关闭窗帘', '客厅窗帘', 'curtain', 'teal'],
                                [
                                    '设置空调',
                                    '制冷 26°C',
                                    'air-conditioner',
                                    'blue',
                                ],
                                ['安防模式', '回家模式', 'security', 'purple'],
                            ]"
                            :key="step[0]"
                        >
                            <i :class="`is-${step[3]}`"
                                ><SvgIcon :name="step[2]" /></i
                            ><b>{{ step[0] }}</b
                            ><small>{{ step[1] }}</small
                            ><em v-if="index < 4">→</em>
                        </div>
                    </div>
                    <div class="records">
                        <h3>最近执行记录</h3>
                        <p
                            v-for="row in [
                                ['今天 18:36', '回家联动', '成功', '2.4s'],
                                ['今天 07:00', '晨间唤醒联动', '成功', '3.1s'],
                                [
                                    '昨天 22:30',
                                    '睡眠模式自动化',
                                    '成功',
                                    '2.8s',
                                ],
                                ['昨天 12:15', '空调节能联动', '成功', '1.9s'],
                            ]"
                            :key="row[0]"
                        >
                            <time>{{ row[0] }}</time
                            ><span>{{ row[1] }}</span
                            ><b>◉ {{ row[2] }}</b
                            ><em>{{ row[3] }}</em>
                        </p>
                    </div>
                </div>
            </section>
        </main>
        <aside class="right page-shell">
            <section v-if="selected" class="panel detail">
                <header>
                    <h2>▣ 规则详情</h2>
                    <SvgIcon name="scan" size="sm" />
                </header>
                <div class="detail-title">
                    <i :class="selected.tone"
                        ><SvgIcon :name="selected.icon" /></i
                    ><span
                        ><h3>{{ selected.name }}</h3>
                        <em>{{ selected.enabled ? "已启用" : "已停用" }}</em>
                        <p>当您回到家附近，自动执行舒适回家流程</p></span
                    >
                </div>
                <dl>
                    <div>
                        <dt>触发条件</dt>
                        <dd>{{ selected.description }}</dd>
                    </div>
                    <div>
                        <dt>执行方式</dt>
                        <dd>自动执行</dd>
                    </div>
                    <div>
                        <dt>关联房间</dt>
                        <dd>玄关、客厅、餐厅、主卧</dd>
                    </div>
                    <div>
                        <dt>关联设备</dt>
                        <dd class="link">{{ selected.devices }} 个设备</dd>
                    </div>
                    <div>
                        <dt>创建时间</dt>
                        <dd>2026-06-15 10:30</dd>
                    </div>
                    <div>
                        <dt>更新时间</dt>
                        <dd>2026-08-01 10:15</dd>
                    </div>
                </dl>
                <footer>
                    <button class="primary" @click="run(selected)">
                        ▶ 执行</button
                    ><button @click="activeDialog = 'edit'">
                        <SvgIcon name="edit" size="sm" />编辑</button
                    ><button>▣ 复制</button>
                </footer>
            </section>
            <section class="panel">
                <h2>▣ 快捷操作</h2>
                <div class="quick">
                    <button
                        class="tone-blue"
                        @click="activeDialog = 'batch'"
                    >
                        <SvgIcon name="power" />批量启用<small
                            >启用多个规则</small
                        ></button
                    ><button
                        class="tone-purple"
                        @click="activeDialog = 'schedule'"
                    >
                        <SvgIcon name="clock" />定时设置<small
                            >统一定时管理</small
                        ></button
                    ><button class="tone-teal">
                        <SvgIcon name="layers" />排序管理<small
                            >自定义排序</small
                        ></button
                    ><button
                        class="tone-orange"
                        @click="activeDialog = 'logs'"
                    >
                        <SvgIcon name="log" />查看日志<small
                            >执行记录与日志</small
                        >
                    </button>
                </div>
            </section>
            <section class="panel templates">
                <header>
                    <h2>▣ 推荐模板</h2>
                    <a>更多 ›</a>
                </header>
                <p
                    v-for="item in [
                        [
                            'home',
                            '节能回家',
                            '节能模式 + 舒适回家流程',
                            'green',
                        ],
                        [
                            'security',
                            '夜间安防',
                            '夜间自动布防与照明联动',
                            'purple',
                        ],
                        [
                            'illumination',
                            '晨间唤醒',
                            '灯光、窗帘、空调联动唤醒',
                            'orange',
                        ],
                    ]"
                    :key="item[1]"
                >
                    <i :class="item[3]"><SvgIcon :name="item[0]" /></i
                    ><span
                        ><b>{{ item[1] }}</b
                        ><small>{{ item[2] }}</small></span
                    ><button>使用</button>
                </p>
                <a class="browse">浏览更多模板 ›</a>
            </section>
        </aside>
        <AutomationDialogs
            v-model="activeDialog"
            :rule="selected"
            :rules="automations"
            @save="saveRule"
            @batch="batchEnable"
            @imported="(count) => ElMessage.success(`已导入 ${count} 条规则`)"
            @scheduled="() => ElMessage.success('定时设置已保存')"
        />
    </div>
</template>

<style scoped>
.page-shell {
    overflow: auto;
}
.automation {
    display: flex;
    flex-direction: column;
    gap: 14px;
    padding: 20px;
}
.filters label {
    display: flex;
    align-items: center;
    gap: 7px;
    border: 1px solid var(--color-border-default);
    border-radius: 9px;
    background: var(--color-card-bg);
    padding: 0 11px;
    color: var(--color-text-tertiary);
}
.filters input {
    min-width: 0;
    outline: 0;
    font-size: 14px;
}
.filters {
    display: flex;
    align-items: center;
    gap: 10px;
}
.filters label {
    width: 230px;
    height: 42px;
}
.filters > span {
    font-size: 13px;
    font-weight: 900;
}
.filters select,
.filters button {
    height: 42px;
    border: 1px solid var(--color-border-default);
    border-radius: 8px;
    background: var(--color-card-bg);
    padding: 0 12px;
    font-size: 13px;
    font-weight: 800;
}

.filters select option {
    background: var(--color-card-bg);
    color: var(--color-text-primary);
}
.filters select {
    width: 112px;
}
.filters .primary,
.primary {
    border-color: var(--color-primary-600);
    background: var(--color-primary-600);
    color: #fff;
}
.stats {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
}
.cards header > i,
.detail-title > i,
.templates p > i {
    display: grid;
    width: 50px;
    height: 50px;
    flex: none;
    place-items: center;
    border-radius: 50%;
}
.blue {
    background: var(--color-primary-50);
    color: var(--color-primary-600);
}
.green {
    background: var(--color-success-soft);
    color: var(--color-success);
}
.purple {
    background: var(--tone-purple-soft);
    color: var(--tone-purple);
}
.orange {
    background: var(--tone-orange-soft);
    color: var(--tone-orange);
}
.red {
    background: var(--color-danger-soft);
    color: var(--color-danger);
}

.cards {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
}
.cards article {
    min-width: 0;
    border: 1px solid var(--color-border-default);
    border-radius: 13px;
    background: var(--color-card-bg);
    padding: 13px;
    cursor: pointer;
}
.cards article.selected {
    border: 1.5px solid var(--color-primary-600);
    box-shadow: 0 0 0 1px var(--color-primary-200);
}
.cards header {
    display: flex;
    gap: 11px;
}
.cards header > i {
    width: 44px;
    height: 44px;
}
.cards header span {
    display: grid;
    grid-template-columns: auto auto;
    min-width: 0;
    flex: 1;
    align-content: start;
    gap: 2px 7px;
}
.cards header b {
    overflow: hidden;
    font-size: 15px;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.cards header em {
    width: max-content;
    border-radius: 5px;
    background: var(--color-success-soft);
    padding: 3px 7px;
    color: var(--color-success);
    font-size: 11px;
    font-style: normal;
}
.cards header small {
    grid-column: span 2;
    overflow: hidden;
    color: var(--color-text-tertiary);
    font-size: 12px;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.devices {
    display: flex;
    align-items: center;
    gap: 6px;
    margin: 13px 0;
}
.devices i {
    display: grid;
    width: 30px;
    height: 30px;
    place-items: center;
    border-radius: 6px;
    background: var(--color-primary-50);
    color: var(--color-primary-600);
}
.devices i.dev-curtain {
    background: var(--tone-teal-soft);
    color: var(--tone-teal);
}
.devices i.dev-temp {
    background: var(--color-primary-50);
    color: var(--color-primary-600);
}
.devices span {
    color: var(--color-text-tertiary);
    font-size: 12px;
}
.cards footer {
    display: flex;
    gap: 8px;
    border-top: 1px solid var(--color-border-subtle);
    padding-top: 10px;
}
.cards footer > button {
    height: 34px;
    border: 1px solid var(--color-border-default);
    border-radius: 6px;
    padding: 0 10px;
    color: var(--color-primary-600);
    font-size: 13px;
    font-weight: 900;
}
.switch {
    margin-left: auto;
}
.switch input {
    display: none;
}
.switch span {
    display: block;
    width: 40px;
    height: 23px;
    border-radius: 20px;
    background: var(--color-border-strong);
    padding: 2px;
}
.switch span:after {
    display: block;
    width: 19px;
    height: 19px;
    border-radius: 50%;
    background: #fff;
    content: "";
    transition: 0.2s;
}
.switch input:checked + span {
    background: var(--color-primary-600);
}
.switch input:checked + span:after {
    transform: translateX(17px);
}
.panel {
    border: 1px solid var(--color-border-default);
    border-radius: 14px;
    background: var(--color-card-bg);
    padding: 14px;
}
.panel h2 {
    font-size: 16px;
    font-weight: 900;
}
.panel header {
    display: flex;
    justify-content: space-between;
}
.panel a,
.link {
    color: var(--color-primary-600) !important;
    font-size: 12px;
    font-weight: 800;
    cursor: pointer;
}
.flow-body {
    display: grid;
    grid-template-columns: 1fr 1fr;
    margin-top: 10px;
}
.steps {
    display: flex;
    align-items: center;
    padding: 16px 6px;
}
.steps > div {
    position: relative;
    display: flex;
    min-width: 0;
    flex: 1;
    align-items: center;
    flex-direction: column;
}
.steps i {
    display: grid;
    width: 42px;
    height: 42px;
    place-items: center;
    border-radius: 14px;
    background: var(--color-primary-50);
    color: var(--color-primary-600);
}
.steps i.is-blue {
    background: var(--color-primary-50);
    color: var(--color-primary-600);
}
.steps i.is-orange {
    background: var(--tone-orange-soft);
    color: var(--tone-orange);
}
.steps i.is-teal {
    background: var(--tone-teal-soft);
    color: var(--tone-teal);
}
.steps i.is-purple {
    background: var(--tone-purple-soft);
    color: var(--tone-purple);
}
.steps b {
    margin-top: 8px;
    font-size: 12px;
}
.steps small {
    color: var(--color-text-tertiary);
    font-size: 11px;
    white-space: nowrap;
}
.steps em {
    position: absolute;
    top: 13px;
    right: -5px;
    color: var(--color-primary-600);
    font-size: 22px;
    font-style: normal;
}
.records {
    border-left: 1px solid var(--color-border-subtle);
    padding-left: 14px;
}
.records h3 {
    font-size: 13px;
}
.records p {
    display: grid;
    grid-template-columns: 82px 1fr 52px 34px;
    gap: 5px;
    padding: 7px 0;
    border-bottom: 1px solid var(--color-border-subtle);
    font-size: 11px;
}
.records time,
.records em {
    color: var(--color-text-tertiary);
    font-style: normal;
}
.records b {
    color: var(--color-success);
}
.right {
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 12px;
}
.detail-title {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 15px 0;
}
.detail-title span {
    display: grid;
    grid-template-columns: auto auto;
    min-width: 0;
}
.detail-title h3 {
    font-size: 18px;
}
.detail-title em {
    width: max-content;
    margin-left: 8px;
    border-radius: 5px;
    background: var(--color-success-soft);
    padding: 2px 6px;
    color: var(--color-success);
    font-size: 12px;
    font-style: normal;
}
.detail-title p {
    grid-column: span 2;
    color: var(--color-text-tertiary);
    font-size: 12px;
}
.detail dl div {
    display: grid;
    grid-template-columns: 82px 1fr;
    padding: 7px 0;
    font-size: 12px;
}
.detail dt {
    color: var(--color-text-tertiary);
}
.detail dd {
    color: var(--color-text-secondary);
}
.detail footer {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 7px;
    margin-top: 14px;
}
.detail footer button {
    height: 40px;
    border: 1px solid var(--color-border-default);
    border-radius: 7px;
    font-size: 13px;
    font-weight: 900;
}
.quick {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-top: 12px;
}
.quick button {
    display: grid;
    min-height: 62px;
    grid-template-columns: 28px 1fr;
    align-items: center;
    border: 1px solid var(--color-border-default);
    border-radius: 8px;
    padding: 10px;
    text-align: left;
    font-size: 13px;
    font-weight: 900;
}
.quick svg {
    grid-row: span 2;
    color: var(--color-primary-600);
}
.quick button.tone-blue svg {
    color: var(--color-primary-600);
}
.quick button.tone-purple svg {
    color: var(--tone-purple);
}
.quick button.tone-teal svg {
    color: var(--tone-teal);
}
.quick button.tone-orange svg {
    color: var(--tone-orange);
}
.quick small {
    color: var(--color-text-tertiary);
    font-size: 11px;
    font-weight: 500;
}
.templates p {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 10px;
}
.templates p > i {
    width: 34px;
    height: 34px;
}
.templates p span {
    display: flex;
    min-width: 0;
    flex: 1;
    flex-direction: column;
    font-size: 12px;
}
.templates p small {
    overflow: hidden;
    color: var(--color-text-tertiary);
    font-size: 11px;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.templates p button {
    border: 1px solid var(--color-border-default);
    border-radius: 6px;
    padding: 5px 10px;
    color: var(--color-primary-600);
    font-size: 12px;
    font-weight: 900;
}
.browse {
    display: block;
    margin-top: 12px;
    text-align: center;
}
@media (max-width: 1200px) {
    .filters {
        flex-wrap: wrap;
    }
    .stats {
        grid-template-columns: repeat(2, 1fr);
    }
    .cards {
        grid-template-columns: repeat(2, 1fr);
    }
    .flow-body {
        grid-template-columns: 1fr;
    }
    .records {
        border: 0;
        border-top: 1px solid var(--color-border-subtle);
        padding: 10px 0 0;
    }
}
</style>
