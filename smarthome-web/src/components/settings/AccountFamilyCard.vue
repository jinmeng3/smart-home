<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { ElButton, ElMessageBox } from "element-plus";
import BaseSmartModal from "../common/BaseSmartModal.vue";
import type { AccountForm } from "../../types/settings";
import SettingsSectionCard from "./SettingsSectionCard.vue";
import "element-plus/theme-chalk/el-message-box.css";

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
const avatarLoadError = ref(false);
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
            class="secondary-button mt-4 w-full"
            type="button"
            @click="openDialog"
        >
            查看与编辑账户信息
        </button>
    </SettingsSectionCard>

    <BaseSmartModal
        v-model="dialogVisible"
        width="620px"
        title="账户与家庭"
        description="查看当前账户信息并管理所属家庭"
        icon="account"
        :close-button-disabled="loading"
    >
        <section class="current-account">
            <img
                v-if="visibleAvatarUrl"
                :src="visibleAvatarUrl"
                :alt="form.name"
                @error="avatarLoadError = true"
            />
            <span v-else class="account-avatar">{{ accountInitial }}</span>
            <div class="min-w-0">
                <span>当前账户</span>
                <strong>{{ form.name || "未命名账户" }}</strong>
                <p>{{ form.email || "未设置邮箱" }}</p>
            </div>
            <div class="avatar-actions">
                <ElButton
                    :disabled="loading"
                    size="small"
                    @click="selectAvatar"
                >
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
                    <ElButton
                        :disabled="loading"
                        @click="dialogVisible = false"
                    >
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
    </BaseSmartModal>
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

.current-account {
    margin: 0;
    padding: 16px 18px;
    border: 1px solid var(--color-primary-200);
    border-radius: 16px;
    background: linear-gradient(
        135deg,
        var(--color-card-bg),
        var(--color-primary-50)
    );
    box-shadow: var(--shadow-card);
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
