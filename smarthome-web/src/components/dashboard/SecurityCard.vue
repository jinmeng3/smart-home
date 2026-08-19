<script setup lang="ts">
import { ref, watch, nextTick } from "vue";
import { useHomeStore } from "../../stores/home";
import SvgIcon from "../common/SvgIcon.vue";

const store = useHomeStore();

/** 安防状态变化时，对徽章与数量做一次短暂强调 */
const badgeEmphasis = ref(false);
let emphasisTimer: ReturnType<typeof setTimeout> | undefined;
watch(
    () => store.securityAlertHandled,
    () => {
        void nextTick(() => {
            badgeEmphasis.value = true;
            if (emphasisTimer) clearTimeout(emphasisTimer);
            emphasisTimer = setTimeout(() => {
                badgeEmphasis.value = false;
                emphasisTimer = undefined;
            }, 900);
        });
    },
);
</script>

<template>
    <section
        class="security-card motion-card min-w-0 rounded-xl border border-[var(--color-border)] bg-[var(--color-card-bg)] px-4 py-2.5 shadow-soft"
        style="animation-delay: 420ms"
    >
        <div class="mb-2 flex items-center justify-between gap-2">
            <h2
                class="flex items-center gap-1.5 text-[14px] font-extrabold text-[var(--color-text-primary)]"
            >
                <SvgIcon name="security" size="sm" />
                安防
            </h2>
            <span
                class="security-badge"
                :class="[
                    store.securityAlertHandled ? 'is-ok' : 'is-warn',
                    { 'is-emphasis': badgeEmphasis },
                ]"
            >
                {{ store.securityAlertHandled ? "正常" : "异常" }}
            </span>
        </div>

        <!-- 主信息：告警数量 -->
        <p
            class="security-count text-lg font-extrabold leading-snug"
            :class="{ 'is-emphasis': badgeEmphasis }"
        >
            {{ store.alertCount }} 处告警
        </p>
        <!-- 次信息：状态描述 -->
        <p class="security-summary text-xs">
            {{
                store.securityAlertHandled
                    ? "全部门窗已关闭"
                    : "门窗传感器异常"
            }}
        </p>
        <!-- 次级入口 -->
        <a
            class="motion-button mt-2.5 inline-flex items-center gap-0.5 text-xs font-bold text-[var(--color-primary-600)] transition-colors duration-150 hover:text-[var(--color-primary-700)]"
            href="#"
        >
            查看详情
            <SvgIcon name="chevron-right" size="sm" />
        </a>
    </section>
</template>

<style scoped>
.security-badge {
    border-radius: 999px;
    padding: 1px 8px;
    font-size: 10px;
    font-weight: 800;
    line-height: 1.6;
}

.security-badge.is-ok {
    color: var(--color-success);
    background: var(--color-success-soft);
}

.security-badge.is-warn {
    color: var(--color-warning);
    background: var(--color-warning-soft);
}

.security-count {
    color: var(--color-text-primary);
}

/* 状态变化时的一次性强调：不持续闪烁 */
.security-badge.is-emphasis,
.security-count.is-emphasis {
    animation: security-change-emphasis 500ms var(--motion-ease) 1 both;
}

@keyframes security-change-emphasis {
    0% { opacity: 0.55; transform: scale(0.96); }
    45% { opacity: 1; transform: scale(1.06); }
    100% { opacity: 1; transform: scale(1); }
}

.security-summary {
    margin-top: 2px;
    color: var(--color-text-tertiary);
}
</style>
