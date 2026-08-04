<script setup lang="ts">
import { computed, nextTick, reactive, ref, watch } from "vue";
import { ElButton, ElInput } from "element-plus";
import { useAuthStore } from "../../stores/auth";
import { useSettingsStore } from "../../stores/settings";
import BaseSmartModal from "../common/BaseSmartModal.vue";
import SvgIcon from "../common/SvgIcon.vue";
import { sleep } from "../../utils/async";
import "element-plus/theme-chalk/el-input.css";

type AuthMode = "login" | "register";
type FeedbackType = "error" | "warning" | "success";
type Feedback = { type: FeedbackType; message: string };
type AuthOutcome = "login" | "register" | "logout";

const authStore = useAuthStore();
const settingsStore = useSettingsStore();
const mode = ref<AuthMode>("login");
const submitting = ref(false);
const feedback = ref<Feedback | null>(null);
const shaking = ref(false);
const outcome = ref<AuthOutcome | null>(null);
const accountInput = ref<{ focus: () => void } | null>(null);
const loginForm = reactive({ account: "", password: "" });
const registerForm = reactive({
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
});
const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const title = computed(() =>
    outcome.value
        ? "操作已完成"
        : authStore.isAuthenticated
          ? "账户已登录"
          : mode.value === "login"
            ? "登录 Orion Home"
            : "注册 Orion Home",
);
const description = computed(() =>
    outcome.value
        ? "Orion Home 已安全更新你的账户状态"
        : authStore.isAuthenticated
          ? "你可以继续使用当前账户，或切换到其他 Orion Home 账户"
          : mode.value === "login"
            ? "登录后同步家庭、会话和智能助手配置"
            : "创建账户，开始管理你的智能家庭",
);
const footerHint = computed(() =>
    authStore.isAuthenticated
        ? "当前账户会继续用于设备同步与智能对话"
        : mode.value === "login"
          ? "账户凭据仅用于安全登录"
          : "注册即表示同意账户安全规范",
);
const username = computed(
    () => settingsStore.settings.account.username.trim() || "Orion Home 用户",
);
const avatarUrl = computed(() => settingsStore.settings.account.avatarUrl);
const accountInitial = computed(() => username.value.slice(0, 1).toUpperCase());
const outcomeContent = computed(() => {
    const content = {
        login: {
            title: "欢迎回来",
            message: "登录成功，正在同步家庭设备与智能助手配置",
        },
        register: {
            title: "账户创建成功",
            message: "你的 Orion Home 空间已经准备就绪",
        },
        logout: {
            title: "已安全登出",
            message: "本机登录凭证已清除，期待与你再次见面",
        },
    };
    return outcome.value ? content[outcome.value] : null;
});

const selectMode = (nextMode: AuthMode) => {
    if (submitting.value || authStore.isAuthenticated) return;
    feedback.value = null;
    mode.value = nextMode;

    if (nextMode === "login") {
        void nextTick(() => accountInput.value?.focus());
    }
};

const validateRegisterForm = (): string | null => {
    if (!registerForm.username.trim()) return "请输入用户名";
    if (!emailPattern.test(registerForm.email.trim()))
        return "请输入有效的邮箱地址";
    if (registerForm.password.length < 6) return "密码至少需要 6 位字符";
    if (registerForm.password !== registerForm.confirmPassword)
        return "两次输入的密码不一致";
    return null;
};

const showFeedback = (type: FeedbackType, message: string, shake = false) => {
    feedback.value = { type, message };
    if (shake) {
        shaking.value = false;
        void nextTick(() => {
            shaking.value = true;
        });
    }
};

const submit = async () => {
    feedback.value = null;
    if (mode.value === "login") {
        if (!loginForm.account.trim() || !loginForm.password) {
            showFeedback("warning", "请输入账号和密码", true);
            return;
        }
    } else {
        const message = validateRegisterForm();
        if (message) {
            showFeedback("warning", message, true);
            return;
        }
    }

    submitting.value = true;
    try {
        if (mode.value === "login") {
            await authStore.login(
                {
                    account: loginForm.account.trim(),
                    password: loginForm.password,
                },
                false,
            );
            loginForm.password = "";
            outcome.value = "login";
            await sleep(1200);
            authStore.loginVisible = false;
        } else {
            await authStore.register(
                {
                    username: registerForm.username.trim(),
                    email: registerForm.email.trim(),
                    password: registerForm.password,
                },
                false,
            );
            registerForm.password = "";
            registerForm.confirmPassword = "";
            outcome.value = "register";
            await sleep(1200);
            authStore.loginVisible = false;
        }
        // 登录凭证已经由 Store 保存，异步刷新账户资料即可，无需整页重载。
        void settingsStore.loadAccountHome().catch(() => undefined);
    } catch (error) {
        showFeedback(
            "error",
            error instanceof Error
                ? error.message
                : mode.value === "login"
                  ? "登录失败"
                  : "注册失败",
            true,
        );
    } finally {
        submitting.value = false;
    }
};

watch(
    () => authStore.loginVisible,
    (visible) => {
        if (!visible) return;
        outcome.value = null;
        if (authStore.isAuthenticated) return;
        feedback.value = null;
        mode.value = "login";
        void nextTick(() => accountInput.value?.focus());
    },
);

watch([loginForm, registerForm], () => {
    if (feedback.value) feedback.value = null;
});

const logout = async () => {
    submitting.value = true;
    try {
        await authStore.logout(false);
        outcome.value = "logout";
        await sleep(1200);
        authStore.loginVisible = false;
    } catch (error) {
        showFeedback(
            "error",
            error instanceof Error ? error.message : "登出失败",
            true,
        );
    } finally {
        submitting.value = false;
    }
};
</script>

<template>
    <BaseSmartModal
        v-model="authStore.loginVisible"
        :closable="!submitting"
        width="560px"
    >
        <template #header>
            <header class="dialog-header">
                <span class="dialog-icon" aria-hidden="true">
                    <SvgIcon name="account" size="sm" />
                </span>
                <div>
                    <h2>{{ title }}</h2>
                    <p>{{ description }}</p>
                </div>
                <ElButton
                    aria-label="关闭"
                    class="close-button"
                    :disabled="submitting"
                    text
                    @click="authStore.loginVisible = false"
                    >×</ElButton
                >
            </header>
        </template>

        <section v-if="outcomeContent" class="auth-result" role="status">
            <span class="result-mark" aria-hidden="true">✓</span>
            <strong>{{ outcomeContent.title }}</strong>
            <p>{{ outcomeContent.message }}</p>
            <small>账户状态已通过安全连接更新</small>
        </section>

        <div
            v-else-if="feedback"
            :class="['auth-feedback', `is-${feedback.type}`]"
            role="alert"
        >
            <span class="feedback-icon" aria-hidden="true">
                {{
                    feedback.type === "error"
                        ? "!"
                        : feedback.type === "success"
                          ? "✓"
                          : "⚠"
                }}
            </span>
            <p>{{ feedback.message }}</p>
        </div>

        <section
            v-if="!outcome && authStore.isAuthenticated"
            class="current-account"
        >
            <img
                v-if="avatarUrl"
                class="account-avatar"
                :src="avatarUrl"
                alt=""
            />
            <div v-else class="account-avatar account-avatar-fallback">
                {{ accountInitial }}
            </div>
            <div>
                <strong>{{ username }}</strong>
                <p>当前账户已完成登录，家庭设备与智能对话已同步。</p>
            </div>
        </section>

        <!-- 使用单一根节点，避免通用弹窗把标签栏和表单自动排成双栏。 -->
        <div v-if="!outcome && !authStore.isAuthenticated" class="auth-content">
            <div class="auth-assurance">
                <span aria-hidden="true">✓</span>
                <p>安全连接已启用，账户凭据仅用于 Orion Home 身份认证</p>
            </div>
            <nav class="auth-tabs" aria-label="账户操作">
                <button
                    :class="{ active: mode === 'login' }"
                    type="button"
                    @click="selectMode('login')"
                >
                    登录
                </button>
                <button
                    :class="{ active: mode === 'register' }"
                    type="button"
                    @click="selectMode('register')"
                >
                    注册
                </button>
            </nav>

            <form
                class="login-form"
                :class="{ shake: shaking }"
                @submit.prevent="submit"
            >
                <template v-if="mode === 'login'">
                    <label class="login-field">
                        <span>邮箱</span>
                        <ElInput
                            ref="accountInput"
                            v-model="loginForm.account"
                            autocomplete="username"
                            placeholder="name@example.com"
                            type="email"
                        />
                    </label>
                    <label class="login-field">
                        <span>密码</span>
                        <ElInput
                            v-model="loginForm.password"
                            autocomplete="current-password"
                            placeholder="请输入密码"
                            show-password
                            type="password"
                        />
                    </label>
                </template>
                <template v-else>
                    <label class="login-field"
                        ><span>用户名</span
                        ><ElInput
                            v-model="registerForm.username"
                            autocomplete="username"
                            placeholder="请输入用户名"
                    /></label>
                    <label class="login-field"
                        ><span>邮箱</span
                        ><ElInput
                            v-model="registerForm.email"
                            autocomplete="email"
                            placeholder="name@example.com"
                            type="email"
                    /></label>
                    <div class="password-grid">
                        <label class="login-field"
                            ><span>密码</span
                            ><ElInput
                                v-model="registerForm.password"
                                autocomplete="new-password"
                                placeholder="至少 6 位字符"
                                show-password
                                type="password"
                        /></label>
                        <label class="login-field"
                            ><span>确认密码</span
                            ><ElInput
                                v-model="registerForm.confirmPassword"
                                autocomplete="new-password"
                                placeholder="再次输入密码"
                                show-password
                                type="password"
                        /></label>
                    </div>
                </template>
            </form>
        </div>

        <template #footer>
            <footer v-if="!outcome" class="dialog-footer">
                <span>{{ footerHint }}</span>
                <div>
                    <ElButton
                        :disabled="submitting"
                        @click="authStore.loginVisible = false"
                        >取消</ElButton
                    >
                    <ElButton
                        v-if="authStore.isAuthenticated"
                        :loading="submitting"
                        type="primary"
                        @click="logout"
                        >登出</ElButton
                    >
                    <ElButton
                        v-if="!authStore.isAuthenticated"
                        :loading="submitting"
                        type="primary"
                        @click="submit"
                        >{{ mode === "login" ? "登录" : "创建账户" }}</ElButton
                    >
                </div>
            </footer>
        </template>
    </BaseSmartModal>
</template>

<style scoped>
.auth-result {
    display: grid;
    min-height: 238px;
    place-items: center;
    align-content: center;
    border: 1px solid
        color-mix(in srgb, var(--color-success-border) 74%, transparent);
    border-radius: 18px;
    background:
        radial-gradient(
            circle at 50% 15%,
            var(--color-success-soft),
            transparent 48%
        ),
        linear-gradient(
            180deg,
            var(--color-card-bg),
            var(--color-surface-subtle)
        );
    padding: 28px;
    text-align: center;
    animation: auth-result-in 360ms var(--motion-ease) both;
}

.result-mark {
    display: grid;
    width: 64px;
    height: 64px;
    margin-bottom: 16px;
    place-items: center;
    border-radius: 50%;
    background: linear-gradient(
        135deg,
        var(--color-success),
        var(--color-teal-600)
    );
    box-shadow: 0 12px 30px
        color-mix(in srgb, var(--color-success) 24%, transparent);
    color: var(--color-text-on-primary);
    font-size: 30px;
    font-weight: 900;
}

.auth-result strong {
    color: var(--color-text-primary);
    font-size: 20px;
    font-weight: 900;
}

.auth-result p {
    margin: 8px 0 0;
    color: var(--color-text-secondary);
    font-size: 14px;
    line-height: 1.6;
}

.auth-result small {
    margin-top: 18px;
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 700;
}

@keyframes auth-result-in {
    from {
        opacity: 0;
        transform: translateY(8px) scale(0.98);
    }
    to {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
}

.auth-tabs {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 6px;
    margin-bottom: 14px;
    padding: 5px;
    border: 1px solid var(--color-border-subtle);
    border-radius: 14px;
    background: color-mix(
        in srgb,
        var(--color-surface-subtle) 72%,
        transparent
    );
}

.auth-content {
    display: grid;
    min-width: 0;
}

.auth-assurance {
    display: flex;
    align-items: center;
    gap: 9px;
    margin-bottom: 14px;
    border: 1px solid
        color-mix(in srgb, var(--color-teal-border) 58%, transparent);
    border-radius: 12px;
    background: color-mix(in srgb, var(--color-teal-soft) 68%, transparent);
    padding: 10px 13px;
    color: var(--color-text-secondary);
}

.auth-assurance span {
    display: grid;
    width: 20px;
    height: 20px;
    flex: 0 0 20px;
    place-items: center;
    border-radius: 50%;
    background: color-mix(
        in srgb,
        var(--color-teal-600) 82%,
        var(--color-primary-500)
    );
    color: var(--color-text-on-primary);
    font-size: 12px;
    font-weight: 900;
}

.auth-assurance p {
    margin: 0;
    font-size: 12px;
    font-weight: 700;
    line-height: 1.5;
}

.auth-tabs button {
    height: 38px;
    border: 0;
    border-radius: 10px;
    color: var(--color-text-tertiary);
    font-weight: 700;
    background: transparent;
    transition:
        color 160ms var(--motion-ease),
        background-color 160ms var(--motion-ease),
        box-shadow 160ms var(--motion-ease);
}

.auth-tabs button:not(.active):hover {
    color: var(--color-primary-700);
    background: color-mix(in srgb, var(--color-primary-50) 58%, transparent);
}

.auth-tabs button.active {
    color: var(--color-primary-700);
    background: color-mix(
        in srgb,
        var(--color-card-bg) 82%,
        var(--color-primary-50)
    );
    box-shadow:
        inset 0 0 0 1px
            color-mix(in srgb, var(--color-primary-200) 70%, transparent),
        0 6px 18px rgb(15 23 42 / 6%);
}

.dialog-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
}

.dialog-footer > span {
    margin-right: auto;
    color: var(--color-text-tertiary);
    font-size: 13px;
    text-align: left;
}

.dialog-footer > div {
    display: flex;
    flex-shrink: 0;
}

.current-account {
    display: flex;
    align-items: center;
    gap: 14px;
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

.current-account strong {
    display: block;
    color: var(--color-text-primary);
    font-size: 16px;
    font-weight: 800;
}

.current-account p {
    margin-top: 4px;
    color: var(--color-text-secondary);
    font-size: 13px;
}

.account-avatar {
    width: 48px;
    height: 48px;
    flex: 0 0 48px;
    border-radius: 50%;
    object-fit: cover;
    overflow: hidden;
    line-height: 1;
    white-space: nowrap;
}

.account-avatar-fallback {
    display: grid;
    place-items: center;
    color: var(--color-text-on-primary);
    font-size: 14px;
    font-weight: 800;
    background: linear-gradient(
        135deg,
        var(--color-primary-200),
        var(--color-primary-600)
    );
}

.login-form {
    display: grid;
    gap: 16px;
    border: 1px solid
        color-mix(in srgb, var(--color-border-subtle) 64%, transparent);
    border-radius: 16px;
    background: linear-gradient(
        180deg,
        color-mix(in srgb, var(--color-card-bg) 86%, transparent),
        color-mix(in srgb, var(--color-surface-subtle) 42%, transparent)
    );
    padding: 16px;
}

.login-form.shake {
    animation: warning-shake 420ms var(--motion-ease) both;
}

.auth-feedback {
    display: flex;
    align-items: center;
    gap: 9px;
    border-radius: 12px;
    padding: 10px 13px;
    animation: auth-feedback-in 220ms var(--motion-ease) both;
}

.auth-feedback p {
    margin: 0;
    font-size: 13px;
    font-weight: 700;
    line-height: 1.5;
}

.feedback-icon {
    display: grid;
    width: 20px;
    height: 20px;
    flex: 0 0 20px;
    place-items: center;
    border-radius: 50%;
    font-size: 12px;
    font-weight: 900;
}

.auth-feedback.is-error {
    color: var(--color-danger);
    background: var(--color-danger-soft);
    border: 1px solid var(--color-danger-border);
}

.auth-feedback.is-error .feedback-icon {
    color: var(--color-text-on-primary);
    background: var(--color-danger);
}

.auth-feedback.is-warning {
    color: var(--color-warning);
    background: var(--color-warning-soft);
    border: 1px solid var(--color-warning-border);
}

.auth-feedback.is-warning .feedback-icon {
    color: var(--color-text-on-primary);
    background: var(--color-warning);
}

.auth-feedback.is-success {
    color: var(--color-success);
    background: var(--color-success-soft);
    border: 1px solid var(--color-success-border);
}

.auth-feedback.is-success .feedback-icon {
    color: var(--color-text-on-primary);
    background: var(--color-success);
}

@keyframes auth-feedback-in {
    from {
        opacity: 0;
        transform: translateY(-4px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.login-field {
    display: grid;
    gap: 8px;
    margin: 0 !important;
}
.login-field > span {
    color: var(--color-text-tertiary);
    font-size: 13px;
    font-weight: 800;
}
.password-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 16px;
}

:deep(.login-field .el-input__wrapper) {
    min-height: 44px;
    border-radius: 12px;
    padding: 0 14px;
    border: 1px solid
        color-mix(in srgb, var(--color-border-default) 76%, transparent);
    background: color-mix(
        in srgb,
        var(--color-card-bg) 84%,
        var(--color-surface-subtle)
    );
    box-shadow: inset 0 1px 0 rgb(255 255 255 / 28%);
    transition:
        border-color 160ms var(--motion-ease),
        box-shadow 160ms var(--motion-ease),
        background-color 160ms var(--motion-ease);
}

:deep(.login-field .el-input__wrapper:hover) {
    border-color: color-mix(
        in srgb,
        var(--color-border-strong) 86%,
        transparent
    );
    background: color-mix(
        in srgb,
        var(--color-card-bg) 78%,
        var(--color-primary-50)
    );
}

:deep(.login-field .el-input__wrapper.is-focus) {
    border-color: color-mix(in srgb, var(--color-primary-500) 84%, transparent);
    background: var(--color-card-bg);
    box-shadow:
        inset 0 1px 0 rgb(255 255 255 / 34%),
        0 0 0 3px color-mix(in srgb, var(--color-focus-ring) 62%, transparent);
}

:deep(.login-field .el-input__inner) {
    color: var(--color-text-primary);
    font-size: 14px;
    font-weight: 600;
}

:deep(.login-field .el-input__inner::placeholder) {
    color: color-mix(in srgb, var(--color-text-tertiary) 62%, transparent);
    font-weight: 500;
}

.dialog-header {
    border-bottom-color: var(--color-border) !important;
    background: linear-gradient(
        135deg,
        var(--color-card-bg),
        color-mix(in srgb, var(--color-primary-50) 52%, var(--color-card-bg))
    ) !important;
}

.dialog-icon {
    color: var(--color-text-on-primary) !important;
    background: linear-gradient(
        135deg,
        var(--color-primary-600),
        color-mix(in srgb, var(--color-primary-500) 70%, var(--color-teal-600))
    ) !important;
    box-shadow: 0 8px 20px
        color-mix(in srgb, var(--color-focus-ring) 72%, transparent);
}

.dialog-footer :deep(.el-button--primary) {
    border-color: var(--color-primary-600) !important;
    background: linear-gradient(
        135deg,
        var(--color-primary-600),
        var(--color-primary-500)
    ) !important;
    color: var(--color-text-on-primary) !important;
}

@media (max-width: 640px) {
    .password-grid {
        grid-template-columns: 1fr;
    }
}
</style>
