-- Smart Home Test Data SQL
-- Run this against your database to populate with realistic test data
-- Assumes tables are created via migrations (Alembic)
-- Uses fixed IDs for easier reference; adjust if using auto-increment differently

-- ============================================================
-- 1. USERS
-- ============================================================
INSERT INTO users (id, name, email, password_hash, status, failed_login_count, locked_until, last_login_at, avatar_url, created_at, updated_at) VALUES
(1, '张三', 'zhangsan@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S', 'active', 0, NULL, NOW(), NULL, NOW(), NOW()),
(2, '李四', 'lisi@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S', 'active', 0, NULL, NOW(), NULL, NOW(), NOW()),
(3, '王五', 'wangwu@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S', 'active', 0, NULL, NOW(), NULL, NOW(), NOW()),
(4, '测试用户', 'test@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S', 'active', 0, NULL, NOW(), NULL, NOW(), NOW());

-- Password for all above is "password123" (bcrypt hash)

-- ============================================================
-- 2. HOUSEHOLDS
-- ============================================================
INSERT INTO households (id, name, address, timezone, created_by, created_at, updated_at) VALUES
(1, '张三的智能家庭', '北京市朝阳区xxx小区1号楼', 'Asia/Shanghai', 1, NOW(), NOW()),
(2, '李四的温馨小家', '上海市浦东新区yyy公寓2栋', 'Asia/Shanghai', 2, NOW(), NOW()),
(3, '共享家庭', '深圳市南山区zzz大厦', 'Asia/Shanghai', 1, NOW(), NOW());

-- ============================================================
-- 3. HOUSEHOLD MEMBERSHIPS
-- ============================================================
INSERT INTO household_memberships (id, household_id, user_id, role, joined_at) VALUES
(1, 1, 1, 'admin', NOW()),   -- 张三是家庭1的管理员
(2, 1, 2, 'member', NOW()),  -- 李四是家庭1的成员
(3, 2, 2, 'admin', NOW()),   -- 李四是家庭2的管理员
(4, 2, 3, 'member', NOW()),  -- 王五是家庭2的成员
(5, 3, 1, 'admin', NOW()),   -- 张三是家庭3的管理员
(6, 3, 3, 'member', NOW()),  -- 王五是家庭3的成员
(7, 1, 4, 'member', NOW());  -- 测试用户加入家庭1

-- ============================================================
-- 4. ROOMS (for household_id = 1)
-- ============================================================
INSERT INTO rooms (id, household_id, name, floor, room_type, image_url, icon, theme_color, version, area, comfort, created_at, updated_at) VALUES
(1, 1, '客厅', '1F', 'living', NULL, 'living-room', '#3478f6', 1, 25.5, 85, NOW(), NOW()),
(2, 1, '主卧', '1F', 'bedroom', NULL, 'bedroom', '#e91e63', 1, 18.0, 90, NOW(), NOW()),
(3, 1, '次卧', '1F', 'bedroom', NULL, 'bedroom', '#9c27b0', 1, 12.0, 80, NOW(), NOW()),
(4, 1, '厨房', '1F', 'kitchen', NULL, 'kitchen', '#ff9800', 1, 8.0, 75, NOW(), NOW()),
(5, 1, '卫生间', '1F', 'bathroom', NULL, 'bathroom', '#00bcd4', 1, 5.0, 70, NOW(), NOW()),
(6, 1, '阳台', '1F', 'balcony', NULL, 'balcony', '#4caf50', 1, 6.0, 80, NOW(), NOW());

-- Rooms for household_id = 2
INSERT INTO rooms (id, household_id, name, floor, room_type, image_url, icon, theme_color, version, area, comfort, created_at, updated_at) VALUES
(7, 2, '客厅', '1F', 'living', NULL, 'living-room', '#3478f6', 1, 30.0, 88, NOW(), NOW()),
(8, 2, '卧室', '1F', 'bedroom', NULL, 'bedroom', '#e91e63', 1, 20.0, 92, NOW(), NOW()),
(9, 2, '书房', '1F', 'study', NULL, 'desk', '#673ab7', 1, 10.0, 85, NOW(), NOW());

-- ============================================================
-- 5. DEVICE GROUPS
-- ============================================================
INSERT INTO device_group (id, household_id, name, description, created_at) VALUES
(1, 1, '客厅设备组', '客厅的所有智能设备', NOW()),
(2, 1, '卧室设备组', '主卧和次卧的设备', NOW()),
(3, 1, '灯光组', '全屋智能灯光', NOW()),
(4, 2, '客厅设备', '李四家客厅设备', NOW());

-- ============================================================
-- 6. DEVICES (for household_id = 1)
-- device_id is the unique device identifier (like MAC or serial)
-- ============================================================
INSERT INTO devices (id, household_id, device_id, name, room, type, brand, status, connection, firmware, icon, color, image_url, group_id, last_online, created_at, updated_at) VALUES
-- 客厅设备
(1, 1, 'light_living_main', '客厅主灯', '客厅', 'light', 'Yeelight', 'online', 'wifi', '1.2.3', 'lightbulb', '#ffeb3b', NULL, 1, NOW(), NOW(), NOW()),
(2, 1, 'light_living_strip', '客厅氛围灯带', '客厅', 'light', 'Philips Hue', 'online', 'zigbee', '2.1.0', 'led-strip', '#ff5722', NULL, 3, NOW(), NOW(), NOW()),
(3, 1, 'tv_living', '客厅电视', '客厅', 'tv', 'Xiaomi', 'online', 'wifi', '3.0.1', 'tv', '#212121', NULL, 1, NOW(), NOW(), NOW()),
(4, 1, 'ac_living', '客厅空调', '客厅', 'air_conditioner', 'Gree', 'online', 'wifi', '1.5.0', 'air-conditioner', '#00bcd4', NULL, 1, NOW(), NOW(), NOW()),
(5, 1, 'speaker_living', '客厅音响', '客厅', 'speaker', 'Sonos', 'online', 'wifi', '2.0.0', 'speaker', '#757575', NULL, 1, NOW(), NOW(), NOW()),
(6, 1, 'curtain_living', '客厅窗帘', '客厅', 'curtain', 'Aqara', 'online', 'zigbee', '1.0.2', 'curtains', '#8d6e63', NULL, 1, NOW(), NOW(), NOW()),

-- 主卧设备
(7, 1, 'light_bedroom_main', '主卧主灯', '主卧', 'light', 'Yeelight', 'online', 'wifi', '1.2.3', 'lightbulb', '#ffeb3b', NULL, 2, NOW(), NOW(), NOW()),
(8, 1, 'light_bedside', '床头灯', '主卧', 'light', 'IKEA', 'online', 'zigbee', '1.1.0', 'lamp', '#ffc107', NULL, 3, NOW(), NOW(), NOW()),
(9, 1, 'ac_bedroom', '主卧空调', '主卧', 'air_conditioner', 'Midea', 'online', 'wifi', '1.4.0', 'air-conditioner', '#00bcd4', NULL, 2, NOW(), NOW(), NOW()),
(10, 1, 'humidifier_bedroom', '加湿器', '主卧', 'humidifier', 'Xiaomi', 'online', 'wifi', '2.0.0', 'humidifier', '#4fc3f7', NULL, 2, NOW(), NOW(), NOW()),

-- 次卧设备
(11, 1, 'light_guest_main', '次卧主灯', '次卧', 'light', 'Yeelight', 'offline', 'wifi', '1.2.3', 'lightbulb', '#ffeb3b', NULL, 2, NOW(), NOW(), NOW()),
(12, 1, 'fan_guest', '次卧风扇', '次卧', 'fan', 'Dyson', 'online', 'wifi', '1.0.0', 'fan', '#9e9e9e', NULL, 2, NOW(), NOW(), NOW()),

-- 厨房设备
(13, 1, 'fridge_kitchen', '冰箱', '厨房', 'refrigerator', 'Haier', 'online', 'wifi', '2.1.0', 'fridge', '#607d8b', NULL, NULL, NOW(), NOW(), NOW()),
(14, 1, 'hood_kitchen', '油烟机', '厨房', 'range_hood', 'Fotile', 'online', 'wifi', '1.0.0', 'fan', '#424242', NULL, NULL, NOW(), NOW(), NOW()),
(15, 1, 'sensor_gas', '燃气报警器', '厨房', 'sensor', 'Honeywell', 'online', 'wifi', '1.0.0', 'gas-meter', '#f44336', NULL, NULL, NOW(), NOW(), NOW()),

-- 卫生间设备
(16, 1, 'heater_bathroom', '浴霸', '卫生间', 'heater', 'Panasonic', 'online', 'wifi', '1.0.0', 'heat', '#ff5722', NULL, NULL, NOW(), NOW(), NOW()),
(17, 1, 'sensor_water', '漏水传感器', '卫生间', 'sensor', 'Aqara', 'online', 'zigbee', '1.0.0', 'water', '#2196f3', NULL, NULL, NOW(), NOW(), NOW()),

-- 阳台设备
(18, 1, 'light_balcony', '阳台灯', '阳台', 'light', 'Opple', 'online', 'wifi', '1.1.0', 'lightbulb', '#ffeb3b', NULL, NULL, NOW(), NOW(), NOW()),
(19, 1, 'washer_balcony', '洗衣机', '阳台', 'washer', 'LittleSwan', 'online', 'wifi', '2.0.0', 'washing-machine', '#1976d2', NULL, NULL, NOW(), NOW(), NOW()),
(20, 1, 'sensor_env_balcony', '环境传感器', '阳台', 'sensor', 'Qingping', 'online', 'bluetooth', '1.0.0', 'thermometer', '#00bcd4', NULL, NULL, NOW(), NOW(), NOW());

-- Devices for household_id = 2
INSERT INTO devices (id, household_id, device_id, name, room, type, brand, status, connection, firmware, icon, color, image_url, group_id, last_online, created_at, updated_at) VALUES
(21, 2, 'light_living_2', '客厅主灯', '客厅', 'light', 'Yeelight', 'online', 'wifi', '1.2.3', 'lightbulb', '#ffeb3b', NULL, 4, NOW(), NOW(), NOW()),
(22, 2, 'tv_living_2', '客厅电视', '客厅', 'tv', 'Hisense', 'online', 'wifi', '2.0.0', 'tv', '#212121', NULL, 4, NOW(), NOW(), NOW()),
(23, 2, 'ac_living_2', '客厅空调', '客厅', 'air_conditioner', 'Gree', 'online', 'wifi', '1.5.0', 'air-conditioner', '#00bcd4', NULL, 4, NOW(), NOW(), NOW()),
(24, 2, 'light_bedroom_2', '卧室主灯', '卧室', 'light', 'Philips', 'online', 'wifi', '1.1.0', 'lightbulb', '#ffeb3b', NULL, NULL, NOW(), NOW(), NOW()),
(25, 2, 'desk_lamp_2', '书桌台灯', '书房', 'light', 'BenQ', 'online', 'wifi', '1.0.0', 'lamp', '#ffc107', NULL, NULL, NOW(), NOW(), NOW());

-- ============================================================
-- 7. ROOM_DEVICES (link devices to rooms for household_id = 1)
-- ============================================================
INSERT INTO room_devices (id, room_id, device_id, group_name, favorite, sort_order) VALUES
-- 客厅
(1, 1, 1, '灯光', TRUE, 1),
(2, 1, 2, '灯光', TRUE, 2),
(3, 1, 3, '娱乐', TRUE, 3),
(4, 1, 4, '空调', FALSE, 4),
(5, 1, 5, '娱乐', FALSE, 5),
(6, 1, 6, '窗帘', FALSE, 6),
-- 主卧
(7, 2, 7, '灯光', TRUE, 1),
(8, 2, 8, '灯光', TRUE, 2),
(9, 2, 9, '空调', FALSE, 3),
(10, 2, 10, '环境', FALSE, 4),
-- 次卧
(11, 3, 11, '灯光', FALSE, 1),
(12, 3, 12, '电器', FALSE, 2),
-- 厨房
(13, 4, 13, '大型电器', TRUE, 1),
(14, 4, 14, '厨房电器', FALSE, 2),
(15, 4, 15, '安全', TRUE, 3),
-- 卫生间
(16, 5, 16, '取暖', FALSE, 1),
(17, 5, 17, '安全', TRUE, 2),
-- 阳台
(18, 6, 18, '灯光', FALSE, 1),
(19, 6, 19, '洗护', TRUE, 2),
(20, 6, 20, '环境', FALSE, 3);

-- Room devices for household_id = 2
INSERT INTO room_devices (id, room_id, device_id, group_name, favorite, sort_order) VALUES
(21, 7, 21, '灯光', TRUE, 1),
(22, 7, 22, '娱乐', TRUE, 2),
(23, 7, 23, '空调', FALSE, 3),
(24, 8, 24, '灯光', TRUE, 1),
(25, 9, 25, '灯光', TRUE, 1);

-- ============================================================
-- 8. DEVICE LOGS
-- ============================================================
INSERT INTO device_logs (id, device_id, action, message, created_at) VALUES
(1, 1, 'turn_on', '客厅主灯已开启，亮度 80%', NOW()),
(2, 1, 'brightness_change', '客厅主灯亮度调整为 100%', NOW()),
(3, 2, 'turn_on', '客厅氛围灯带已开启，模式：阅读', NOW()),
(4, 3, 'turn_on', '客厅电视已开启', NOW()),
(5, 4, 'turn_on', '客厅空调已开启，制冷模式 26°C', NOW()),
(6, 4, 'temp_change', '客厅空调温度调整为 24°C', NOW()),
(7, 7, 'turn_on', '主卧主灯已开启', NOW()),
(8, 8, 'turn_on', '床头灯已开启，暖光模式', NOW()),
(9, 9, 'turn_on', '主卧空调已开启，制热模式 22°C', NOW()),
(10, 13, 'alert', '冰箱门未关紧', NOW()),
(11, 15, 'alert', '检测到燃气浓度异常，已自动关闭阀门', NOW()),
(12, 17, 'alert', '卫生间检测到漏水，请立即检查', NOW()),
(13, 19, 'cycle_complete', '洗衣机洗涤完成', NOW()),
(14, 20, 'data_report', '环境数据上报：温度 25.5°C，湿度 60%', NOW());

-- ============================================================
-- 9. SCENE TEMPLATES
-- ============================================================
INSERT INTO scene_templates (id, name, description, icon, color, trigger_type, trigger_label, category, room_labels, device_count, recommended, steps_json, enabled, sort_order, created_at, updated_at) VALUES
('tpl_morning', '晨间模式', '一键开启美好一天：打开窗帘、开启灯光、播放新闻', 'weather-sunny', '#ff9800', 'schedule', '每天 07:00', '日常', '["客厅", "主卧"]', 5, TRUE, '[
  {"name": "打开客厅窗帘", "description": "打开客厅电动窗帘", "device_id": "curtain_living", "order": 1},
  {"name": "开启客厅主灯", "description": "客厅主灯亮度 50%", "device_id": "light_living_main", "order": 2},
  {"name": "开启主卧灯光", "description": "主卧主灯亮度 30%", "device_id": "light_bedroom_main", "order": 3},
  {"name": "播放早间新闻", "description": "客厅音响播放新闻", "device_id": "speaker_living", "order": 4},
  {"name": "开启空气净化", "description": "客厅空调开启净化模式", "device_id": "ac_living", "order": 5}
]', TRUE, 1, NOW(), NOW()),

('tpl_night', '晚安模式', '一键关闭全屋灯光、锁门、设置安防', 'weather-night', '#3f51b5', 'manual', '手动执行', '安防', '["客厅", "主卧", "次卧", "阳台"]', 6, TRUE, '[
  {"name": "关闭客厅主灯", "description": "关闭客厅主灯", "device_id": "light_living_main", "order": 1},
  {"name": "关闭氛围灯带", "description": "关闭客厅氛围灯带", "device_id": "light_living_strip", "order": 2},
  {"name": "关闭主卧灯光", "description": "关闭主卧所有灯光", "device_id": "light_bedroom_main", "order": 3},
  {"name": "关闭床头灯", "description": "关闭床头灯", "device_id": "light_bedside", "order": 4},
  {"name": "关闭次卧灯光", "description": "关闭次卧灯光", "device_id": "light_guest_main", "order": 5},
  {"name": "关闭阳台灯", "description": "关闭阳台灯", "device_id": "light_balcony", "order": 6}
]', TRUE, 2, NOW(), NOW()),

('tpl_movie', '观影模式', '打造家庭影院氛围：关灯、拉窗帘、开投影/电视、开音响', 'movie', '#e91e63', 'manual', '手动执行', '娱乐', '["客厅"]', 4, TRUE, '[
  {"name": "关闭主灯", "description": "关闭客厅主灯", "device_id": "light_living_main", "order": 1},
  {"name": "开启氛围灯带", "description": "氛围灯带设为暗红色 20%", "device_id": "light_living_strip", "order": 2},
  {"name": "关闭窗帘", "description": "关闭客厅窗帘遮光", "device_id": "curtain_living", "order": 3},
  {"name": "开启电视和音响", "description": "打开电视并切换到HDMI，开启音响", "device_id": "tv_living", "order": 4}
]', TRUE, 3, NOW(), NOW()),

('tpl_away', '离家模式', '离家时一键关闭非必要电器、开启安防、设置省电', 'exit-run', '#607d8b', 'manual', '手动执行', '安防', '["客厅", "主卧", "次卧", "厨房", "卫生间", "阳台"]', 8, TRUE, '[
  {"name": "关闭所有灯光", "description": "全屋灯光关闭", "device_id": "light_living_main", "order": 1},
  {"name": "关闭空调", "description": "关闭客厅和卧室空调", "device_id": "ac_living", "order": 2},
  {"name": "关闭电视音响", "description": "关闭娱乐设备", "device_id": "tv_living", "order": 3},
  {"name": "关闭窗帘", "description": "关闭所有窗帘", "device_id": "curtain_living", "order": 4},
  {"name": "开启燃气报警", "description": "启用厨房燃气监测", "device_id": "sensor_gas", "order": 5},
  {"name": "开启漏水监测", "description": "启用卫生间漏水监测", "device_id": "sensor_water", "order": 6},
  {"name": "设置空调省电", "description": "空调设为省电模式", "device_id": "ac_bedroom", "order": 7},
  {"name": "关闭洗衣机", "description": "确保洗衣机关闭", "device_id": "washer_balcony", "order": 8}
]', TRUE, 4, NOW(), NOW()),

('tpl_reading', '阅读模式', '书房/卧室阅读专用：护眼灯光、安静环境', 'book-open', '#4caf50', 'manual', '手动执行', '日常', '["主卧", "书房"]', 3, FALSE, '[
  {"name": "开启床头灯", "description": "床头灯暖光 40%", "device_id": "light_bedside", "order": 1},
  {"name": "关闭主灯", "description": "关闭主卧主灯", "device_id": "light_bedroom_main", "order": 2},
  {"name": "开启加湿器", "description": "开启加湿器保持湿度", "device_id": "humidifier_bedroom", "order": 3}
]', TRUE, 5, NOW(), NOW()),

('tpl_party', '派对模式', '聚会时的炫酷灯光和音乐', 'party', '#ff5722', 'manual', '手动执行', '娱乐', '["客厅"]', 4, FALSE, '[
  {"name": "关闭主灯", "description": "关闭主灯", "device_id": "light_living_main", "order": 1},
  {"name": "氛围灯动态", "description": "灯带跟随音乐变色", "device_id": "light_living_strip", "order": 2},
  {"name": "开启音响", "description": "蓝牙连接手机播放音乐", "device_id": "speaker_living", "order": 3},
  {"name": "关闭窗帘", "description": "拉上窗帘营造氛围", "device_id": "curtain_living", "order": 4}
]', TRUE, 6, NOW(), NOW());

-- ============================================================
-- 10. SCENES (created from templates or manually)
-- ============================================================
INSERT INTO scenes (id, household_id, created_by, name, description, icon, color, trigger_type, trigger_label, device_count, enabled, recommended, sort_order, room_names, monthly_execute_count, last_executed_at, high_risk, source_template_id, created_at, updated_at) VALUES
-- 家庭 1 的场景
('scene_morning_1', 1, 1, '我的晨间模式', '基于晨间模板自定义', 'weather-sunny', '#ff9800', 'schedule', '工作日 07:00', 5, TRUE, TRUE, 1, '["客厅", "主卧"]', 12, NOW(), FALSE, 'tpl_morning', NOW(), NOW()),
('scene_night_1', 1, 1, '我的晚安模式', '睡前一键关闭', 'weather-night', '#3f51b5', 'manual', '手动执行', 6, TRUE, TRUE, 2, '["客厅", "主卧", "次卧", "阳台"]', 25, NOW(), FALSE, 'tpl_night', NOW(), NOW()),
('scene_movie_1', 1, 1, '周末观影', '周五晚上看电影', 'movie', '#e91e63', 'manual', '手动执行', 4, TRUE, FALSE, 3, '["客厅"]', 8, NOW(), FALSE, 'tpl_movie', NOW(), NOW()),
('scene_away_1', 1, 1, '离家安防', '出门必开', 'exit-run', '#607d8b', 'manual', '手动执行', 8, TRUE, TRUE, 4, '["客厅", "主卧", "次卧", "厨房", "卫生间", "阳台"]', 15, NOW(), TRUE, 'tpl_away', NOW(), NOW()),
('scene_reading_1', 1, 2, '睡前阅读', '李四的阅读场景', 'book-open', '#4caf50', 'manual', '手动执行', 3, TRUE, FALSE, 5, '["主卧"]', 5, NOW(), FALSE, 'tpl_reading', NOW(), NOW()),
('scene_custom_1', 1, 1, '自定义：仅开客厅灯', '简单场景', 'lightbulb', '#ffeb3b', 'manual', '手动执行', 2, TRUE, FALSE, 6, '["客厅"]', 3, NOW(), FALSE, NULL, NOW(), NOW()),
('scene_disabled_1', 1, 1, '已停用的场景', '测试停用', 'power', '#9e9e9e', 'manual', '手动执行', 1, FALSE, FALSE, 7, '["客厅"]', 0, NULL, FALSE, NULL, NOW(), NOW()),

-- 家庭 2 的场景
('scene_morning_2', 2, 2, '李四的晨间', '简单晨间', 'weather-sunny', '#ff9800', 'schedule', '每天 07:30', 3, TRUE, TRUE, 1, '["客厅", "卧室"]', 10, NOW(), FALSE, 'tpl_morning', NOW(), NOW()),
('scene_night_2', 2, 2, '李四的晚安', '关灯睡觉', 'weather-night', '#3f51b5', 'manual', '手动执行', 4, TRUE, TRUE, 2, '["客厅", "卧室"]', 20, NOW(), FALSE, 'tpl_night', NOW(), NOW());

-- ============================================================
-- 11. SCENE STEPS
-- ============================================================
INSERT INTO scene_steps (id, scene_id, name, description, device_id, step_order) VALUES
-- scene_morning_1
('step_morning_1_1', 'scene_morning_1', '打开客厅窗帘', '打开客厅电动窗帘', 'curtain_living', 1),
('step_morning_1_2', 'scene_morning_1', '开启客厅主灯', '客厅主灯亮度 50%', 'light_living_main', 2),
('step_morning_1_3', 'scene_morning_1', '开启主卧灯光', '主卧主灯亮度 30%', 'light_bedroom_main', 3),
('step_morning_1_4', 'scene_morning_1', '播放早间新闻', '客厅音响播放新闻', 'speaker_living', 4),
('step_morning_1_5', 'scene_morning_1', '开启空气净化', '客厅空调开启净化模式', 'ac_living', 5),

-- scene_night_1
('step_night_1_1', 'scene_night_1', '关闭客厅主灯', '关闭客厅主灯', 'light_living_main', 1),
('step_night_1_2', 'scene_night_1', '关闭氛围灯带', '关闭客厅氛围灯带', 'light_living_strip', 2),
('step_night_1_3', 'scene_night_1', '关闭主卧灯光', '关闭主卧所有灯光', 'light_bedroom_main', 3),
('step_night_1_4', 'scene_night_1', '关闭床头灯', '关闭床头灯', 'light_bedside', 4),
('step_night_1_5', 'scene_night_1', '关闭次卧灯光', '关闭次卧灯光', 'light_guest_main', 5),
('step_night_1_6', 'scene_night_1', '关闭阳台灯', '关闭阳台灯', 'light_balcony', 6),

-- scene_movie_1
('step_movie_1_1', 'scene_movie_1', '关闭主灯', '关闭客厅主灯', 'light_living_main', 1),
('step_movie_1_2', 'scene_movie_1', '开启氛围灯带', '氛围灯带设为暗红色 20%', 'light_living_strip', 2),
('step_movie_1_3', 'scene_movie_1', '关闭窗帘', '关闭客厅窗帘遮光', 'curtain_living', 3),
('step_movie_1_4', 'scene_movie_1', '开启电视和音响', '打开电视并切换到HDMI，开启音响', 'tv_living', 4),

-- scene_away_1
('step_away_1_1', 'scene_away_1', '关闭所有灯光', '全屋灯光关闭', 'light_living_main', 1),
('step_away_1_2', 'scene_away_1', '关闭空调', '关闭客厅和卧室空调', 'ac_living', 2),
('step_away_1_3', 'scene_away_1', '关闭电视音响', '关闭娱乐设备', 'tv_living', 3),
('step_away_1_4', 'scene_away_1', '关闭窗帘', '关闭所有窗帘', 'curtain_living', 4),
('step_away_1_5', 'scene_away_1', '开启燃气报警', '启用厨房燃气监测', 'sensor_gas', 5),
('step_away_1_6', 'scene_away_1', '开启漏水监测', '启用卫生间漏水监测', 'sensor_water', 6),
('step_away_1_7', 'scene_away_1', '设置空调省电', '空调设为省电模式', 'ac_bedroom', 7),
('step_away_1_8', 'scene_away_1', '关闭洗衣机', '确保洗衣机关闭', 'washer_balcony', 8),

-- scene_reading_1
('step_reading_1_1', 'scene_reading_1', '开启床头灯', '床头灯暖光 40%', 'light_bedside', 1),
('step_reading_1_2', 'scene_reading_1', '关闭主灯', '关闭主卧主灯', 'light_bedroom_main', 2),
('step_reading_1_3', 'scene_reading_1', '开启加湿器', '开启加湿器保持湿度', 'humidifier_bedroom', 3),

-- scene_custom_1
('step_custom_1_1', 'scene_custom_1', '开启客厅主灯', '亮度 80%', 'light_living_main', 1),
('step_custom_1_2', 'scene_custom_1', '开启氛围灯带', '暖色 30%', 'light_living_strip', 2),

-- scene_disabled_1
('step_disabled_1_1', 'scene_disabled_1', '开启主灯', '测试', 'light_living_main', 1),

-- scene_morning_2
('step_morning_2_1', 'scene_morning_2', '开启客厅灯', '客厅主灯', 'light_living_2', 1),
('step_morning_2_2', 'scene_morning_2', '开启卧室灯', '卧室主灯', 'light_bedroom_2', 2),
('step_morning_2_3', 'scene_morning_2', '开启空调', '客厅空调', 'ac_living_2', 3),

-- scene_night_2
('step_night_2_1', 'scene_night_2', '关闭客厅灯', '关闭客厅主灯', 'light_living_2', 1),
('step_night_2_2', 'scene_night_2', '关闭卧室灯', '关闭卧室主灯', 'light_bedroom_2', 2),
('step_night_2_3', 'scene_night_2', '关闭空调', '关闭客厅空调', 'ac_living_2', 3),
('step_night_2_4', 'scene_night_2', '关闭台灯', '关闭书桌台灯', 'desk_lamp_2', 4);

-- ============================================================
-- 12. SCENE ROOMS (link scenes to rooms)
-- ============================================================
INSERT INTO scene_rooms (id, scene_id, room_id) VALUES
-- scene_morning_1
(1, 'scene_morning_1', 1),  -- 客厅
(2, 'scene_morning_1', 2),  -- 主卧
-- scene_night_1
(3, 'scene_night_1', 1),   -- 客厅
(4, 'scene_night_1', 2),   -- 主卧
(5, 'scene_night_1', 3),   -- 次卧
(6, 'scene_night_1', 6),   -- 阳台
-- scene_movie_1
(7, 'scene_movie_1', 1),   -- 客厅
-- scene_away_1
(8, 'scene_away_1', 1),    -- 客厅
(9, 'scene_away_1', 2),    -- 主卧
(10, 'scene_away_1', 3),   -- 次卧
(11, 'scene_away_1', 4),   -- 厨房
(12, 'scene_away_1', 5),   -- 卫生间
(13, 'scene_away_1', 6),   -- 阳台
-- scene_reading_1
(14, 'scene_reading_1', 2),  -- 主卧
-- scene_custom_1
(15, 'scene_custom_1', 1),   -- 客厅
-- scene_disabled_1
(16, 'scene_disabled_1', 1), -- 客厅
-- scene_morning_2
(17, 'scene_morning_2', 7),  -- 客厅(家庭2)
(18, 'scene_morning_2', 8),  -- 卧室(家庭2)
-- scene_night_2
(19, 'scene_night_2', 7),    -- 客厅(家庭2)
(20, 'scene_night_2', 8);    -- 卧室(家庭2)

-- ============================================================
-- 13. SCENE EXECUTION LOGS
-- ============================================================
INSERT INTO scene_execution_logs (id, scene_id, status, source, started_at, finished_at, message) VALUES
('exec_1', 'scene_morning_1', 'success', 'schedule', NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day' + INTERVAL '30 second', '晨间模式执行成功'),
('exec_2', 'scene_night_1', 'success', 'manual', NOW() - INTERVAL '2 hours', NOW() - INTERVAL '2 hours' + INTERVAL '15 second', '晚安模式执行成功'),
('exec_3', 'scene_movie_1', 'success', 'manual', NOW() - INTERVAL '3 days', NOW() - INTERVAL '3 days' + INTERVAL '20 second', '观影模式执行成功'),
('exec_4', 'scene_away_1', 'success', 'manual', NOW() - INTERVAL '1 week', NOW() - INTERVAL '1 week' + INTERVAL '45 second', '离家模式执行成功'),
('exec_5', 'scene_morning_1', 'success', 'schedule', NOW() - INTERVAL '2 days', NOW() - INTERVAL '2 days' + INTERVAL '28 second', '晨间模式执行成功'),
('exec_6', 'scene_night_1', 'failed', 'manual', NOW() - INTERVAL '5 days', NOW() - INTERVAL '5 days' + INTERVAL '10 second', '步骤3执行失败：主卧灯光离线'),
('exec_7', 'scene_custom_1', 'success', 'manual', NOW() - INTERVAL '1 hour', NOW() - INTERVAL '1 hour' + INTERVAL '5 second', '自定义场景执行成功');

-- ============================================================
-- 14. SCENE EXECUTION STEPS
-- ============================================================
INSERT INTO scene_execution_steps (id, execution_id, step_id, status, started_at, finished_at, message) VALUES
-- exec_1 (scene_morning_1 success)
('step_exec_1_1', 'exec_1', 'step_morning_1_1', 'success', NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day' + INTERVAL '5 second', '窗帘已打开'),
('step_exec_1_2', 'exec_1', 'step_morning_1_2', 'success', NOW() - INTERVAL '1 day' + INTERVAL '5 second', NOW() - INTERVAL '1 day' + INTERVAL '10 second', '主灯已开启'),
('step_exec_1_3', 'exec_1', 'step_morning_1_3', 'success', NOW() - INTERVAL '1 day' + INTERVAL '10 second', NOW() - INTERVAL '1 day' + INTERVAL '15 second', '卧室灯已开启'),
('step_exec_1_4', 'exec_1', 'step_morning_1_4', 'success', NOW() - INTERVAL '1 day' + INTERVAL '15 second', NOW() - INTERVAL '1 day' + INTERVAL '20 second', '新闻播放中'),
('step_exec_1_5', 'exec_1', 'step_morning_1_5', 'success', NOW() - INTERVAL '1 day' + INTERVAL '20 second', NOW() - INTERVAL '1 day' + INTERVAL '30 second', '净化模式已开启'),

-- exec_2 (scene_night_1 success)
('step_exec_2_1', 'exec_2', 'step_night_1_1', 'success', NOW() - INTERVAL '2 hours', NOW() - INTERVAL '2 hours' + INTERVAL '3 second', '主灯已关闭'),
('step_exec_2_2', 'exec_2', 'step_night_1_2', 'success', NOW() - INTERVAL '2 hours' + INTERVAL '3 second', NOW() - INTERVAL '2 hours' + INTERVAL '6 second', '灯带已关闭'),
('step_exec_2_3', 'exec_2', 'step_night_1_3', 'success', NOW() - INTERVAL '2 hours' + INTERVAL '6 second', NOW() - INTERVAL '2 hours' + INTERVAL '9 second', '卧室灯已关闭'),
('step_exec_2_4', 'exec_2', 'step_night_1_4', 'success', NOW() - INTERVAL '2 hours' + INTERVAL '9 second', NOW() - INTERVAL '2 hours' + INTERVAL '12 second', '床头灯已关闭'),
('step_exec_2_5', 'exec_2', 'step_night_1_5', 'success', NOW() - INTERVAL '2 hours' + INTERVAL '12 second', NOW() - INTERVAL '2 hours' + INTERVAL '14 second', '次卧灯已关闭'),
('step_exec_2_6', 'exec_2', 'step_night_1_6', 'success', NOW() - INTERVAL '2 hours' + INTERVAL '14 second', NOW() - INTERVAL '2 hours' + INTERVAL '15 second', '阳台灯已关闭'),

-- exec_3 (scene_movie_1 success)
('step_exec_3_1', 'exec_3', 'step_movie_1_1', 'success', NOW() - INTERVAL '3 days', NOW() - INTERVAL '3 days' + INTERVAL '5 second', '主灯已关闭'),
('step_exec_3_2', 'exec_3', 'step_movie_1_2', 'success', NOW() - INTERVAL '3 days' + INTERVAL '5 second', NOW() - INTERVAL '3 days' + INTERVAL '10 second', '氛围灯已设置'),
('step_exec_3_3', 'exec_3', 'step_movie_1_3', 'success', NOW() - INTERVAL '3 days' + INTERVAL '10 second', NOW() - INTERVAL '3 days' + INTERVAL '15 second', '窗帘已关闭'),
('step_exec_3_4', 'exec_3', 'step_movie_1_4', 'success', NOW() - INTERVAL '3 days' + INTERVAL '15 second', NOW() - INTERVAL '3 days' + INTERVAL '20 second', '电视音响已开启'),

-- exec_4 (scene_away_1 success)
('step_exec_4_1', 'exec_4', 'step_away_1_1', 'success', NOW() - INTERVAL '1 week', NOW() - INTERVAL '1 week' + INTERVAL '5 second', '全屋灯光已关闭'),
('step_exec_4_2', 'exec_4', 'step_away_1_2', 'success', NOW() - INTERVAL '1 week' + INTERVAL '5 second', NOW() - INTERVAL '1 week' + INTERVAL '12 second', '空调已关闭'),
('step_exec_4_3', 'exec_4', 'step_away_1_3', 'success', NOW() - INTERVAL '1 week' + INTERVAL '12 second', NOW() - INTERVAL '1 week' + INTERVAL '18 second', '娱乐设备已关闭'),
('step_exec_4_4', 'exec_4', 'step_away_1_4', 'success', NOW() - INTERVAL '1 week' + INTERVAL '18 second', NOW() - INTERVAL '1 week' + INTERVAL '25 second', '窗帘已关闭'),
('step_exec_4_5', 'exec_4', 'step_away_1_5', 'success', NOW() - INTERVAL '1 week' + INTERVAL '25 second', NOW() - INTERVAL '1 week' + INTERVAL '30 second', '燃气监测已启用'),
('step_exec_4_6', 'exec_4', 'step_away_1_6', 'success', NOW() - INTERVAL '1 week' + INTERVAL '30 second', NOW() - INTERVAL '1 week' + INTERVAL '35 second', '漏水监测已启用'),
('step_exec_4_7', 'exec_4', 'step_away_1_7', 'success', NOW() - INTERVAL '1 week' + INTERVAL '35 second', NOW() - INTERVAL '1 week' + INTERVAL '40 second', '空调省电模式已设置'),
('step_exec_4_8', 'exec_4', 'step_away_1_8', 'success', NOW() - INTERVAL '1 week' + INTERVAL '40 second', NOW() - INTERVAL '1 week' + INTERVAL '45 second', '洗衣机已确认关闭'),

-- exec_6 (scene_night_1 failed - step 3)
('step_exec_6_1', 'exec_6', 'step_night_1_1', 'success', NOW() - INTERVAL '5 days', NOW() - INTERVAL '5 days' + INTERVAL '2 second', '主灯已关闭'),
('step_exec_6_2', 'exec_6', 'step_night_1_2', 'success', NOW() - INTERVAL '5 days' + INTERVAL '2 second', NOW() - INTERVAL '5 days' + INTERVAL '4 second', '灯带已关闭'),
('step_exec_6_3', 'exec_6', 'step_night_1_3', 'failed', NOW() - INTERVAL '5 days' + INTERVAL '4 second', NOW() - INTERVAL '5 days' + INTERVAL '8 second', '设备离线：主卧主灯'),
('step_exec_6_4', 'exec_6', 'step_night_1_4', 'skipped', NULL, NULL, '上一步骤失败，跳过执行'),
('step_exec_6_5', 'exec_6', 'step_night_1_5', 'skipped', NULL, NULL, '上一步骤失败，跳过执行'),
('step_exec_6_6', 'exec_6', 'step_night_1_6', 'skipped', NULL, NULL, '上一步骤失败，跳过执行'),

-- exec_7 (scene_custom_1 success)
('step_exec_7_1', 'exec_7', 'step_custom_1_1', 'success', NOW() - INTERVAL '1 hour', NOW() - INTERVAL '1 hour' + INTERVAL '3 second', '主灯已开启'),
('step_exec_7_2', 'exec_7', 'step_custom_1_2', 'success', NOW() - INTERVAL '1 hour' + INTERVAL '3 second', NOW() - INTERVAL '1 hour' + INTERVAL '5 second', '灯带已开启');

-- ============================================================
-- 15. SCENE DRAFTS
-- ============================================================
INSERT INTO scene_drafts (id, household_id, created_by, payload_json, updated_at) VALUES
('draft_1', 1, 1, '{"name":"新建场景草稿","description":"正在编辑中","icon":"plus","color":"var(--color-primary-600)","trigger_type":"manual","trigger_label":"手动执行","enabled":true,"steps":[{"name":"开启客厅灯","description":"","device_id":"light_living_main","order":1}]}', NOW()),
('draft_2', 1, 2, '{"name":"李四的草稿","description":"想做个派对场景","icon":"party","color":"#ff5722","trigger_type":"manual","trigger_label":"手动执行","enabled":true,"steps":[{"name":"关主灯","description":"","device_id":"light_living_main","order":1},{"name":"开灯带","description":"彩虹模式","device_id":"light_living_strip","order":2}]}', NOW()),
('draft_3', 2, 2, '{"name":"家庭2草稿","description":"测试","icon":"home","color":"#3478f6","trigger_type":"manual","trigger_label":"手动执行","enabled":true,"steps":[]}', NOW());

-- ============================================================
-- 16. ROOM ACTIVITY LOGS
-- ============================================================
INSERT INTO room_activity_logs (id, room_id, device_id, source, event, result, duration_ms, tags_json, detail_json, occurred_at) VALUES
(1, 1, 1, 'scene', '执行场景：我的晨间模式', 'success', 30000, '["scene", "schedule"]', '{"scene_id":"scene_morning_1"}', NOW() - INTERVAL '1 day'),
(2, 1, 3, 'user', '手动开启电视', 'success', 5000, '["manual", "tv"]', '{"device_id":"tv_living"}', NOW() - INTERVAL '2 hours'),
(3, 2, 7, 'scene', '执行场景：我的晚安模式', 'success', 15000, '["scene", "manual"]', '{"scene_id":"scene_night_1"}', NOW() - INTERVAL '2 hours'),
(4, 4, 15, 'alert', '燃气报警器触发', 'success', 1000, '["alert", "safety", "gas"]', '{"device_id":"sensor_gas","level":"high"}', NOW() - INTERVAL '3 days'),
(5, 5, 17, 'alert', '漏水传感器触发', 'success', 800, '["alert", "safety", "water"]', '{"device_id":"sensor_water"}', NOW() - INTERVAL '1 week'),
(6, 1, 19, 'device', '洗衣机完成洗涤', 'success', 2000, '["notification", "washer"]', '{"device_id":"washer_balcony","cycle":"cotton"}', NOW() - INTERVAL '4 hours'),
(7, 6, 20, 'device', '环境数据上报', 'success', 100, '["sensor", "environment"]', '{"device_id":"sensor_env_balcony","temperature":25.5,"humidity":60}', NOW() - INTERVAL '30 minutes');

-- ============================================================
-- VERIFICATION QUERIES (run after insert to verify)
-- ============================================================
-- SELECT 'users' as table_name, COUNT(*) as count FROM users
-- UNION ALL SELECT 'households', COUNT(*) FROM households
-- UNION ALL SELECT 'household_memberships', COUNT(*) FROM household_memberships
-- UNION ALL SELECT 'rooms', COUNT(*) FROM rooms
-- UNION ALL SELECT 'devices', COUNT(*) FROM devices
-- UNION ALL SELECT 'device_group', COUNT(*) FROM device_group
-- UNION ALL SELECT 'room_devices', COUNT(*) FROM room_devices
-- UNION ALL SELECT 'device_logs', COUNT(*) FROM device_logs
-- UNION ALL SELECT 'scene_templates', COUNT(*) FROM scene_templates
-- UNION ALL SELECT 'scenes', COUNT(*) FROM scenes
-- UNION ALL SELECT 'scene_steps', COUNT(*) FROM scene_steps
-- UNION ALL SELECT 'scene_rooms', COUNT(*) FROM scene_rooms
-- UNION ALL SELECT 'scene_execution_logs', COUNT(*) FROM scene_execution_logs
-- UNION ALL SELECT 'scene_execution_steps', COUNT(*) FROM scene_execution_steps
-- UNION ALL SELECT 'scene_drafts', COUNT(*) FROM scene_drafts
-- UNION ALL SELECT 'room_activity_logs', COUNT(*) FROM room_activity_logs;