<script setup lang="ts">
import { computed, nextTick, reactive, ref, watch } from "vue";
import { ElButton, ElInput, ElMessage } from "element-plus";
import { useAuthStore } from "../../stores/auth";
import { useSettingsStore } from "../../stores/settings";
import BaseSmartModal from "../common/BaseSmartModal.vue";
import SvgIcon from "../common/SvgIcon.vue";
import "element-plus/theme-chalk/el-input.css";
import "element-plus/theme-chalk/el-message.css";

type AuthMode = "login" | "register";

const authStore = useAuthStore();
const settingsStore = useSettingsStore();
const mode = ref<AuthMode>("login");
const submitting = ref(false);
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
    authStore.isAuthenticated
        ? "账户已登录"
        : mode.value === "login"
          ? "登录 Orion Home"
          : "注册 Orion Home",
);
const description = computed(() =>
    authStore.isAuthenticated
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

const selectMode = (nextMode: AuthMode) => {
    if (submitting.value || authStore.isAuthenticated) return;
    mode.value = nextMode;

    if (nextMode === "login") {
        void nextTick(() => accountInput.value?.focus());
    }
};

const validateRegisterForm = () => {
    if (!registerForm.username.trim()) {
        ElMessage.warning("请输入用户名");
        return false;
    }
    if (!emailPattern.test(registerForm.email.trim())) {
        ElMessage.warning("请输入有效的邮箱地址");
        return false;
    }
    if (registerForm.password.length < 6) {
        ElMessage.warning("密码至少需要 6 位字符");
        return false;
    }
    if (registerForm.password !== registerForm.confirmPassword) {
        ElMessage.warning("两次输入的密码不一致");
        return false;
    }
    return true;
};

const submit = async () => {
    if (mode.value === "login" && (!loginForm.account.trim() || !loginForm.password)) {
        ElMessage.warning("请输入账号和密码");
        return;
    }
    if (mode.value === "register" && !validateRegisterForm()) return;

    submitting.value = true;
    try {
        if (mode.value === "login") {
            await authStore.login({
                account: loginForm.account.trim(),
                password: loginForm.password,
            });
            loginForm.password = "";
            ElMessage.success("登录成功");
        } else {
            await authStore.register({
                username: registerForm.username.trim(),
                email: registerForm.email.trim(),
                password: registerForm.password,
            });
            registerForm.password = "";
            registerForm.confirmPassword = "";
            ElMessage.success("注册成功");
        }
        // 登录凭证已经由 Store 保存，异步刷新账户资料即可，无需整页重载。
        void settingsStore.loadAccountHome().catch(() => undefined);
    } catch (error) {
        ElMessage.error(
            error instanceof Error
                ? error.message
                : mode.value === "login"
                  ? "登录失败"
                  : "注册失败",
        );
    } finally {
        submitting.value = false;
    }
};

watch(
    () => authStore.loginVisible,
    (visible) => {
        if (!visible || authStore.isAuthenticated) return;
        mode.value = "login";
        void nextTick(() => accountInput.value?.focus());
    },
);

const logout = async () => {
    submitting.value = true;
    try {
        await authStore.logout();
        ElMessage.success("已登出");
    } catch (error) {
        ElMessage.error(error instanceof Error ? error.message : "登出失败");
    } finally {
        submitting.value = false;
    }
};
</script>

<template>
    <BaseSmartModal
        v-model="authStore.loginVisible"
        :closable="!submitting"
        class="login-dialog"
        width="560px"
    >
        <template #header>
            <header class="dialog-header">
                <span class="dialog-icon" aria-hidden="true">
                    <SvgIcon name="account" size="sm" />
                </span>
                <div><h2>{{ title }}</h2><p>{{ description }}</p></div>
                <ElButton
                    aria-label="关闭"
                    class="close-button"
                    :disabled="submitting"
                    text
                    @click="authStore.loginVisible = false"
                >×</ElButton>
            </header>
        </template>

        <section v-if="authStore.isAuthenticated" class="current-account">
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
        <div v-if="!authStore.isAuthenticated" class="auth-content">
            <nav class="auth-tabs" aria-label="账户操作">
                <button :class="{ active: mode === 'login' }" type="button" @click="selectMode('login')">登录</button>
                <button :class="{ active: mode === 'register' }" type="button" @click="selectMode('register')">注册</button>
            </nav>

            <form class="login-form" @submit.prevent="submit">
                <template v-if="mode === 'login'">
                    <label class="login-field">
                        <span>邮箱</span>
                        <ElInput ref="accountInput" v-model="loginForm.account" autocomplete="username" placeholder="name@example.com" type="email" />
                    </label>
                    <label class="login-field">
                        <span>密码</span>
                        <ElInput v-model="loginForm.password" autocomplete="current-password" placeholder="请输入密码" show-password type="password" />
                    </label>
                </template>
                <template v-else>
                    <label class="login-field"><span>用户名</span><ElInput v-model="registerForm.username" autocomplete="username" placeholder="请输入用户名" /></label>
                    <label class="login-field"><span>邮箱</span><ElInput v-model="registerForm.email" autocomplete="email" placeholder="name@example.com" type="email" /></label>
                    <div class="password-grid">
                        <label class="login-field"><span>密码</span><ElInput v-model="registerForm.password" autocomplete="new-password" placeholder="至少 6 位字符" show-password type="password" /></label>
                        <label class="login-field"><span>确认密码</span><ElInput v-model="registerForm.confirmPassword" autocomplete="new-password" placeholder="再次输入密码" show-password type="password" /></label>
                    </div>
                </template>
            </form>
        </div>

        <template #footer>
            <footer class="dialog-footer">
                <span>{{ footerHint }}</span>
                <div>
                    <ElButton :disabled="submitting" @click="authStore.loginVisible = false">取消</ElButton>
                    <ElButton v-if="authStore.isAuthenticated" :loading="submitting" type="primary" @click="logout">登出</ElButton>
                    <ElButton v-if="!authStore.isAuthenticated" :loading="submitting" type="primary" @click="submit">{{ mode === "login" ? "登录" : "创建账户" }}</ElButton>
                </div>
            </footer>
        </template>
    </BaseSmartModal>
</template>

<style scoped>
.auth-tabs {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 4px;
    margin-bottom: 20px;
    padding: 4px;
    border: 1px solid var(--color-border-default);
    border-radius: 12px;
    background: #f8fafc;
}

.auth-content {
    display: grid;
    min-width: 0;
}

.auth-tabs button {
    height: 38px;
    border: 0;
    border-radius: 9px;
    color: var(--color-text-tertiary);
    font-weight: 700;
    background: transparent;
}

.auth-tabs button.active {
    color: var(--color-primary-700);
    background: #fff;
    box-shadow: 0 2px 8px rgb(15 23 42 / 8%);
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
    margin-bottom: 18px;
    padding: 16px;
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
    color: white;
    font-size: 14px;
    font-weight: 800;
    background: linear-gradient(135deg, var(--color-primary-200), var(--color-primary-600));
}

.login-form { display: grid; gap: 16px; }
.login-field { display: grid; gap: 8px; margin: 0 !important; }
.password-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }

:deep(.login-field .el-input__wrapper) {
    min-height: 44px;
    border-radius: 10px;
    padding: 0 14px;
    background: linear-gradient(180deg, #fff, #f8fafc);
}

:deep(.login-field .el-input__inner) {
    color: var(--color-text-primary);
    font-size: 14px;
    font-weight: 600;
}

@media (max-width: 640px) {
    .password-grid { grid-template-columns: 1fr; }
}
</style>
