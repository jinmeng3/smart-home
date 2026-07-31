<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import { ElButton, ElDialog, ElMessage, ElMessageBox } from "element-plus";
import { useSettingsStore } from "../../stores/settings";
import "element-plus/theme-chalk/el-dialog.css";
import "element-plus/theme-chalk/el-message-box.css";
import "element-plus/theme-chalk/el-overlay.css";

interface PasswordForm {
    newPassword: string;
    confirmPassword: string;
}

const props = defineProps<{
    modelValue: boolean;
}>();

const emit = defineEmits<{
    "update:modelValue": [value: boolean];
    saved: [];
}>();

const settingsStore = useSettingsStore();
const form = reactive<PasswordForm>({
    newPassword: "",
    confirmPassword: "",
});
const showPassword = ref(false);
const passwordUpdatedAt = computed(
    () => settingsStore.securityMeta.passwordUpdatedAt ?? "尚未更新",
);
const trustedDeviceCount = computed(
    () => settingsStore.securityMeta.devices.filter((device) => device.trusted).length,
);
const strength = computed(() => {
    const value = form.newPassword;
    if (!value) {
        return { label: "未输入", percent: 0, tone: "neutral" as const };
    }

    let score = 0;
    if (value.length >= 6) score += 1;
    if (value.length >= 10) score += 1;
    if (/[a-z]/.test(value) && /[A-Z]/.test(value)) score += 1;
    if (/\d/.test(value)) score += 1;
    if (/[^a-zA-Z0-9]/.test(value)) score += 1;

    if (score <= 1) {
        return { label: "弱", percent: 33, tone: "weak" as const };
    }
    if (score <= 3) {
        return { label: "中", percent: 66, tone: "medium" as const };
    }
    return { label: "强", percent: 100, tone: "strong" as const };
});
const hasChanges = computed(
    () => form.newPassword.trim().length > 0 || form.confirmPassword.trim().length > 0,
);
const canSave = computed(
    () =>
        form.newPassword.length >= 6 &&
        form.newPassword === form.confirmPassword,
);
const passwordError = computed(() => {
    if (!hasChanges.value) {
        return "";
    }
    if (form.newPassword.length > 0 && form.newPassword.length < 6) {
        return "密码至少 6 位字符";
    }
    if (form.confirmPassword.length > 0 && form.newPassword !== form.confirmPassword) {
        return "两次输入的密码不一致";
    }
    return "";
});

const resetForm = () => {
    form.newPassword = "";
    form.confirmPassword = "";
};

const openDialog = () => {
    resetForm();
    showPassword.value = false;
};

watch(
    () => props.modelValue,
    (visible) => {
        if (visible) {
            openDialog();
        }
    },
    { immediate: true },
);

const requestClose = async () => {
    if (hasChanges.value) {
        try {
            await ElMessageBox.confirm(
                "当前修改尚未保存，确定关闭吗？",
                "放弃修改",
                {
                    confirmButtonText: "关闭",
                    cancelButtonText: "继续编辑",
                    type: "warning",
                },
            );
        } catch {
            return;
        }
    }

    emit("update:modelValue", false);
};

const handleBeforeClose = async (done: () => void) => {
    if (hasChanges.value) {
        try {
            await ElMessageBox.confirm(
                "当前修改尚未保存，确定关闭吗？",
                "放弃修改",
                {
                    confirmButtonText: "关闭",
                    cancelButtonText: "继续编辑",
                    type: "warning",
                },
            );
        } catch {
            return;
        }
    }

    done();
    emit("update:modelValue", false);
};

const savePassword = async () => {
    if (form.newPassword.length < 6) {
        ElMessage.warning("密码至少 6 位字符");
        return;
    }

    if (form.newPassword !== form.confirmPassword) {
        ElMessage.warning("两次输入的密码不一致");
        return;
    }

    settingsStore.changeLocalPassword();
    emit("saved");
    emit("update:modelValue", false);
    ElMessage.success("密码已更新");
};
</script>

<template>
    <ElDialog
        :model-value="modelValue"
        :close-on-click-modal="true"
        :close-on-press-escape="true"
        :lock-scroll="true"
        :modal="true"
        :show-close="false"
        :before-close="handleBeforeClose"
        append-to-body
        class="account-family-dialog password-dialog"
        modal-class="settings-dialog-overlay"
        width="680px"
        @update:model-value="emit('update:modelValue', $event)"
    >
        <template #header>
            <header class="dialog-header">
                <span class="dialog-icon" aria-hidden="true">🔒</span>
                <div>
                    <h2>修改密码</h2>
                    <p>更新当前账户的本地安全记录</p>
                </div>
                <ElButton aria-label="关闭" class="close-button" text @click="requestClose">
                    ×
                </ElButton>
            </header>
        </template>

        <div class="password-dialog-body">
            <section class="password-card">
                <div class="password-card-header">
                    <div>
                        <strong>密码设置</strong>
                        <span>最少 6 位字符</span>
                    </div>
                    <span class="password-strength-label" :data-tone="strength.tone">
                        {{ strength.label }}
                    </span>
                </div>

                <label class="password-field">
                    <span>新密码</span>
                    <div class="password-input-shell">
                        <input
                            v-model="form.newPassword"
                            :type="showPassword ? 'text' : 'password'"
                            class="settings-input password-input"
                            placeholder="输入新密码"
                        />
                    <button class="password-toggle" type="button" @click="showPassword = !showPassword">
                        {{ showPassword ? "隐藏" : "显示" }}
                    </button>
                    </div>
                </label>

                <label class="password-field">
                    <span>确认密码</span>
                    <input
                        v-model="form.confirmPassword"
                        :type="showPassword ? 'text' : 'password'"
                        class="settings-input password-input"
                        placeholder="再次输入"
                    />
                </label>

                <div class="password-meter" aria-hidden="true">
                    <span :class="['password-meter-bar', `password-meter-${strength.tone}`]" :style="{ width: `${strength.percent}%` }" />
                </div>

                <p v-if="passwordError" class="password-error">
                    {{ passwordError }}
                </p>

                <ul class="password-rules">
                    <li>最少 6 位字符</li>
                    <li>两次密码必须一致</li>
                    <li>输入错误会实时提示</li>
                </ul>
            </section>

            <aside class="password-summary">
                <div class="password-summary-item">
                    <span>更新时间</span>
                    <strong>{{ passwordUpdatedAt }}</strong>
                </div>
                <div class="password-summary-item">
                    <span>双重认证</span>
                    <strong>已开启</strong>
                </div>
                <div class="password-summary-item">
                    <span>可信设备</span>
                    <strong>{{ trustedDeviceCount }} 台</strong>
                </div>
                <p>修改后仅更新本地安全记录，不请求后端。</p>
            </aside>
        </div>

        <template #footer>
            <footer class="dialog-footer">
                <span>修改结果只会保存在本地</span>
                <div>
                    <ElButton @click="requestClose">关闭</ElButton>
                    <ElButton :disabled="!canSave" type="primary" @click="savePassword">
                        保存
                    </ElButton>
                </div>
            </footer>
        </template>
    </ElDialog>
</template>

<style scoped>
:global(.password-dialog) {
    display: flex;
    max-height: calc(100vh - 48px);
    flex-direction: column;
    overflow: hidden;
    border: 1px solid var(--color-border-default);
    border-radius: 20px;
    background: var(--color-panel-background);
    box-shadow: 0 24px 70px rgb(15 23 42 / 22%);
}

:global(.password-dialog .el-dialog__header),
:global(.password-dialog .el-dialog__body),
:global(.password-dialog .el-dialog__footer) {
    padding: 0;
}

:global(.password-dialog .el-dialog__body) {
    min-height: 0;
    overflow-y: auto;
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
    font-size: 18px;
    background: linear-gradient(
        135deg,
        var(--color-dialog-icon-start),
        var(--color-dialog-icon-end)
    );
    box-shadow: 0 8px 20px rgb(59 130 246 / 24%);
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

.password-dialog-body {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 240px;
    gap: 16px;
    padding: 16px 20px 18px;
}

.password-card,
.password-summary {
    min-width: 0;
    border: 1px solid var(--color-border-default);
    border-radius: 16px;
    background: var(--color-workspace-background);
}

.password-card {
    padding: 16px;
}

.password-card-header {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 16px;
}

.password-card-header strong {
    display: block;
    color: var(--color-text-primary);
    font-size: 15px;
    font-weight: 800;
}

.password-card-header span {
    color: var(--color-text-tertiary);
    font-size: 12px;
}

.password-strength-label {
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 700;
}

.password-strength-label[data-tone="weak"] {
    color: var(--color-danger);
}

.password-strength-label[data-tone="medium"] {
    color: var(--color-warning);
}

.password-strength-label[data-tone="strong"] {
    color: var(--color-success);
}

.password-field {
    display: grid;
    gap: 6px;
    margin-bottom: 12px;
}

.password-field span {
    color: var(--color-text-secondary);
    font-size: 13px;
    font-weight: 600;
}

.password-input-shell {
    position: relative;
}

.password-input {
    width: 100%;
    padding-right: 72px;
}

.password-toggle {
    position: absolute;
    top: 50%;
    right: 10px;
    translate: 0 -50%;
    color: var(--color-primary-700);
    font-size: 12px;
    font-weight: 700;
}

.password-meter {
    height: 6px;
    overflow: hidden;
    border-radius: 999px;
    background: var(--color-surface-subtle);
}

.password-meter-bar {
    display: block;
    height: 100%;
    border-radius: inherit;
    transition: width 160ms ease;
}

.password-meter-neutral {
    background: var(--color-border-default);
}

.password-meter-weak {
    background: var(--color-danger);
}

.password-meter-medium {
    background: var(--color-warning);
}

.password-meter-strong {
    background: var(--color-success);
}

.password-error {
    margin-top: 10px;
    color: var(--color-danger);
    font-size: 12px;
    font-weight: 600;
}

.password-rules {
    margin-top: 12px;
    padding-left: 18px;
    color: var(--color-text-tertiary);
    font-size: 12px;
    line-height: 1.6;
}

.password-summary {
    display: grid;
    gap: 12px;
    align-content: start;
    padding: 16px;
}

.password-summary-item {
    display: grid;
    gap: 4px;
}

.password-summary-item span {
    color: var(--color-text-tertiary);
    font-size: 12px;
}

.password-summary-item strong {
    color: var(--color-text-primary);
    font-size: 14px;
    font-weight: 800;
}

.password-summary p {
    color: var(--color-text-tertiary);
    font-size: 12px;
    line-height: 1.5;
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

.dialog-footer > div {
    display: flex;
    gap: 8px;
}

@media (max-width: 640px) {
    :global(.password-dialog) {
        width: calc(100% - 24px) !important;
    }

    .password-dialog-body {
        grid-template-columns: 1fr;
    }

    .dialog-footer {
        align-items: stretch;
        flex-direction: column;
    }

    .dialog-footer > div {
        justify-content: flex-end;
    }
}
</style>
