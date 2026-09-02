/**
 * 测试环境 setup：模拟浏览器 API，供 client.ts 解析响应测试使用。
 *
 * 设计原则：只装 client.ts 实际用到的 API，多余的避免污染。
 */

const storage = new Map();
const listeners = new Map();

const setupBrowserGlobals = () => {
  if (globalThis.window) return;

  globalThis.window = {
    sessionStorage: {
      getItem: (key) => (storage.has(key) ? storage.get(key) : null),
      setItem: (key, value) => storage.set(key, String(value)),
      removeItem: (key) => storage.delete(key),
      clear: () => storage.clear(),
      get length() {
        return storage.size;
      },
      key: (i) => Array.from(storage.keys())[i] ?? null,
    },
    dispatchEvent: (event) => {
      const arr = listeners.get(event.type) || [];
      for (const cb of arr) {
        try {
          cb(event);
        } catch (e) {
          console.error("[test setup] listener error", e);
        }
      }
      return true;
    },
    addEventListener: (type, cb) => {
      if (!listeners.has(type)) listeners.set(type, []);
      listeners.get(type).push(cb);
    },
    removeEventListener: (type, cb) => {
      const arr = listeners.get(type) || [];
      listeners.set(
        type,
        arr.filter((fn) => fn !== cb),
      );
    },
  };

  // Event 类（client.ts 用 new Event）
  if (typeof globalThis.Event === "undefined") {
    globalThis.Event = class Event {
      constructor(type) {
        this.type = type;
      }
    };
  }
};

const clearBrowserState = () => {
  storage.clear();
  listeners.clear();
};

export { setupBrowserGlobals, clearBrowserState, storage, listeners };