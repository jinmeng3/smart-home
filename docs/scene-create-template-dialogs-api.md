# 场景创建与模板导入弹窗接口设计

本文档对应前端两个独立页面弹窗：

- 创建场景：`SceneCreateDialog.vue`
- 导入模板：`SceneTemplateDialog.vue`

实现遵循 SOLID：

- 前端页面只负责组装，弹窗组件只负责各自 UI。
- `useSceneModeController` 只负责交互协调和消息提示。
- 后端按模板、场景、步骤、执行预览拆分接口，避免单接口承担过多职责。

## 数据库

沿用 SQLite：`db/orion_home.db`。

### scene_templates

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | TEXT PRIMARY KEY | 模板 ID |
| name | TEXT NOT NULL | 模板名称 |
| description | TEXT NOT NULL | 模板描述 |
| icon | TEXT NOT NULL | SVG 图标名 |
| color | TEXT NOT NULL | 色彩 token |
| trigger_type | TEXT NOT NULL | `manual`、`schedule`、`location`、`device` |
| trigger_label | TEXT NOT NULL | 触发文案 |
| category | TEXT NOT NULL | 分类，如娱乐、安防、睡眠 |
| room_labels | TEXT NOT NULL | JSON 数组 |
| device_count | INTEGER NOT NULL | 设备数量 |
| recommended | INTEGER NOT NULL DEFAULT 0 | 是否推荐 |
| steps_json | TEXT NOT NULL | 步骤 JSON |
| sort_order | INTEGER NOT NULL DEFAULT 0 | 排序 |
| created_at | TEXT NOT NULL | 创建时间 |
| updated_at | TEXT NOT NULL | 更新时间 |

### scenes

创建弹窗提交后写入 `scenes` 表，字段参考 `docs/scene-mode-api-and-database.md`，并补充：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| source_template_id | TEXT NULL | 来源模板 ID |
| sort_order | INTEGER NOT NULL DEFAULT 0 | 场景排序 |
| high_risk | INTEGER NOT NULL DEFAULT 0 | 是否包含门锁、摄像头等高风险动作 |

### scene_steps

创建或导入时批量写入执行动作。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | TEXT PRIMARY KEY | 步骤 ID |
| scene_id | TEXT NOT NULL | 场景 ID |
| name | TEXT NOT NULL | 动作名称 |
| description | TEXT NOT NULL | 动作说明 |
| device_id | TEXT NOT NULL | 设备 ID |
| step_order | INTEGER NOT NULL | 执行顺序 |

## 创建场景

`POST /api/scenes`

输入：

```json
{
  "name": "回家模式",
  "description": "回到家时自动开启舒适环境",
  "icon": "home",
  "color": "var(--color-primary-600)",
  "triggerType": "location",
  "triggerLabel": "位置触发（到达“家”半径 100m）",
  "roomLabels": ["玄关", "客厅", "主卧"],
  "deviceIds": ["light-entry", "light-living", "ac-living"],
  "enabled": true,
  "steps": [
    {
      "name": "打开玄关灯",
      "description": "玄关灯 · 开",
      "deviceId": "light-entry",
      "order": 1
    }
  ]
}
```

输出：

```json
{
  "id": "home",
  "name": "回家模式",
  "description": "回到家时自动开启舒适环境",
  "icon": "home",
  "color": "var(--color-primary-600)",
  "triggerType": "location",
  "triggerLabel": "位置触发（到达“家”半径 100m）",
  "deviceCount": 8,
  "enabled": true,
  "recommended": false,
  "createdAt": "2026-08-02 20:00",
  "updatedAt": "2026-08-02 20:00",
  "steps": []
}
```

## 保存草稿

`POST /api/scenes/drafts`

输入同创建场景，允许缺少步骤。

输出：

```json
{
  "draftId": "draft-home-001",
  "updatedAt": "2026-08-02 20:00"
}
```

## 查询模板列表

`GET /api/scenes/templates`

输入 Query：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| keyword | string | 否 | 模板名称或描述 |
| category | string | 否 | 分类 |
| limit | number | 否 | 默认 20 |

输出：

```json
{
  "items": [
    {
      "id": "romantic-dinner",
      "name": "浪漫晚餐模式",
      "description": "营造温馨浪漫的晚餐氛围",
      "icon": "light",
      "color": "var(--color-warning)",
      "triggerType": "manual",
      "triggerLabel": "手动执行",
      "roomLabels": ["餐厅", "客厅"],
      "deviceCount": 6,
      "recommended": true,
      "category": "娱乐",
      "steps": []
    }
  ]
}
```

## 导入模板

`POST /api/scenes/templates/{template_id}/use`

输入：

```json
{
  "name": "浪漫晚餐模式",
  "enabled": true,
  "deviceMapping": {
    "dining-light": "device-1001"
  }
}
```

输出：创建后的 `Scene` 对象。

后端处理：

- 查询 `scene_templates`。
- 根据 `steps_json` 生成 `scene_steps`。
- 根据 `deviceMapping` 替换设备 ID。
- 写入 `scenes.source_template_id`。
- 返回完整场景对象。

## 模板预览

`GET /api/scenes/templates/{template_id}/preview`

输出：

```json
{
  "templateId": "romantic-dinner",
  "matchedDeviceCount": 6,
  "missingDeviceCount": 0,
  "steps": [
    {
      "name": "调暗餐厅灯光 40%",
      "description": "餐厅灯 · 亮度 40%",
      "deviceId": "dining-light",
      "matched": true
    }
  ]
}
```
