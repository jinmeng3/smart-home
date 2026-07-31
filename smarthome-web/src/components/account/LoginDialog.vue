<script setup lang="ts">
import { computed, reactive, ref } from "vue";
import { ElButton, ElInput, ElMessage } from "element-plus";
import { useAuthStore } from "../../stores/auth";
import BaseModal from "../common/BaseModal.vue";
import "element-plus/theme-chalk/el-input.css";
import "element-plus/theme-chalk/el-message.css";

type AuthMode = "login" | "register";

const authStore = useAuthStore();
const mode = ref<AuthMode>("login");
const submitting = ref(false);
const loginForm = reactive({ account: "", password: "" });
const registerForm = reactive({
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
});
const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const title = computed(() =>
    mode.value === "login" ? "登录 Orion Home" : "注册 Orion Home",
);
const description = computed(() =>
    mode.value === "login"
        ? "登录后同步家庭、会话和智能助手配置"
        : "创建账户，开始管理你的智能家庭",
);

const selectMode = (nextMode: AuthMode) => {
    if (submitting.value) return;
    mode.value = nextMode;
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
    if (registerForm.password.length < 8) {
        ElMessage.warning("密码至少需要 8 位字符");
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
        window.location.reload();
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
</script>

<template>
    <BaseModal
        v-model="authStore.loginVisible"
        :closable="!submitting"
        class="login-dialog"
        width="560px"
    >
        <template #header>
            <header class="dialog-header">
                <span class="dialog-icon" aria-hidden="true">♙</span>
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

        <nav class="auth-tabs" aria-label="账户操作">
            <button :class="{ active: mode === 'login' }" type="button" @click="selectMode('login')">登录</button>
            <button :class="{ active: mode === 'register' }" type="button" @click="selectMode('register')">注册</button>
        </nav>

        <form class="login-form" @submit.prevent="submit">
            <template v-if="mode === 'login'">
                <label class="login-field">
                    <span>账号</span>
                    <ElInput v-model="loginForm.account" autocomplete="username" placeholder="邮箱或用户名" />
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
                    <label class="login-field"><span>密码</span><ElInput v-model="registerForm.password" autocomplete="new-password" placeholder="至少 8 位字符" show-password type="password" /></label>
                    <label class="login-field"><span>确认密码</span><ElInput v-model="registerForm.confirmPassword" autocomplete="new-password" placeholder="再次输入密码" show-password type="password" /></label>
                </div>
            </template>
        </form>

        <template #footer>
            <footer class="dialog-footer">
                <span>{{ mode === "login" ? "账户凭据仅用于安全登录" : "注册即表示同意账户安全规范" }}</span>
                <div>
                    <ElButton :disabled="submitting" @click="authStore.loginVisible = false">取消</ElButton>
                    <ElButton :loading="submitting" type="primary" @click="submit">{{ mode === "login" ? "登录" : "创建账户" }}</ElButton>
                </div>
            </footer>
        </template>
    </BaseModal>
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

.login-form { display: grid; gap: 16px; }
.login-field { display: grid; gap: 8px; margin: 0 !important; }
.password-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }

@media (max-width: 640px) {
    .password-grid { grid-template-columns: 1fr; }
}
</style>
