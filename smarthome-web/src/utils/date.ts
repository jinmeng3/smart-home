/**
 * 将 ISO 时间戳格式化为 "YYYY-MM-DD HH:mm" 的本地展示格式。
 * @param value ISO 时间字符串
 * @param fallback 无法解析时的兜底文案（如 "从未在线"）
 */
export const formatDeviceTimestamp = (value: string, fallback = "") => {
  const match = value.match(/^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})/);

  if (match) {
    return `${match[1]} ${match[2]}`;
  }

  return fallback || value;
};
