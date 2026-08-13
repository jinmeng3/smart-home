import { computed, reactive, ref, watch } from "vue";
import { onScopeDispose } from "vue";
import { nextTick } from "vue";
import { listDevices as apiListDevices } from "../api/device";
import type { Device, DeviceFilters } from "../types/device";

export type DeviceSortKey = "updated" | "name" | "status";

const createDefaultFilters = (): DeviceFilters => ({
    page: 1,
    pageSize: 10,
    keyword: "",
    type: "",
    status: "",
    room: "",
});

interface DeviceQueryHooks {
    /** 每次加载完成（非 Abort）后回调，用于刷新选中设备等派生状态 */
    onLoaded?: (devices: Device[], total: number) => void | Promise<void>;
    onError?: (error: unknown) => void;
}

/**
 * 设备列表查询——统一管理筛选、分页、防抖与请求取消。
 *
 * 与页面解耦：调用方通过 `updateFilter/updatePage/updatePageSize` 修改条件，
 * composable 内部用单一 watch 合并筛选变化（筛选变更 → 页码重置 + 防抖加载，
 * 分页变更 → 立即加载），并取消旧请求防止旧响应覆盖新数据。
 */
export const useDeviceQuery = (hooks: DeviceQueryHooks = {}) => {
    const filters = reactive<DeviceFilters>(createDefaultFilters());
    const devices = ref<Device[]>([]);
    const total = ref(0);
    const loading = ref(false);
    const sort = ref<DeviceSortKey>("updated");

    const rooms = computed(() =>
        Array.from(new Set(devices.value.map((device) => device.room))).filter(
            Boolean,
        ),
    );

    let requestId = 0;
    let controller: AbortController | null = null;
    let timerId = 0;
    /** 筛选变更重置 page 时，抑制分页 watch 的重复请求 */
    let suppressPageLoad = false;

    const runLoad = async (signal?: AbortSignal) => {
        const currentRequest = ++requestId;
        loading.value = true;

        try {
            const response = await apiListDevices(filters, signal);
            if (currentRequest !== requestId) return;
            devices.value = response.items;
            total.value = response.total;
            await hooks.onLoaded?.(response.items, response.total);
        } catch (error) {
            if (error instanceof DOMException && error.name === "AbortError") {
                return;
            }
            if (currentRequest !== requestId) return;
            devices.value = [];
            total.value = 0;
            hooks.onError?.(error);
        } finally {
            if (currentRequest === requestId) {
                loading.value = false;
            }
        }
    };

    /** 防抖加载（筛选输入停止后才请求） */
    const scheduleLoad = () => {
        window.clearTimeout(timerId);
        timerId = window.setTimeout(() => {
            controller?.abort();
            const next = new AbortController();
            controller = next;
            void runLoad(next.signal);
        }, 250);
    };

    /** 立即加载（分页、首次、保存后刷新） */
    const loadDevices = () => {
        window.clearTimeout(timerId);
        controller?.abort();
        const next = new AbortController();
        controller = next;
        void runLoad(next.signal);
    };

    // ── 单一筛选监听：筛选变化 → 页码重置 + 防抖加载 ────────────
    watch(
        () =>
            [
                filters.keyword,
                filters.room,
                filters.status,
                filters.type,
            ] as const,
        () => {
            suppressPageLoad = true;
            filters.page = 1;
            scheduleLoad();
            void nextTick(() => {
                suppressPageLoad = false;
            });
        },
    );

    // ── 分页监听：立即加载（页码重置导致的触发被抑制） ─────────
    watch(
        () => [filters.page, filters.pageSize] as const,
        () => {
            if (suppressPageLoad) return;
            loadDevices();
        },
    );

    const updateFilter = <K extends keyof DeviceFilters>(
        key: K,
        value: DeviceFilters[K],
    ) => {
        filters[key] = value;
    };

    const updatePage = (value: number) => {
        filters.page = value;
    };

    const updatePageSize = (value: number) => {
        filters.pageSize = value;
    };

    const cancel = () => {
        window.clearTimeout(timerId);
        controller?.abort();
        controller = null;
        suppressPageLoad = false;
    };

    onScopeDispose(cancel);

    return {
        cancel,
        devices,
        filters,
        loadDevices,
        loading,
        rooms,
        scheduleLoad,
        sort,
        total,
        updateFilter,
        updatePage,
        updatePageSize,
    };
};