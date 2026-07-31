<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { ElButton, ElDialog, ElMessageBox } from "element-plus";
import type { AccountForm } from "../../types/account";
import SettingsSectionCard from "./SettingsSectionCard.vue";
import "element-plus/theme-chalk/el-dialog.css";
import "element-plus/theme-chalk/el-message-box.css";
import "element-plus/theme-chalk/el-overlay.css";

const props = defineProps<{
    form: AccountForm;
    loading: boolean;
    dirty: boolean;
}>();

const emit = defineEmits<{
    deleteAvatar: [];
    save: [];
    uploadAvatar: [file: File];
    updateForm: [form: AccountForm];
}>();

const avatarInput = ref<HTMLInputElement | null>(null);
const dialogVisible = ref(false);
const previewUrl = ref<string | null>(null);
const timezones = [
    "Asia/Shanghai",
    "Asia/Tokyo",
    "Europe/London",
    "America/New_York",
    "UTC",
];

const visibleAvatarUrl = computed(
    () => previewUrl.value ?? props.form.avatarUrl,
);
const accountInitial = computed(() => props.form.name.trim().slice(0, 1));
const householdSummary = computed(
    () =>
        [props.form.householdName, props.form.address]
            .filter(Boolean)
            .join(" · ") || "尚未设置家庭信息",
);

watch(
    () => props.form.avatarUrl,
    () => {
        if (previewUrl.value) {
            URL.revokeObjectURL(previewUrl.value);
            previewUrl.value = null;
        }
    },
);

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

    if (previewUrl.value) {
        URL.revokeObjectURL(previewUrl.value);
    }

    previewUrl.value = URL.createObjectURL(file);
    emit("uploadAvatar", file);
    target.value = "";
};

const deleteAvatar = async () => {
    try {
        await ElMessageBox.confirm("确认删除当前头像？", "删除头像", {
            confirmButtonText: "删除",
            cancelButtonText: "取消",
            type: "warning",
        });
        emit("deleteAvatar");
    } catch {
        // User cancelled.
    }
};
</script>

<template>
    <SettingsSectionCard id="account" icon="♙" title="账户与家庭">
        <div class="account-summary">
            <img
                v-if="visibleAvatarUrl"
                class="h-14 w-14 shrink-0 rounded-full object-cover"
                :src="visibleAvatarUrl"
                :alt="form.name"
            />
            <span
                v-else
                class="grid h-14 w-14 shrink-0 place-items-center rounded-full bg-gradient-to-br from-blue-100 to-blue-600 text-lg font-extrabold text-white"
            >
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
                <span class="mt-1 block truncate text-xs text-[var(--color-text-tertiary)]">
                    {{ householdSummary }}
                </span>
            </div>
        </div>

        <button
            class="secondary-button mt-4 w-full"
            type="button"
            @click="openDialog"
        >
            查看与编辑账户信息
        </button>
    </SettingsSectionCard>

    <ElDialog
        v-model="dialogVisible"
        :close-on-click-modal="!loading"
        :close-on-press-escape="!loading"
        :lock-scroll="true"
        :modal="true"
        :show-close="false"
        append-to-body
        class="account-family-dialog"
        modal-class="settings-dialog-overlay"
        width="620px"
    >
        <template #header>
            <header class="dialog-header">
                <span class="dialog-icon" aria-hidden="true">♙</span>
                <div>
                    <h2>账户与家庭</h2>
                    <p>查看当前账户信息并管理所属家庭</p>
                </div>
                <ElButton
                    aria-label="关闭"
                    class="close-button"
                    :disabled="loading"
                    text
                    @click="dialogVisible = false"
                    >×</ElButton
                >
            </header>
        </template>

        <section class="current-account">
            <img
                v-if="visibleAvatarUrl"
                :src="visibleAvatarUrl"
                :alt="form.name"
            />
            <span v-else class="account-avatar">{{ accountInitial }}</span>
            <div class="min-w-0">
                <span>当前账户</span>
                <strong>{{ form.name || "未命名账户" }}</strong>
                <p>{{ form.email || "未设置邮箱" }}</p>
            </div>
            <div class="avatar-actions">
                <ElButton :disabled="loading" size="small" @click="selectAvatar">
                    上传头像
                </ElButton>
                <ElButton
                    :disabled="loading || !visibleAvatarUrl"
                    size="small"
                    @click="deleteAvatar"
                >
                    删除
                </ElButton>
            </div>
            <input
                ref="avatarInput"
                class="hidden"
                accept="image/jpeg,image/png,image/webp"
                type="file"
                @change="uploadAvatar"
            />
        </section>

        <div class="form-grid">
            <label class="account-field"
                ><span>姓名</span
                ><input
                    class="settings-input"
                    :value="form.name"
                    @input="
                        updateField(
                            'name',
                            ($event.target as HTMLInputElement).value,
                        )
                    "
            /></label>
            <label class="account-field"
                ><span>邮箱</span
                ><input
                    class="settings-input"
                    :value="form.email"
                    @input="
                        updateField(
                            'email',
                            ($event.target as HTMLInputElement).value,
                        )
                    "
            /></label>
            <label class="account-field"
                ><span>家庭名称</span
                ><input
                    class="settings-input"
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

        <template #footer>
            <footer class="dialog-footer">
                <span>{{ dirty ? "有尚未保存的修改" : "账户信息已同步" }}</span>
                <div>
                    <ElButton :disabled="loading" @click="dialogVisible = false">
                        关闭
                    </ElButton>
                    <ElButton
                        :disabled="!dirty"
                        :loading="loading"
                        type="primary"
                        @click="emit('save')"
                    >
                        保存更改
                    </ElButton>
                </div>
            </footer>
        </template>
    </ElDialog>
</template>

<style scoped>
.account-summary,
.current-account {
    display: flex;
    align-items: center;
    gap: 14px;
}

.account-summary > div,
.current-account > div:first-of-type {
    flex: 1;
}

:global(.account-family-dialog) {
    overflow: hidden;
    border: 1px solid var(--color-border-default);
    border-radius: 20px;
    background: var(--color-panel-background);
    box-shadow: 0 24px 70px rgb(15 23 42 / 22%);
}

:global(.settings-dialog-overlay) {
    background: var(--color-overlay);
    backdrop-filter: blur(4px);
}

:global(.account-family-dialog .el-dialog__header),
:global(.account-family-dialog .el-dialog__body),
:global(.account-family-dialog .el-dialog__footer) {
    padding: 0;
}

.dialog-header {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 17px 20px 14px;
    border-bottom: 1px solid var(--color-divider);
    background: linear-gradient(
        135deg,
        var(--color-dialog-header-start),
        var(--color-dialog-header-end)
    );
}

.dialog-icon {
    display: grid;
    width: 36px;
    height: 36px;
    flex: 0 0 36px;
    place-items: center;
    border-radius: 11px;
    color: white;
    background: linear-gradient(
        135deg,
        var(--color-dialog-icon-start),
        var(--color-dialog-icon-end)
    );
}

.dialog-header h2 {
    color: var(--color-text-primary);
    font-size: 17px;
    font-weight: 800;
}

.dialog-header p {
    margin-top: 2px;
    color: var(--color-text-tertiary);
    font-size: 12px;
}

.close-button {
    margin: -4px -6px 0 auto;
    color: var(--color-text-tertiary);
    font-size: 22px;
}

.current-account {
    margin: 16px 20px 0;
    padding: 14px;
    border: 1px solid var(--color-divider);
    border-radius: 14px;
    background: var(--color-workspace-background);
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
    color: white;
    font-size: 18px;
    font-weight: 800;
    background: linear-gradient(135deg, #93c5fd, var(--color-primary-600));
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
    padding: 16px 20px 20px;
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

.address-field {
    grid-column: 1 / -1;
}

.dialog-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 12px 20px;
    border-top: 1px solid var(--color-divider);
    background: var(--color-workspace-background);
}

.dialog-footer > span {
    color: var(--color-text-tertiary);
    font-size: 11px;
}

@media (max-width: 640px) {
    :global(.account-family-dialog) {
        width: calc(100% - 24px) !important;
    }

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
