<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import { ElMessage } from "element-plus";
import BaseButton from "../common/BaseButton.vue";
import BaseSmartModal from "../common/BaseSmartModal.vue";
import ConfirmActionDialog from "../common/ConfirmActionDialog.vue";
import ConfirmEntitySummary from "../common/ConfirmEntitySummary.vue";
import { useSettingsStore } from "../../stores/settings";

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
/** 关闭前未保存时，是否弹确认（仅本地弹窗状态） */
const discardConfirmOpen = ref(false);
const form = reactive<PasswordForm>({
    newPassword: "",
    confirmPassword: "",
});
const showPassword = ref(false);
const passwordUpdatedAt = computed(
    () => settingsStore.securityMeta.passwordUpdatedAt ?? "尚未更新",
);
const trustedDeviceCount = computed(
    () =>
        settingsStore.securityMeta.devices.filter((device) => device.trusted)
            .length,
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
    () =>
        form.newPassword.trim().length > 0 ||
        form.confirmPassword.trim().length > 0,
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
    if (
        form.confirmPassword.length > 0 &&
        form.newPassword !== form.confirmPassword
    ) {
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

const requestClose = () => {
    if (hasChanges.value) {
        discardConfirmOpen.value = true;
        return;
    }
    emit("update:modelValue", false);
};

const confirmBeforeClose = () => {
    if (hasChanges.value) {
        discardConfirmOpen.value = true;
        return false;
    }
    return true;
};

const confirmDiscard = () => {
    discardConfirmOpen.value = false;
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
    <BaseSmartModal
        :model-value="modelValue"
        :before-close="confirmBeforeClose"
        width="medium"
        title="修改密码"
        description="更新当前账户的本地安全记录"
        icon="lock"
        tone="purple"
        body-tone="neutral"
        @update:model-value="emit('update:modelValue', $event)"
    >
        <div class="password-dialog-body">
            <section class="password-card">
                <div class="password-card-header">
                    <div>
                        <strong>密码设置</strong>
                        <span>最少 6 位字符</span>
                    </div>
                    <span
                        class="password-strength-label"
                        :data-tone="strength.tone"
                    >
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
                        <button
                            class="password-toggle"
                            type="button"
                            @click="showPassword = !showPassword"
                        >
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
                    <span
                        :class="[
                            'password-meter-bar',
                            `password-meter-${strength.tone}`,
                        ]"
                        :style="{ width: `${strength.percent}%` }"
                    />
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
                    <BaseButton @click="requestClose">关闭</BaseButton>
                    <BaseButton
                        :disabled="!canSave"
                        variant="primary"
                        @click="savePassword"
                    >
                        保存
                    </BaseButton>
                </div>
            </footer>
        </template>
    </BaseSmartModal>

    <ConfirmActionDialog
        v-if="discardConfirmOpen"
        :model-value="true"
        tone="warning"
        title="放弃修改"
        description="当前密码修改尚未保存，关闭后修改将丢失。"
        confirm-text="关闭"
        cancel-text="继续编辑"
        warning="未保存的密码修改将被丢弃。"
        footer-hint="可返回继续编辑"
        @confirm="confirmDiscard"
        @update:model-value="!$event && (discardConfirmOpen = false)"
    >
        <ConfirmEntitySummary
            icon="lock"
            title="修改密码"
            description="新密码尚未保存"
            color="var(--color-warning)"
        />
    </ConfirmActionDialog>
</template>

<style scoped>
.password-dialog-body {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 240px;
    gap: 18px;
    padding: 0;
}

.password-card,
.password-summary {
    min-width: 0;
    border: 1px solid var(--color-border);
    border-radius: 16px;
    background: var(--color-card-bg);
    box-shadow: var(--shadow-card);
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
    padding-bottom: 12px;
    border-bottom: 1px solid var(--color-border);
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
    color: var(--tone-purple);
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
    border-color: color-mix(in srgb, var(--tone-purple) 28%, var(--color-border));
    background: linear-gradient(
        160deg,
        var(--color-card-bg),
        var(--tone-purple-soft)
    );
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

@media (max-width: 640px) {
    .password-dialog-body {
        grid-template-columns: 1fr;
    }
}
</style>
