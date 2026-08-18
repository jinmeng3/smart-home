/**
 * 图标注册表 —— 集中管理业务名称到 Lucide / 自定义图标的映射。
 *
 * 业务组件通过 <SvgIcon name="xxx"> 引用，不直接依赖 lucide 或 morphicons。
 * 通用图标优先使用 Lucide 数据包（tree-shaking 友好），智能家居专用图标
 * 使用自定义 IconNode 路径。
 *
 * 约定：
 *  - 业务名称使用 kebab-case。
 *  - 映射关系在阶段一确定，后续只增不改。
 *  - 未知名称回退到通用设备图标，开发环境输出警告。
 */

import type { IconNode } from "morphicons";

/* ========== Lucide 图标导入 ========== */
import {
    ArrowRight,
    Bell,
    Calendar,
    Camera,
    Check,
    CheckCircle,
    ChevronDown,
    ChevronLeft,
    ChevronRight,
    CloudUpload,
    Copy,
    Crosshair,
    Droplets,
    Ellipsis,
    Eye,
    Grid3x3,
    Home,
    Info,
    Layers,
    Lightbulb,
    List,
    Lock,
    MapPin,
    MessageCircle,
    Mic,
    Moon,
    Palette,
    Pencil,
    Plus,
    PlusCircle,
    Plug,
    Power,
    RefreshCw,
    RotateCw,
    Scan,
    Search,
    Send,
    Server,
    Settings,
    Shield,
    Sparkles,
    Square,
    Sun,
    Thermometer,
    Trash2,
    TriangleAlert,
    Upload,
    User,
    Users,
    Volume2,
    X,
    Zap,
} from "lucide";

/* ========== 自定义智能家居图标 ========== */

/** 空调（雪花 + 风扇线条） */
const airConditioner = [
    ["path", { d: "M12 2v20M4.2 6.5l15.6 11M19.8 6.5l-15.6 11" }],
    ["path", { d: "m9.5 4.5 2.5 2 2.5-2M9.5 19.5l2.5-2 2.5 2" }],
    ["path", { d: "m5 9 3-.5-.3-3M19 15l-3 .5.3 3" }],
    ["path", { d: "m19 9-3-.5.3-3M5 15l3 .5-.3 3" }],
] as unknown as IconNode;

/** 空气质量/净化（肺叶形气流） */
const airQuality = [
    ["path", { d: "M12 21c-5-3.5-7-7.8-5.8-13.5C12 7 16.5 4.8 19 2.8c.8 8.5-1.8 14.2-7 18.2Z" }],
    ["path", { d: "M8.5 17c2-2.2 4.3-4.2 7.5-7" }],
] as unknown as IconNode;

/** 自动化流程（三个节点 + 连线） */
const automation = [
    ["circle", { cx: "12", cy: "4", r: "2" }],
    ["circle", { cx: "5", cy: "18", r: "2" }],
    ["circle", { cx: "19", cy: "18", r: "2" }],
    ["path", { d: "M12 6v5M6.5 16.5 10.5 12M17.5 16.5 13.5 12" }],
] as unknown as IconNode;

/** 舒适度（笑脸弧线） */
const comfort = [
    ["circle", { cx: "12", cy: "12", r: "9" }],
    ["circle", { cx: "9", cy: "10", r: "1", fill: "currentColor", stroke: "none" }],
    ["circle", { cx: "15", cy: "10", r: "1", fill: "currentColor", stroke: "none" }],
    ["path", { d: "M8 14.5c1 1.5 2.3 2.2 4 2.2s3-.7 4-2.2" }],
] as unknown as IconNode;

/** 窗帘（波浪形） */
const curtain = [
    ["path", { d: "M3 4h18M5 4v16M19 4v16" }],
    ["path", { d: "M5 5c4 2 4 11 0 14M19 5c-4 2-4 11 0 14" }],
    ["path", { d: "M12 5v14" }],
] as unknown as IconNode;

/** 设备管理（通用设备 + 齿轮） */
const deviceManagement = [
    ["rect", { x: "3", y: "4", width: "12", height: "16", rx: "2" }],
    ["path", { d: "M7 8h4" }],
    ["circle", { cx: "9", cy: "16", r: "1.5" }],
    ["circle", { cx: "18", cy: "9", r: "3" }],
    ["path", { d: "M18 7.5V9l1 1" }],
] as unknown as IconNode;

/** Home Assistant 品牌图标（房子 + 连接点） */
const homeAssistant = [
    ["path", { d: "m3 11 9-8 9 8" }],
    ["path", { d: "M5.5 9.5V21h13V9.5" }],
    ["circle", { cx: "12", cy: "10", r: "1.3" }],
    ["circle", { cx: "9", cy: "16", r: "1.3" }],
    ["circle", { cx: "15", cy: "16", r: "1.3" }],
    ["path", { d: "m12 11.3-3 3.4M12 11.3l3 3.4M10.3 16h3.4" }],
] as unknown as IconNode;

/** Matter 协议图标（中心十字 + 交叉线） */
const matter = [
    ["path", { d: "M12 3v18M3 12h18" }],
    ["path", { d: "m5.5 5.5 13 13M18.5 5.5l-13 13" }],
    ["circle", { cx: "12", cy: "12", r: "3" }],
] as unknown as IconNode;

/** Zigbee 协议图标（圆 + Z 形折线） */
const zigbee = [
    ["circle", { cx: "12", cy: "12", r: "9" }],
    ["path", { d: "M8 8h9l-10 8h9" }],
] as unknown as IconNode;

/** MQTT 协议图标（广播波纹） */
const mqtt = [
    ["path", { d: "M5 19a2 2 0 1 1 0-4" }],
    ["path", { d: "M4 11a9 9 0 0 1 9 9" }],
    ["path", { d: "M4 6a14 14 0 0 1 14 14" }],
    ["path", { d: "M4 2a18 18 0 0 1 18 18" }],
] as unknown as IconNode;

/** 在线设备（手机 + 勾选） */
const onlineDevice = [
    ["rect", { x: "7", y: "3", width: "10", height: "18", rx: "2.5" }],
    ["path", { d: "M10 6h4M11 18h2" }],
    ["path", { d: "m9.5 12 1.7 1.7 3.5-4" }],
] as unknown as IconNode;

/** 离线设备（手机 + 叉号） */
const offlineDevice = [
    ["rect", { x: "7", y: "3", width: "10", height: "18", rx: "2.5" }],
    ["path", { d: "M10 6h4M11 18h2" }],
    ["path", { d: "m9.5 10 5 5M14.5 10l-5 5" }],
] as unknown as IconNode;

/** 房间（建筑 + 指示点） */
const room = [
    ["path", { d: "M5 21V4a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v17" }],
    ["path", { d: "M3 21h18" }],
    ["circle", { cx: "15.5", cy: "12", r: ".8", fill: "currentColor", stroke: "none" }],
] as unknown as IconNode;

/** 场景（星星）—— 不同于 Lucide Star 的 5 角星，使用 5 尖星更贴合场景语义 */
const scene = [
    ["path", { d: "m12 3 2.7 5.5 6 .9-4.3 4.2 1 6-5.4-2.9-5.4 2.9 1-6-4.3-4.2 6-.9L12 3Z" }],
] as unknown as IconNode;

/** 传感器（信号波纹 + 中心点） */
const sensor = [
    ["circle", { cx: "12", cy: "12", r: "1.3", fill: "currentColor", stroke: "none" }],
    ["path", { d: "M8.5 8.5a5 5 0 0 0 0 7M15.5 8.5a5 5 0 0 1 0 7" }],
    ["path", { d: "M5.5 5.5a9 9 0 0 0 0 13M18.5 5.5a9 9 0 0 1 0 13" }],
] as unknown as IconNode;

/** 固件/更新（云 + 上传箭头）—— 与 cloud-upload 不同，保持原始风格 */
const firmware = [
    ["path", { d: "M7 18H5.5A3.5 3.5 0 0 1 5 11a6.5 6.5 0 0 1 12.6-1.7A4.5 4.5 0 0 1 18.5 18H17" }],
    ["path", { d: "M12 19V10" }],
    ["path", { d: "m8.5 13.5 3.5-3.5 3.5 3.5" }],
] as unknown as IconNode;

/** 聊天（消息气泡）—— 用 Lucide MessageCircle 即可，但保留 chat 别名 */
/** 日志（文件 + 文字） */
const log = [
    ["path", { d: "M6 3h8l4 4v14H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z" }],
    ["path", { d: "M14 3v5h5" }],
    ["path", { d: "M8 12h7M8 16h7" }],
] as unknown as IconNode;

/** 能耗（柱状图） */
const energy = [
    ["path", { d: "M4 20V12M8 20V7M12 20V10M16 20V4M20 20V14" }],
    ["path", { d: "M3 20h18" }],
] as unknown as IconNode;

/* ========== 注册表 ========== */

export const iconRegistry = new Map<string, IconNode>([
    ["account", User],
    ["ai", Sparkles],
    ["air-conditioner", airConditioner],
    ["air-quality", airQuality],
    ["appearance", Palette],
    ["arrow-right", ArrowRight],
    ["automation", automation],
    ["backup", CloudUpload],
    ["bell", Bell],
    ["calendar", Calendar],
    ["camera", Camera],
    ["chat", MessageCircle],
    ["check", Check],
    ["check-circle", CheckCircle],
    ["chevron-down", ChevronDown],
    ["chevron-left", ChevronLeft],
    ["chevron-right", ChevronRight],
    ["close", X],
    ["delete", Trash2],
    ["curtain", curtain],
    ["device-management", deviceManagement],
    ["edit", Pencil],
    ["energy", energy],
    ["eye", Eye],
    ["firmware", firmware],
    ["grid", Grid3x3],
    ["group", Users],
    ["home", Home],
    ["home-assistant", homeAssistant],
    ["humidity", Droplets],
    ["illumination", Sun],
    ["info", Info],
    ["layers", Layers],
    ["light", Lightbulb],
    ["list", List],
    ["location", MapPin],
    ["lock", Lock],
    ["log", log],
    ["matter", matter],
    ["members", Users],
    ["mic", Mic],
    ["moon", Moon],
    ["more", Ellipsis],
    ["mqtt", mqtt],
    ["new-device", PlusCircle],
    ["noise", Volume2],
    ["notification", Bell],
    ["offline-device", offlineDevice],
    ["online-device", onlineDevice],
    ["platform", Server],
    ["plug", Plug],
    ["plus", Plus],
    ["power", Power],
    ["refresh", RefreshCw],
    ["room", room],
    ["rotate-cw", RotateCw],
    ["scan", Scan],
    ["scene", scene],
    ["search", Search],
    ["send", Send],
    ["square", Square],
    ["sun", Sun],
    ["security", Shield],
    ["sensor", sensor],
    ["settings", Settings],
    ["temperature", Thermometer],
    ["upload", Upload],
    ["warning", TriangleAlert],
    ["x", X],
    ["zigbee", zigbee],
]);

/** 通用回退图标 */
export const fallbackIcon = deviceManagement;

/**
 * 别名映射：Lucide 导出名称 → 业务名称。
 * 用于 API 层直接保存 Lucide 名称的场景。
 */
const aliasMap: Record<string, string> = {
    MessageCircle: "chat",
    X: "close",
};

/**
 * 根据业务名称解析图标数据。
 * - 未知名称：开发环境警告，回退到通用设备图标。
 * - 已知名称：返回对应的 Lucide IconNode 或自定义 IconNode。
 */
export function getIcon(name: string): IconNode {
    const direct = iconRegistry.get(name);
    if (direct) {
        return direct;
    }

    // 尝试别名映射
    const alias = aliasMap[name];
    if (alias) {
        const resolved = iconRegistry.get(alias);
        if (resolved) return resolved;
    }

    if (import.meta.env.DEV) {
        console.warn(
            `[SvgIcon] 未知图标名称 "${name}"，回退到通用设备图标。`,
        );
    }

    return fallbackIcon;
}