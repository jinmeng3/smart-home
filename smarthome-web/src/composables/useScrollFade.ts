import { computed, onScopeDispose, ref, watch, type Ref } from "vue";

/**
 * 侧栏滚动渐隐检测——统一 passive scroll + rAF 节流 + ResizeObserver。
 *
 * 用于侧栏底部渐隐遮罩：内容可滚动时显示渐隐，滚到底部时隐藏。
 * 折叠状态或内容变化（设备切换、平台展开）时自动重新计算。
 *
 * @param scrollRef 滚动容器 ref
 * @param options.deactivated 折叠时挂起监听（不更新状态）
 * @param options.sources 内容变化依赖（数组变化时重新计算）
 */
export const useScrollFade = (
    scrollRef: Ref<HTMLElement | null>,
    options: {
        deactivated?: Ref<boolean>;
        sources?: Ref<unknown>[];
    } = {},
) => {
    const canScroll = ref(false);
    const atBottom = ref(true);

    let rafId = 0;
    let resizeObserver: ResizeObserver | null = null;

    const update = () => {
        if (options.deactivated?.value) return;
        const el = scrollRef.value;
        if (!el) return;
        canScroll.value = el.scrollHeight > el.clientHeight + 4;
        atBottom.value =
            el.scrollTop + el.clientHeight >= el.scrollHeight - 8;
    };

    /** rAF 合并连续 scroll/resize 回调，避免每帧重复布局读取 */
    const schedule = () => {
        if (options.deactivated?.value) return;
        if (rafId) return;
        rafId = window.requestAnimationFrame(() => {
            rafId = 0;
            update();
        });
    };

    watch(
        scrollRef,
        (el) => {
            resizeObserver?.disconnect();
            resizeObserver = null;
            if (!el) return;
            resizeObserver = new ResizeObserver(schedule);
            resizeObserver.observe(el);
            update();
        },
        { immediate: true },
    );

    if (options.sources?.length) {
        watch(options.sources, schedule, { deep: true });
    }

    onScopeDispose(() => {
        window.cancelAnimationFrame(rafId);
        resizeObserver?.disconnect();
        resizeObserver = null;
    });

    /** 内容/折叠变化后立即重算（非滚动触发，如平台展开） */
    const refresh = () => {
        window.cancelAnimationFrame(rafId);
        rafId = 0;
        update();
    };

    return { canScroll, atBottom, refresh, schedule };
};