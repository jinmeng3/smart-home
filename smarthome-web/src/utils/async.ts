/**
 * 延迟指定毫秒数后 resolve，用于模拟异步操作或最小展示时长。
 * @param ms 延迟毫秒数
 */
export const sleep = (ms: number) =>
  new Promise<void>((resolve) => window.setTimeout(resolve, ms));