/**
 * 极简测试运行器（无外部依赖）。
 *
 * 用法：
 *   import { describe, it, expect } from "./runner.mjs";
 *   describe("...", () => { it("...", () => { expect(...).toBe(...) }) });
 *
 * 支持：describe / it / expect().toBe / toEqual / toThrow / toBeTruthy / toBeFalsy / toContain / toMatch。
 * 输出 TAP 风格摘要。
 */

let stats = { passed: 0, failed: 0, suites: 0, total: 0 };
const failures = [];

const formatValue = (v) => {
  if (typeof v === "string") return JSON.stringify(v);
  if (typeof v === "function") return "[Function]";
  if (v instanceof Error) return `${v.name}: ${v.message}`;
  if (v === undefined) return "undefined";
  return JSON.stringify(v);
};

const deepEqual = (a, b) => {
  if (a === b) return true;
  if (a === null || b === null) return false;
  if (typeof a !== typeof b) return false;
  if (typeof a === "object") {
    if (Array.isArray(a) !== Array.isArray(b)) return false;
    const aKeys = Object.keys(a);
    const bKeys = Object.keys(b);
    if (aKeys.length !== bKeys.length) return false;
    return aKeys.every((k) => deepEqual(a[k], b[k]));
  }
  return false;
};

const matchValue = (actual, expected) => {
  if (expected instanceof RegExp) {
    return typeof actual === "string" && expected.test(actual);
  }
  if (typeof expected === "function") {
    return expected(actual);
  }
  return deepEqual(actual, expected);
};

const expect = (actual) => {
  const fail = (msg) => {
    throw new Error(`Expectation failed: ${msg}\n  actual:   ${formatValue(actual)}`);
  };
  return {
    toBe(expected) {
      if (actual !== expected) {
        fail(`expected ${formatValue(actual)} to be ${formatValue(expected)}`);
      }
    },
    toEqual(expected) {
      if (!deepEqual(actual, expected)) {
        fail(`expected ${formatValue(actual)} to equal ${formatValue(expected)}`);
      }
    },
    toBeTruthy() {
      if (!actual) fail("expected truthy value");
    },
    toBeFalsy() {
      if (actual) fail(`expected falsy value, got ${formatValue(actual)}`);
    },
    toBeNull() {
      if (actual !== null) fail(`expected null, got ${formatValue(actual)}`);
    },
    toBeUndefined() {
      if (actual !== undefined) fail(`expected undefined, got ${formatValue(actual)}`);
    },
    toContain(item) {
      if (typeof actual === "string") {
        if (!actual.includes(item)) fail(`expected "${actual}" to contain "${item}"`);
      } else if (Array.isArray(actual)) {
        if (!actual.includes(item)) fail(`expected array to contain ${formatValue(item)}`);
      } else {
        fail(`toContain not supported on ${typeof actual}`);
      }
    },
    toMatch(expected) {
      if (!matchValue(actual, expected)) {
        fail(`expected ${formatValue(actual)} to match ${formatValue(expected)}`);
      }
    },
    toThrow(matcher) {
      if (typeof actual !== "function") fail("toThrow requires a function");
      try {
        actual();
        fail("expected function to throw");
      } catch (e) {
        if (matcher) {
          const ok =
            matcher instanceof RegExp
              ? matcher.test(e.message)
              : typeof matcher === "string"
                ? e.message.includes(matcher)
                : e instanceof matcher;
          if (!ok) fail(`thrown error did not match: ${formatValue(e)}`);
        }
      }
    },
    toBeGreaterThan(n) {
      if (!(actual > n)) fail(`expected ${formatValue(actual)} > ${n}`);
    },
    toHaveLength(n) {
      if (!actual || actual.length !== n) {
        fail(`expected length ${n}, got ${actual?.length}`);
      }
    },
  };
};

// 持续累加的任务列表 + 一个最终 await 用的 promise
const allTasks = [];
let finalTask = Promise.resolve();

const describe = (name, fn) => {
  stats.suites += 1;
  console.log(`\n\x1b[1m${name}\x1b[0m`);
  // fn 是同步函数体，里面调 it() 顺序把任务添加到 allTasks
  fn();
};

const it = (name, fn) => {
  const task = finalTask.then(async () => {
    stats.total += 1;
    try {
      await fn();
      stats.passed += 1;
      console.log(`  \x1b[32m✓\x1b[0m ${name}`);
    } catch (err) {
      stats.failed += 1;
      console.log(`  \x1b[31m✗\x1b[0m ${name}\n    ${(err.stack || err.message).split("\n").slice(0, 4).join("\n    ")}`);
      failures.push({ name, error: err });
    }
  });
  allTasks.push(task);
  finalTask = task;
  return task;
};

const runAll = async (suites) => {
  for (const suite of suites) {
    suite();
  }
  // 顺序等：按注册顺序等所有 it 任务结束（避免并发污染 jiti 模块单例）
  for (const task of allTasks) {
    await task;
  }
  console.log(
    `\n\x1b[1m总计：${stats.total} 个用例，${stats.passed} 通过，${stats.failed} 失败\x1b[0m`,
  );
  if (failures.length > 0) {
    console.log("\n\x1b[31m失败详情：\x1b[0m");
    for (const f of failures) {
      console.log(`  ✗ ${f.name}`);
      console.log(`    ${f.error.stack || f.error.message}`);
    }
    process.exit(1);
  }
};

export { describe, it, expect, runAll };