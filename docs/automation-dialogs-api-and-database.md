# 自动化弹窗后端接口与数据写入说明

本文对应自动化中心的创建、编辑、导入、执行日志、定时设置和批量启用六个弹窗。前端当前使用本地状态演示交互；接入后端时按本文契约替换事件处理即可。

## 1. 数据表建议

### `automation_rules`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | UUID | 主键 |
| `household_id` | UUID | 家庭 ID，必须从登录上下文校验权限 |
| `name` | VARCHAR(30) | 规则名称 |
| `description` | VARCHAR(100) | 描述 |
| `trigger_type` | VARCHAR(32) | `device_state`、`location`、`schedule`、`manual` |
| `trigger_config` | JSONB | 触发器参数 |
| `enabled` | BOOLEAN | 是否启用 |
| `priority` | SMALLINT | 1 低、2 中、3 高 |
| `cooldown_seconds` | INTEGER | 重复触发间隔 |
| `delay_seconds` | INTEGER | 动作执行延迟 |
| `note` | VARCHAR(100) | 备注 |
| `created_at` / `updated_at` | TIMESTAMPTZ | 创建、更新时间 |

动作、房间、设备分别使用 `automation_actions(rule_id, device_id, action_type, action_config, sort_order)`、`automation_rule_rooms(rule_id, room_id)`、`automation_rule_devices(rule_id, device_id)`。定时配置使用 `automation_schedules(rule_id, time_local, weekdays, timezone, start_date, end_date, enabled)`；执行记录使用 `automation_runs` 与 `automation_run_steps`。

建议为 `(household_id, name)`、`automation_actions(rule_id, sort_order)`、`automation_runs(rule_id, started_at DESC)` 建索引。所有删除优先软删除，并为规则增加 `version` 字段实施乐观锁。

## 2. 创建与编辑规则

- `POST /api/v1/automations`
- `PUT /api/v1/automations/{rule_id}`，请求携带当前 `version`
- `GET /api/v1/automations/{rule_id}`

```json
{
  "household_id": "uuid",
  "name": "回家自动开灯",
  "description": "到家后开启舒适环境",
  "trigger": {
    "type": "device_state",
    "device_id": "uuid",
    "operator": "eq",
    "value": "open"
  },
  "effective_period": { "type": "all_day" },
  "room_ids": ["uuid"],
  "device_ids": ["uuid"],
  "actions": [
    { "device_id": "uuid", "type": "turn_on", "config": { "brightness": 80, "color_temperature": 4000 }, "sort_order": 1 }
  ],
  "delay_seconds": 0,
  "priority": 2,
  "cooldown_seconds": 0,
  "note": ""
}
```

写入必须在单个事务中完成：校验家庭权限与设备归属，写 `automation_rules`，替换动作和关联表，更新调度任务，提交后发布 `automation.rule.changed` 事件。任何一步失败均回滚。服务端必须再次校验名称长度、动作数量、设备能力和触发参数，不信任前端枚举。

## 3. 导入规则

- `POST /api/v1/automations/import/preview`：`multipart/form-data` 上传文件，仅解析和校验，不写库。
- `POST /api/v1/automations/import/commit`：提交预览返回的 `import_token`、`conflict_strategy`（`skip` / `overwrite` / `copy`）、`preserve_ids`、`smart_merge`。

文件上限 10 MB，只接受 JSON、YAML 或服务端定义的压缩模板包。解析应禁用 YAML 自定义对象、校验压缩包路径穿越及解压后大小，并为 `import_token` 设置短时有效期。提交以批次事务执行；若产品允许部分成功，返回每条规则的 `imported`、`skipped` 或 `failed` 状态并记录审计日志。

## 4. 执行日志

- `GET /api/v1/automation-runs?from=&to=&rule_id=&result=&room_id=&page=&page_size=`
- `GET /api/v1/automation-runs/{run_id}`
- `GET /api/v1/automation-runs/export?from=&to=&format=csv`

列表返回运行时间、规则、触发来源、结果、耗时；详情返回条件检查与每个动作步骤。日志只追加不修改，失败信息应保存可展示错误码，避免存储密钥、令牌或精确位置等敏感内容。导出任务量大时使用异步任务和一次性下载地址。

## 5. 定时设置

- `PUT /api/v1/automations/schedules/batch`

```json
{
  "rule_ids": ["uuid", "uuid"],
  "timezone": "Asia/Shanghai",
  "time": "07:30:00",
  "weekdays": [1, 2, 3, 4, 5],
  "frequency": "daily",
  "interval": 1
}
```

服务端以家庭时区保存规则，同时保留 IANA 时区名以正确处理夏令时。事务更新 `automation_schedules` 后重建调度任务；使用 `(rule_id, scheduled_at)` 作为幂等键，避免调度器重启造成重复执行。

## 6. 批量启用

- `POST /api/v1/automations/batch-enable`

```json
{
  "rule_ids": ["uuid", "uuid"],
  "execute_now": true,
  "execution_interval_seconds": 0
}
```

校验全部规则属于同一家庭后，在事务中批量更新 `enabled = true`。`execute_now` 应在提交成功后投递队列，不能在数据库事务内直接操作设备。接口接受 `Idempotency-Key`，响应返回 `updated_count`、`unchanged_count` 和可选的 `execution_batch_id`。

## 7. 通用响应与错误

成功响应使用 `{ "data": ..., "request_id": "..." }`；校验失败返回 422，权限不足返回 403，规则不存在返回 404，版本冲突返回 409。所有写接口记录操作者、家庭、规则、变更摘要和 `request_id`，不要在审计日志中记录完整导入文件或设备凭据。

