/**
 * 在数组中切换某个值的存在状态：存在则移除，不存在则添加。
 * @param arr 目标数组
 * @param value 要切换的值
 */
export const toggleValue = <T>(arr: T[], value: T) => {
  const index = arr.indexOf(value);
  if (index >= 0) {
    arr.splice(index, 1);
  } else {
    arr.push(value);
  }
};