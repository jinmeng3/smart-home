import { computed, ref, onScopeDispose, getCurrentScope } from "vue";
import { gsap, motionEase, seconds, useMotionMode } from "../motion";

/**
 * 状态动画阶段。
 */
export type StatusPhase = "idle" | "pending" | "success" | "error";

/**
 * 状态视觉反馈配置。
 */
export interface StatusVisuals {
    /** 图标名称（Morphicons 图标名） */
    icon: string;
    /** 语义色 CSS 变量 */
    color: string;
    /** 背景色 CSS 变量 */
    bg: string;
    /** 可选文案 */
    label?: string;
}

/**
 * 状态动画配置。
 */
export interface AnimatedStatusOptions {
    /** 各状态对应的视觉配置 */
    visuals: Record<StatusPhase, StatusVisuals>;
    /** 反馈时长（毫秒，默认 1800，包含保持 + 淡出） */
    duration?: number;
    /** 保持时间（毫秒，默认 1200，之后恢复到 idle） */
    holdDuration?: number;
}

/**
 * Unified pending/success/error 状态动画 composable。
 *
 * 用于设备、场景、自动化等操作按钮和状态指示器的反馈动画：
 * - pending：加载中（旋转图标）
 * - success：成功反馈（图标 Morph + 颜色强调）
 * - error：失败反馈（图标 Morph + 颜色强调）
 * - 反馈完成后自动恢复到 idle 状态
 *
 * @example
 * ```ts
 * const { phase, setPhase, visuals } = useAnimatedStatus({
 *   visuals: {
 *     idle: { icon: "refresh", color: "var(--color-text-secondary)", bg: "transparent" },
 *     pending: { icon: "loading", color: "var(--color-primary)", bg: "var(--color-primary-50)" },
 *     success: { icon: "check", color: "var(--color-success)", bg: "var(--color-success-50)" },
 *     error: { icon: "warning", color: "var(--color-danger)", bg: "var(--color-danger-50)" },
 *   },
 * });
 * ```
 */
export const useAnimatedStatus = (options: AnimatedStatusOptions) => {
    const { isReduced } = useMotionMode();
    const phase = ref<StatusPhase>("idle");
    let autoResetTimer: ReturnType<typeof setTimeout> | undefined;

    const holdDuration = options.holdDuration ?? 1200;

    /** 当前状态对应的视觉配置 */
    const visuals = computed<StatusVisuals>(() => options.visuals[phase.value] ?? options.visuals.idle);

    /**
     * 设置状态并触发视觉反馈。
     * - pending：持续显示，直到手动切换为 success/error
     * - success/error：保持 holdDuration 后自动恢复到 idle
     * - idle：直接显示
     */
    const setPhase = async (newPhase: StatusPhase) => {
        // 清除旧的自动重置定时器
        if (autoResetTimer) {
            clearTimeout(autoResetTimer);
            autoResetTimer = undefined;
        }

        // 减少动态效果模式：直接切换状态，不播放动画
        if (isReduced.value) {
            phase.value = newPhase;
            return;
        }

        phase.value = newPhase;

        // success/error 在保持后自动恢复到 idle
        if (newPhase === "success" || newPhase === "error") {
            autoResetTimer = setTimeout(() => {
                phase.value = "idle";
                autoResetTimer = undefined;
            }, holdDuration);
        }
    };

    /**
     * 执行一个异步操作并自动管理状态反馈。
     *
     * @param action 异步操作函数
     * @returns 操作结果
     */
    const executeWithFeedback = async <T>(action: () => Promise<T>): Promise<T | undefined> => {
        setPhase("pending");
        try {
            const result = await action();
            setPhase("success");
            return result;
        } catch {
            setPhase("error");
            return undefined;
        }
    };

    /** 重置到 idle 状态 */
    const reset = () => {
        if (autoResetTimer) {
            clearTimeout(autoResetTimer);
            autoResetTimer = undefined;
        }
        phase.value = "idle";
    };

    // 组件销毁时清理
    if (getCurrentScope()) {
        onScopeDispose(() => {
            if (autoResetTimer) clearTimeout(autoResetTimer);
        });
    }

    return {
        /** 当前状态阶段 */
        phase,
        /** 当前状态对应的视觉配置 */
        visuals,
        /** 设置状态 */
        setPhase,
        /** 执行操作并自动反馈 */
        executeWithFeedback,
        /** 重置到 idle */
        reset,
    };
};