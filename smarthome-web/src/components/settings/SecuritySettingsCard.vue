<script setup lang="ts">
import { ElMessage, ElMessageBox } from "element-plus";
import type { SecuritySettings } from "../../types/settings";
import SettingsSectionCard from "./SettingsSectionCard.vue";

defineProps<{
    security: SecuritySettings;
}>();

const changePassword = async () => {
    try {
        await ElMessageBox.prompt("请输入新密码", "修改密码", {
            confirmButtonText: "保存",
            cancelButtonText: "取消",
            inputType: "password",
            inputPattern: /^.{6,}$/,
            inputErrorMessage: "密码至少 6 位",
        });
        ElMessage.success("密码已更新");
    } catch {
        ElMessage.info("已取消修改密码");
    }
};

const showPending = (name: string) => {
    ElMessage.info(`${name}功能已进入待办流程`);
};
</script>

<template>
    <SettingsSectionCard id="security" icon="◇" title="安全">
        <div class="settings-field">
            <span>修改密码</span
            ><button
                class="secondary-button"
                type="button"
                @click="changePassword"
            >
                修改
            </button>
        </div>
        <div class="settings-field">
            <span>双重认证</span
            ><el-switch v-model="security.twoFactorEnabled" />
        </div>
        <div class="settings-field">
            <span>登录设备管理</span
            ><button
                class="secondary-button"
                type="button"
                @click="showPending('登录设备管理')"
            >
                管理
            </button>
        </div>
        <div class="settings-field">
            <span>操作日志</span
            ><button
                class="secondary-button"
                type="button"
                @click="showPending('操作日志')"
            >
                查看
            </button>
        </div>
    </SettingsSectionCard>
</template>
