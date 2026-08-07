/** 统一加载状态（低端机性能优化方案 — Store 与界面行为）。 */
export type LoadingState = "idle" | "loading" | "success" | "error";

export const isIdle = (s: LoadingState) => s === "idle";
export const isLoading = (s: LoadingState) => s === "loading";
export const isSuccess = (s: LoadingState) => s === "success";
export const isError = (s: LoadingState) => s === "error";