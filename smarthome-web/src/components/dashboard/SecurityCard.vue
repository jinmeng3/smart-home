<script setup lang="ts">
import { useHomeStore } from "../../stores/home";
import SvgIcon from "../common/SvgIcon.vue";

const store = useHomeStore();
</script>

<template>
    <section
        class="security-card motion-card page-enter-stagger min-w-0 rounded-xl border border-[var(--color-border)] bg-[var(--color-card-bg)] px-4 py-2.5 shadow-soft"
        style="animation-delay: 420ms"
    >
        <div class="mb-2 flex items-center justify-between gap-2">
            <h2
                class="flex items-center gap-1.5 text-[14px] font-extrabold text-slate-800"
            >
                <SvgIcon name="security" size="sm" />
                安防
            </h2>
            <span
                class="security-badge"
                :class="store.securityAlertHandled ? 'is-ok' : 'is-warn'"
            >
                {{ store.securityAlertHandled ? "正常" : "异常" }}
            </span>
        </div>

        <!-- 主信息：告警数量 -->
        <p class="security-count text-lg font-extrabold leading-snug">
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
            class="motion-button mt-2.5 inline-flex items-center gap-0.5 text-xs font-bold text-blue-600 transition-colors duration-150 hover:text-blue-700"
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

.security-summary {
    margin-top: 2px;
    color: var(--color-text-tertiary);
}
</style>
