<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { ElMessageBox } from "element-plus";
import type { AccountForm } from "../../types/account";
import SettingsSectionCard from "./SettingsSectionCard.vue";

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
        <div class="mb-4 flex items-center gap-4">
            <img
                v-if="visibleAvatarUrl"
                class="h-14 w-14 shrink-0 rounded-full object-cover"
                :src="visibleAvatarUrl"
                alt=""
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
                <div class="mt-2 flex gap-2">
                    <button
                        class="secondary-button h-8 min-w-[70px]"
                        :disabled="loading"
                        type="button"
                        @click="selectAvatar"
                    >
                        上传
                    </button>
                    <button
                        class="secondary-button h-8 min-w-[70px]"
                        :disabled="loading || !visibleAvatarUrl"
                        type="button"
                        @click="deleteAvatar"
                    >
                        删除
                    </button>
                    <input
                        ref="avatarInput"
                        class="hidden"
                        accept="image/jpeg,image/png,image/webp"
                        type="file"
                        @change="uploadAvatar"
                    />
                </div>
            </div>
        </div>

        <div class="grid gap-3">
            <label class="settings-field"
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
            <label class="settings-field"
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
            <label class="settings-field"
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
            <label class="settings-field"
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
            <label class="settings-field">
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

        <button
            class="primary-button mx-auto mt-4"
            :disabled="loading || !dirty"
            type="button"
            @click="emit('save')"
        >
            {{ loading ? "保存中" : "保存更改" }}
        </button>
    </SettingsSectionCard>
</template>
