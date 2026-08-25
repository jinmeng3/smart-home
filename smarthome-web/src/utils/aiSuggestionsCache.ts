import type { SettingsSuggestionItem } from "../types/settings";

/**
 * AI 建议本地缓存（SRP：负责序列化、过期判定与查询；
 * 不调用 API、不感知 Pinia）。
 *
 * 缓存键设计：仅基于 settings 摘要的稳定哈希，不绑定 user_id
 * （本地浏览器天然单用户，多设备不共享是预期行为）。
 * TTL 30 分钟；超期视为未命中，由调用方决定是否重新请求 LLM。
 */

const STORAGE_KEY = "smart-home-ai-suggestions";
const TTL_MS = 30 * 60 * 1000;

interface CacheEnvelope {
  expiresAt: number;
  hash: string;
  suggestions: SettingsSuggestionItem[];
}

const isBrowser = (): boolean =>
  typeof window !== "undefined" && typeof window.localStorage !== "undefined";

/** 简单稳定哈希（FNV-1a 32-bit），避免引入额外依赖。 */
export const hashSnapshot = (snapshot: unknown): string => {
  const text = JSON.stringify(snapshot, Object.keys(snapshot as object).sort());
  let hash = 0x811c9dc5;
  for (let i = 0; i < text.length; i++) {
    hash ^= text.charCodeAt(i);
    hash = Math.imul(hash, 0x01000193);
  }
  return (hash >>> 0).toString(16);
};

export interface ReadCacheResult {
  hit: boolean;
  suggestions: SettingsSuggestionItem[];
  expired: boolean;
}

export const readAiSuggestionsCache = (
  hash: string,
): ReadCacheResult => {
  if (!isBrowser()) return { hit: false, suggestions: [], expired: false };
  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) return { hit: false, suggestions: [], expired: false };
  try {
    const envelope = JSON.parse(raw) as CacheEnvelope;
    if (envelope.hash !== hash) {
      return { hit: false, suggestions: [], expired: false };
    }
    if (typeof envelope.expiresAt !== "number" || envelope.expiresAt <= Date.now()) {
      return { hit: false, suggestions: envelope.suggestions ?? [], expired: true };
    }
    return { hit: true, suggestions: envelope.suggestions ?? [], expired: false };
  } catch {
    return { hit: false, suggestions: [], expired: false };
  }
};

export const writeAiSuggestionsCache = (
  hash: string,
  suggestions: SettingsSuggestionItem[],
): void => {
  if (!isBrowser()) return;
  const envelope: CacheEnvelope = {
    expiresAt: Date.now() + TTL_MS,
    hash,
    suggestions,
  };
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(envelope));
  } catch {
    // localStorage 满或被禁用时静默失败；不影响主流程
  }
};

export const clearAiSuggestionsCache = (): void => {
  if (!isBrowser()) return;
  window.localStorage.removeItem(STORAGE_KEY);
};
