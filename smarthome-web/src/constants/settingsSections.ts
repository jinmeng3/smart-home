import type { SettingsSectionId } from "../types/settings";

export interface SettingsSectionConfig {
    id: SettingsSectionId;
    label: string;
    shortLabel: string;
    group: string;
    groupLabel: string;
    icon: string;
    tone: string;
}

/**
 * 统一设置分区配置——单一定义源，消除多处重复定义。
 * 所有分区相关的数据（目录、滚动监听、移动端标签、分组标题等）由此生成。
 */
export const settingsSections: SettingsSectionConfig[] = [
    {
        id: "account",
        label: "账户与家庭",
        shortLabel: "账户",
        group: "personal",
        groupLabel: "个人与家庭",
        icon: "account",
        tone: "primary",
    },
    {
        id: "appearance",
        label: "界面",
        shortLabel: "界面",
        group: "experience",
        groupLabel: "使用体验",
        icon: "appearance",
        tone: "purple",
    },
    {
        id: "notifications",
        label: "通知",
        shortLabel: "通知",
        group: "experience",
        groupLabel: "使用体验",
        icon: "bell",
        tone: "warning",
    },
    {
        id: "ai",
        label: "AI 助手",
        shortLabel: "AI",
        group: "service",
        groupLabel: "智能服务",
        icon: "ai",
        tone: "indigo",
    },
    {
        id: "homeAssistant",
        label: "Home Assistant",
        shortLabel: "Home",
        group: "service",
        groupLabel: "智能服务",
        icon: "platform",
        tone: "orange",
    },
    {
        id: "security",
        label: "安全",
        shortLabel: "安全",
        group: "security",
        groupLabel: "安全与数据",
        icon: "security",
        tone: "danger",
    },
    {
        id: "backup",
        label: "备份",
        shortLabel: "备份",
        group: "security",
        groupLabel: "安全与数据",
        icon: "backup",
        tone: "success",
    },
];

/** 按分组整理 */
export const settingsGroups = settingsSections.reduce<
    { group: string; groupLabel: string; sections: SettingsSectionConfig[] }[]
>((acc, section) => {
    const existing = acc.find((g) => g.group === section.group);
    if (existing) {
        existing.sections.push(section);
    } else {
        acc.push({
            group: section.group,
            groupLabel: section.groupLabel,
            sections: [section],
        });
    }
    return acc;
}, []);

/** 所有分区 ID 列表 */
export const sectionIds: SettingsSectionId[] = settingsSections.map((s) => s.id);

/** 分区 ID → 配置 的快速查找 */
export const sectionById = settingsSections.reduce<
    Record<SettingsSectionId, SettingsSectionConfig>
>((acc, section) => {
    acc[section.id] = section;
    return acc;
}, {} as Record<SettingsSectionId, SettingsSectionConfig>);