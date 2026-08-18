<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { ElMessage } from "element-plus";
import BaseButton from "../common/BaseButton.vue";
import BaseSmartModal from "../common/BaseSmartModal.vue";
import ConfirmActionDialog from "../common/ConfirmActionDialog.vue";
import ConfirmEntitySummary from "../common/ConfirmEntitySummary.vue";
import SvgIcon from "../common/SvgIcon.vue";
import type { AccountForm, HouseholdContext } from "../../types/settings";
import SettingsSectionCard from "./SettingsSectionCard.vue";

const props = defineProps<{
    activeHouseholdId: number | null;
    fieldErrors: Record<string, string>;
    form: AccountForm;
    households: HouseholdContext[];
    loading: boolean;
    dirty: boolean;
    switching: boolean;
}>();

const emit = defineEmits<{
    createHousehold: [payload: { name: string; address: string }];
    deleteAvatar: [];
    save: [];
    switchHousehold: [id: number];
    uploadAvatar: [file: File];
    updateForm: [form: AccountForm];
}>();

const avatarInput = ref<HTMLInputElement | null>(null);
const dialogVisible = ref(false);
const previewUrl = ref<string | null>(null);
const avatarLoadError = ref(false);
const creating = ref(false);
const createName = ref("");
const createAddress = ref("");
const deleteAvatarConfirmOpen = ref(false);
const timezones = [
    "Asia/Shanghai",
    "Asia/Tokyo",
    "Europe/London",
    "America/New_York",
    "UTC",
];

const visibleAvatarUrl = computed(() =>
    avatarLoadError.value ? null : (previewUrl.value ?? props.form.avatarUrl),
);
const accountInitial = computed(
    () => props.form.name.trim().slice(0, 1) || "用",
);
const householdSummary = computed(
    () =>
        [props.form.householdName, props.form.address]
            .filter(Boolean)
            .join(" · ") || "尚未设置家庭信息",
);

watch(
    () => props.form.avatarUrl,
    () => {
        avatarLoadError.value = false;
        if (previewUrl.value) {
            URL.revokeObjectURL(previewUrl.value);
            previewUrl.value = null;
        }
    },
);

watch(creating, (visible) => {
    if (!visible) {
        createName.value = "";
        createAddress.value = "";
    }
});

const updateField = <K extends keyof AccountForm>(
    key: K,
    value: AccountForm[K],
) => {
    emit("updateForm", {
        ...props.form,
        [key]: value,
    });
};

const selectAvatar = () => {
    avatarInput.value?.click();
};

const openDialog = () => {
    dialogVisible.value = true;
};

const uploadAvatar = (event: Event) => {
    const target = event.target as HTMLInputElement;
    const file = target.files?.[0];

    if (!file) {
        return;
    }

    // 文件类型校验（已有 accept 属性兜底，这里做二次校验）
    const allowedTypes = ["image/jpeg", "image/png", "image/webp"];
    if (!allowedTypes.includes(file.type)) {
        ElMessage.warning("仅支持 JPEG、PNG 或 WebP 格式的头像");
        target.value = "";
        return;
    }

    // 文件大小校验：头像限制 5MB
    const maxSize = 5 * 1024 * 1024;
    if (file.size > maxSize) {
        ElMessage.warning("头像文件大小不能超过 5MB");
        target.value = "";
        return;
    }

    if (previewUrl.value) {
        URL.revokeObjectURL(previewUrl.value);
    }

    previewUrl.value = URL.createObjectURL(file);
    emit("uploadAvatar", file);
    target.value = "";
};

const deleteAvatar = () => {
    deleteAvatarConfirmOpen.value = true;
};

const confirmDeleteAvatar = () => {
    deleteAvatarConfirmOpen.value = false;
    emit("deleteAvatar");
};

const toggleCreate = () => {
    if (creating.value) {
        createName.value = "";
        createAddress.value = "";
    }
    creating.value = !creating.value;
};

const submitCreate = () => {
    const name = createName.value.trim();
    if (!name) return;
    emit("createHousehold", { name, address: createAddress.value.trim() });
    createName.value = "";
    createAddress.value = "";
    creating.value = false;
};
</script>

<template>
    <SettingsSectionCard id="account" icon="account" title="账户与家庭" tone="primary">
        <div class="account-summary">
            <img
                v-if="visibleAvatarUrl"
                class="h-14 w-14 shrink-0 rounded-full object-cover"
                :src="visibleAvatarUrl"
                :alt="form.name"
                @error="avatarLoadError = true"
            />
            <span v-else class="account-avatar account-avatar-large">
                {{ accountInitial }}
            </span>
            <div class="min-w-0">
                <strong
                    class="block truncate text-[var(--color-text-primary)]"
                    >{{ form.name || "未命名账户" }}</strong
                >
                <span
                    class="block truncate text-sm text-[var(--color-text-tertiary)]"
                    >{{ form.email || "未设置邮箱" }}</span
                >
                <span
                    class="mt-1 block truncate text-xs text-[var(--color-text-tertiary)]"
                >
                    {{ householdSummary }}
                </span>
            </div>
        </div>

        <button
            class="settings-entry-button account-entry"
            type="button"
            @click="openDialog"
        >
            <span class="entry-icon"><SvgIcon name="account" /></span>
            <span class="entry-copy">
                <strong>账户信息</strong>
                <small>查看与编辑个人资料、家庭及所在时区</small>
            </span>
            <SvgIcon class="entry-arrow" name="chevron-right" />
        </button>
    </SettingsSectionCard>

    <BaseSmartModal
        v-model="dialogVisible"
        width="860px"
        title="账户与家庭"
        description="查看当前账户信息并管理所属家庭"
        icon="account"
        tone="primary"
        body-tone="neutral"
        :close-button-disabled="loading"
    >
        <div class="account-dialog-layout">
            <aside class="account-dialog-sidebar">
                <section class="current-account">
                    <img v-if="visibleAvatarUrl" :src="visibleAvatarUrl" :alt="form.name" @error="avatarLoadError = true" />
                    <span v-else class="account-avatar">{{ accountInitial }}</span>
                    <div class="min-w-0"><span>当前账户</span><strong>{{ form.name || "未命名账户" }}</strong><p>{{ form.email || "未设置邮箱" }}</p></div>
                    <div class="avatar-actions"><BaseButton :disabled="loading" size="sm" @click="selectAvatar">上传</BaseButton><BaseButton :disabled="loading || !visibleAvatarUrl" size="sm" @click="deleteAvatar">删除</BaseButton></div>
                    <input ref="avatarInput" class="hidden" accept="image/jpeg,image/png,image/webp" type="file" @change="uploadAvatar" />
                </section>

                <section class="household-switcher">
                    <div class="household-heading"><span>我的家庭</span><button class="household-create-toggle" type="button" @click="toggleCreate">＋ 新建</button></div>
                    <div v-if="props.households.length" class="household-list">
                        <button v-for="household in props.households" :key="household.id" class="household-item" :class="{ 'is-active': household.id === props.activeHouseholdId }" :disabled="props.switching" type="button" @click="emit('switchHousehold', household.id)">
                            <span class="household-item-main"><strong>{{ household.name }}</strong><small>{{ household.memberCount }} 位成员 · {{ household.role === "admin" ? "管理员" : "成员" }}</small></span>
                            <span v-if="household.id === props.activeHouseholdId" class="household-current">当前</span>
                        </button>
                    </div>
                    <p v-else class="household-empty">尚未创建家庭，请先新建家庭</p>
                </section>
            </aside>

            <section class="account-edit-card">
                <header class="account-edit-header"><div><strong>账户与家庭资料</strong><small>更新个人资料和当前家庭的基础信息</small></div><span>{{ dirty ? "待保存" : "已同步" }}</span></header>
                <div class="form-grid">
            <label class="account-field"
                ><span>姓名</span
                ><input
                    class="settings-input"
                    :class="{ 'has-error': props.fieldErrors.name }"
                    :value="form.name"
                    @input="
                        updateField(
                            'name',
                            ($event.target as HTMLInputElement).value,
                        )
                    "
                /><small
                    v-if="props.fieldErrors.name"
                    class="field-error"
                    >{{ props.fieldErrors.name }}</small
                ></label
            >
            <label class="account-field"
                ><span>邮箱</span
                ><input
                    class="settings-input"
                    :class="{ 'has-error': props.fieldErrors.email }"
                    :value="form.email"
                    @input="
                        updateField(
                            'email',
                            ($event.target as HTMLInputElement).value,
                        )
                    "
                /><small
                    v-if="props.fieldErrors.email"
                    class="field-error"
                    >{{ props.fieldErrors.email }}</small
                ></label
            >
            <label class="account-field"
                ><span>家庭名称</span
                ><input
                    class="settings-input"
                    :class="{ 'has-error': props.fieldErrors.name }"
                    :value="form.householdName"
                    @input="
                        updateField(
                            'householdName',
                            ($event.target as HTMLInputElement).value,
                        )
                    "
            /></label>
            <label class="account-field address-field"
                ><span>家庭地址</span
                ><input
                    class="settings-input"
                    :value="form.address"
                    @input="
                        updateField(
                            'address',
                            ($event.target as HTMLInputElement).value,
                        )
                    "
            /></label>
            <label class="account-field">
                <span>时区</span>
                <select
                    class="settings-input"
                    :value="form.timezone"
                    @change="
                        updateField(
                            'timezone',
                            ($event.target as HTMLSelectElement).value,
                        )
                    "
                >
                    <option
                        v-for="timezone in timezones"
                        :key="timezone"
                        :value="timezone"
                    >
                        {{ timezone }}
                    </option>
                </select>
            </label>
                </div>
            </section>
        </div>

        <template #footer>
            <footer class="dialog-footer">
                <span>{{ dirty ? "有尚未保存的修改" : "账户信息已同步" }}</span>
                <div>
                    <BaseButton
                        :disabled="loading"
                        @click="dialogVisible = false"
                    >
                        关闭
                    </BaseButton>
                    <BaseButton
                        :disabled="!dirty"
                        :loading="loading"
                        variant="primary"
                        @click="emit('save')"
                    >
                        保存更改
                    </BaseButton>
                </div>
            </footer>
        </template>
    </BaseSmartModal>

    <BaseSmartModal
        v-model="creating"
        width="440px"
        title="新建家庭"
        description="创建家庭后将自动切换到新家庭"
        icon="plus"
        tone="primary"
        body-tone="neutral"
    >
        <div class="create-household-dialog">
            <label><span>家庭名称 *</span><input v-model="createName" class="settings-input" placeholder="例如 张三的智能家庭" /></label>
            <label><span>家庭地址</span><input v-model="createAddress" class="settings-input" placeholder="可选" /></label>
        </div>
        <template #footer>
            <footer class="dialog-footer create-dialog-footer"><span>创建后可继续完善家庭资料</span><div><BaseButton @click="toggleCreate">取消</BaseButton><BaseButton :disabled="!createName.trim()" variant="primary" @click="submitCreate">创建并切换</BaseButton></div></footer>
        </template>
    </BaseSmartModal>

    <ConfirmActionDialog
        v-if="deleteAvatarConfirmOpen"
        :model-value="true"
        title="删除头像"
        description="删除后，头像将恢复为默认显示。"
        confirm-text="删除"
        warning="删除后无法恢复，请谨慎操作。"
        @confirm="confirmDeleteAvatar"
        @update:model-value="!$event && (deleteAvatarConfirmOpen = false)"
    >
        <ConfirmEntitySummary
            icon="account"
            title="当前头像"
            description="删除后使用默认占位头像"
            color="var(--color-danger)"
        />
    </ConfirmActionDialog>
</template>

<style scoped>
.account-summary,
.current-account {
    display: flex;
    align-items: center;
    gap: 14px;
}

/* 账户与家庭：首页卡片式布局，模块色柔和渐变背景 */
.account-summary {
    position: relative;
    overflow: hidden;
    padding: 16px 18px;
    border: 1px solid color-mix(in srgb, var(--color-primary-600) 18%, var(--color-border));
    border-radius: 16px;
    background: linear-gradient(
        135deg,
        color-mix(in srgb, var(--color-primary-600) 8%, var(--color-card-bg)),
        var(--color-primary-50)
    );
    box-shadow: var(--shadow-card);
}

.account-summary::before {
    content: "";
    position: absolute;
    top: -30px;
    right: -30px;
    width: 110px;
    height: 110px;
    border-radius: 50%;
    background: radial-gradient(
        circle,
        color-mix(in srgb, var(--color-primary-600) 16%, transparent),
        transparent 70%
    );
    pointer-events: none;
}

.account-summary > div.min-w-0 {
    position: relative;
}

.settings-entry-button {
    display: grid;
    width: 100%;
    min-height: 68px;
    grid-template-columns: 40px minmax(0, 1fr) 20px;
    align-items: center;
    gap: 12px;
    margin-top: 16px;
    border: 1px solid var(--color-primary-200);
    border-radius: 14px;
    background: linear-gradient(135deg, var(--color-card-bg), var(--color-primary-50));
    padding: 12px 14px;
    text-align: left;
    box-shadow: 0 6px 18px color-mix(in srgb, var(--color-primary-600) 8%, transparent);
    transition: transform 160ms var(--motion-ease), border-color 160ms, box-shadow 160ms;
}

.settings-entry-button:hover {
    transform: translateY(-2px);
    border-color: var(--color-primary-400);
    box-shadow: 0 10px 24px color-mix(in srgb, var(--color-primary-600) 14%, transparent);
}

.entry-icon {
    display: grid;
    width: 40px;
    height: 40px;
    place-items: center;
    border-radius: 12px;
    background: var(--color-primary-600);
    color: white;
}

.entry-copy {
    display: grid;
    min-width: 0;
    gap: 3px;
}

.entry-copy strong { color: var(--color-text-primary); font-size: 14px; }
.entry-copy small { overflow: hidden; color: var(--color-text-tertiary); font-size: 12px; text-overflow: ellipsis; white-space: nowrap; }
.entry-arrow { color: var(--color-primary-500); transition: transform 160ms; }
.settings-entry-button:hover .entry-arrow { transform: translateX(3px); }

.account-summary > div,
.current-account > div:first-of-type {
    flex: 1;
}

.current-account {
    margin: 0 20px 10px;
    padding: 16px 18px;
    border: 1px solid color-mix(in srgb, var(--color-primary-600) 18%, var(--color-border));
    border-radius: 14px;
    background: linear-gradient(
        135deg,
        color-mix(in srgb, var(--color-primary-600) 5%, var(--color-card-bg)),
        var(--color-primary-50)
    );
    box-shadow: none;
}

.current-account > img,
.account-avatar {
    width: 52px;
    height: 52px;
    flex: 0 0 52px;
    border-radius: 50%;
}

.current-account > img {
    object-fit: cover;
}

.account-avatar {
    display: grid;
    place-items: center;
    overflow: hidden;
    color: white;
    font-size: 16px;
    font-weight: 800;
    line-height: 1;
    white-space: nowrap;
    background: linear-gradient(
        135deg,
        var(--color-primary-300),
        var(--color-primary-600)
    );
}

.account-avatar-large {
    width: 56px;
    height: 56px;
    flex: 0 0 56px;
    font-size: 15px;
}

.current-account span,
.current-account strong,
.current-account p {
    display: block;
}

.current-account div > span,
.current-account p {
    color: var(--color-text-tertiary);
    font-size: 11px;
}

.current-account strong {
    margin: 2px 0;
    color: var(--color-text-primary);
}

.avatar-actions {
    display: flex;
    flex: 0 0 auto;
    gap: 8px;
    margin-left: auto;
}

.avatar-actions :deep(.el-button + .el-button) {
    margin-left: 0;
}

.form-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    grid-auto-flow: dense;
    gap: 14px 16px;
    padding: 16px;
    border: 1px solid color-mix(in srgb, var(--color-primary-600) 18%, var(--color-border));
    border-radius: 14px;
    background: color-mix(in srgb, var(--color-primary-600) 5%, var(--color-card-bg));
    margin: 0 20px 8px;
}

.account-field {
    display: grid;
    min-width: 0;
    gap: 7px;
    color: var(--color-text-secondary);
    font-size: 13px;
    font-weight: 600;
}

.account-field .settings-input {
    width: 100%;
    height: 38px;
}

.account-field .settings-input.has-error {
    border-color: var(--color-danger);
}

.account-field .field-error {
    color: var(--color-danger);
    font-size: 12px;
    font-weight: 500;
}

/* === 家庭切换器 === */

.household-switcher {
    margin: 0 20px 10px;
    padding: 14px 16px;
    border: 1px solid color-mix(in srgb, var(--color-primary-600) 18%, var(--color-border));
    border-radius: 14px;
    background: color-mix(in srgb, var(--color-primary-600) 5%, var(--color-card-bg));
}

.household-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;
    color: var(--color-text-secondary);
    font-size: 13px;
    font-weight: 700;
}

.household-create-toggle {
    border: 0;
    color: var(--color-primary-600);
    background: transparent;
    font-size: 12px;
    font-weight: 700;
    cursor: pointer;
}

.household-create-form {
    display: grid;
    gap: 8px;
    margin-bottom: 10px;
    padding: 10px;
    border: 1px dashed var(--color-primary-300);
    border-radius: 12px;
    background: var(--color-primary-50);
}

.household-create-form .settings-input {
    height: 34px;
}

.household-create-actions {
    display: flex;
    justify-content: flex-end;
    gap: 6px;
}

.household-list {
    display: grid;
    gap: 6px;
    max-height: 200px;
    overflow-y: auto;
}

.household-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    width: 100%;
    min-height: 44px;
    padding: 7px 10px;
    border: 1px solid var(--color-border-default);
    border-radius: 10px;
    background: var(--color-card-bg);
    text-align: left;
    cursor: pointer;
    transition: border-color 150ms, background 150ms;
}

.household-item:hover:not(:disabled) {
    border-color: var(--color-primary-400);
    background: var(--color-surface-hover);
}

.household-item:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

.household-item.is-active {
    border-color: var(--color-primary-500);
    background: var(--color-primary-50);
}

.household-item-main {
    display: grid;
    min-width: 0;
    gap: 2px;
}

.household-item-main strong {
    overflow: hidden;
    color: var(--color-text-primary);
    font-size: 13px;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.household-item-main small {
    color: var(--color-text-tertiary);
    font-size: 11px;
}

.household-current {
    flex: 0 0 auto;
    border-radius: 999px;
    padding: 2px 8px;
    color: white;
    background: var(--color-primary-600);
    font-size: 11px;
    font-weight: 800;
}

.household-empty {
    margin: 0;
    padding: 10px 0;
    color: var(--color-text-tertiary);
    font-size: 12px;
}

.address-field {
    grid-column: 1 / -1;
}

/* === 账户弹窗：桌面双栏，避免整窗持续纵向滚动 === */
.account-dialog-layout {
    display: grid;
    height: min(470px, calc(80dvh - 170px));
    min-height: 360px;
    grid-template-columns: 280px minmax(0, 1fr);
    gap: 14px;
}

.account-dialog-sidebar {
    display: grid;
    min-height: 0;
    grid-template-rows: auto minmax(0, 1fr);
    gap: 12px;
    border: 1px solid color-mix(
        in srgb,
        var(--color-primary-600) 12%,
        var(--color-border-subtle)
    );
    border-radius: 16px;
    background: linear-gradient(
        155deg,
        color-mix(in srgb, var(--color-primary-50) 62%, var(--color-card-bg)),
        color-mix(in srgb, var(--color-primary-100) 32%, var(--color-card-bg))
    );
    padding: 10px;
}

.account-dialog-layout .current-account,
.account-dialog-layout .household-switcher,
.account-edit-card {
    margin: 0;
    border-color: color-mix(
        in srgb,
        var(--color-primary-600) 18%,
        var(--color-border)
    );
    background: color-mix(
        in srgb,
        var(--color-card-bg) 96%,
        var(--color-primary-50)
    );
}

.account-dialog-layout .current-account {
    display: grid;
    grid-template-columns: 52px minmax(0, 1fr);
    padding: 14px;
}

.account-dialog-layout .avatar-actions {
    grid-column: 1 / -1;
    width: 100%;
    margin: 2px 0 0;
    padding: 0;
}

.account-dialog-layout .avatar-actions :deep(.base-button) {
    flex: 1 1 0;
}

.account-dialog-layout .household-switcher {
    display: flex;
    min-height: 0;
    flex-direction: column;
    padding: 13px;
}

.account-dialog-layout .household-list {
    min-height: 0;
    max-height: none;
    flex: 1 1 auto;
    padding-right: 3px;
    overscroll-behavior: contain;
    scrollbar-width: thin;
}

.account-edit-card {
    min-width: 0;
    border: 1px solid;
    border-radius: 14px;
    background: linear-gradient(
        145deg,
        var(--color-card-bg) 0%,
        color-mix(in srgb, var(--color-primary-50) 48%, var(--color-card-bg)) 100%
    );
    padding: 16px;
    box-shadow: 0 8px 24px color-mix(
        in srgb,
        var(--color-primary-600) 7%,
        transparent
    );
}

.account-edit-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--color-border-subtle);
}

.account-edit-header > div {
    display: grid;
    gap: 3px;
}

.account-edit-header strong {
    color: var(--color-text-primary);
    font-size: 14px;
}

.account-edit-header small {
    color: var(--color-text-tertiary);
    font-size: 11px;
}

.account-edit-header > span {
    border-radius: 999px;
    background: var(--color-primary-50);
    padding: 3px 8px;
    color: var(--color-primary-700);
    font-size: 10px;
    font-weight: 800;
}

.account-edit-card .form-grid {
    margin: 0;
    border: 0;
    background: transparent;
    padding: 0;
}

.account-edit-card .settings-input,
.create-household-dialog .settings-input {
    background: var(--color-card-bg);
}

.account-edit-card .settings-input:focus,
.create-household-dialog .settings-input:focus {
    border-color: var(--color-primary-500);
    box-shadow: 0 0 0 3px color-mix(
        in srgb,
        var(--color-primary-500) 14%,
        transparent
    );
}

.create-household-dialog {
    display: grid;
    gap: 14px;
    border: 1px solid color-mix(
        in srgb,
        var(--color-primary-600) 14%,
        var(--color-border-subtle)
    );
    border-radius: 14px;
    background: linear-gradient(
        145deg,
        var(--color-card-bg),
        color-mix(in srgb, var(--color-primary-50) 54%, var(--color-card-bg))
    );
    padding: 14px;
}

.create-household-dialog label {
    display: grid;
    gap: 7px;
    color: var(--color-text-secondary);
    font-size: 12px;
    font-weight: 700;
}

.create-household-dialog .settings-input {
    width: 100%;
    height: 40px;
}

.create-dialog-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
}

.create-dialog-footer > div {
    display: flex;
    gap: 10px;
}

@media (max-width: 760px) {
    .account-dialog-layout {
        height: auto;
        min-height: 0;
        grid-template-columns: minmax(0, 1fr);
    }

    .account-dialog-sidebar {
        grid-template-rows: auto auto;
    }

    .account-dialog-layout .household-list {
        max-height: 220px;
    }
}

@media (max-width: 640px) {
    .form-grid {
        grid-template-columns: 1fr;
    }

    .form-grid label {
        grid-column: auto !important;
    }

    .current-account {
        flex-wrap: wrap;
    }

    .avatar-actions {
        width: 100%;
        margin-left: 0;
        padding-left: 66px;
    }
}
</style>
