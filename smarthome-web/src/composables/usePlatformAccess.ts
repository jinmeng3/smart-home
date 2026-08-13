import { computed, type Ref } from "vue";
import { syncDevices as apiSyncDevices } from "../api/device";
import { devicePlatformOptions } from "../components/device/deviceMeta";
import type { Device, DevicePlatformInfo, PlatformConnectionStatus } from "../types/device";

/**
 * 接入平台数据与操作——从设备列表派生平台状态，供侧栏、状态条等共享。
 *
 * 派生数据（platforms/connectedPlatforms/connectedCount）在组件外集中计算，
 * 组件只消费结果；同步操作统一入口，后续设置中心接入平台管理时可复用。
 */
export const usePlatformAccess = (devices: Ref<Device[]>) => {
    const platforms = computed<DevicePlatformInfo[]>(() =>
        devicePlatformOptions.map((name) => {
            const platformDevices = devices.value.filter(
                (device) => device.connection === name,
            );
            const connected = platformDevices.length > 0;

            return {
                name,
                connected,
                status: (connected ? "connected" : "disabled") as PlatformConnectionStatus,
                deviceCount: platformDevices.length,
            };
        }),
    );

    const connectedPlatforms = computed(() =>
        platforms.value.filter((platform) => platform.connected),
    );

    const connectedCount = computed(() => connectedPlatforms.value.length);

    /** 单平台同步——后端暂未提供单平台接口，当前统一走全局同步 */
    const syncPlatform = async (_platformId: string) => {
        return await apiSyncDevices("Home Assistant");
    };

    /** 全平台同步 */
    const syncAllPlatforms = async () => {
        return await apiSyncDevices("Home Assistant");
    };

    return {
        connectedCount,
        connectedPlatforms,
        platforms,
        syncAllPlatforms,
        syncPlatform,
    };
};