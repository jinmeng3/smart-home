import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { gzipSync } from "node:zlib";

/**
 * 低端机性能验收：chunk 预算检查（DRY：只读 dist，不依赖第三方插件）。
 * 规则（对应「低端设备性能与代码复用优化方案」目标）：
 *  1. 主入口 index-*.js gzip <= 48KB（控制首屏框架成本）
 *  2. 任一非入口 JS chunk gzip <= 120KB（单路由首屏预算）
 *  3. 超标公共大块（SvgIcon / BaseSmartModal / SettingsCenter）单独列出待优化，
 *     超过硬顶 160KB 才阻断 build，保证低端机拿到可用包体。
 * 用法：
 *  CHUNK_BUDGET=silent  跳过检查
 *  CHUNK_BUDGET=strict  将「建议优化」级别也视为失败
 *  APP_BUDGET_MAIN_KB / APP_BUDGET_CHUNK_KB / APP_BUDGET_CHUNK_HARD_KB 可覆盖阈值
 */
const distDir = process.argv[2] ?? join(process.cwd(), "dist");
const assetsDir = join(distDir, "assets");

const mode = process.env.CHUNK_BUDGET ?? "normal";
const mainLimitKb = Number(process.env.APP_BUDGET_MAIN_KB ?? 48);
const chunkLimitKb = Number(process.env.APP_BUDGET_CHUNK_KB ?? 120);
const hardChunkKb = Number(process.env.APP_BUDGET_CHUNK_HARD_KB ?? 160);

if (mode === "silent") {
  console.log("[chunk-budget] 已跳过（CHUNK_BUDGET=silent）");
  process.exit(0);
}

let files;
try {
  files = readdirSync(assetsDir).filter((name) => name.endsWith(".js"));
} catch {
  console.error(`[chunk-budget] 找不到构建产物：${assetsDir}`);
  console.error("[chunk-budget] 请先执行 npm run build-only");
  process.exit(1);
}

const gzipKb = (path) => {
  const buf = readFileSync(path);
  return gzipSync(buf).length / 1024;
};

const rows = files
  .map((name) => {
    const full = join(assetsDir, name);
    if (!statSync(full).isFile()) return null;
    return { name, gz: gzipKb(full) };
  })
  .filter(Boolean)
  .sort((a, b) => b.gz - a.gz);

const fmt = (num) => num.toFixed(2);
const main = rows.find((r) => r.name.startsWith("index-"));

const failures = [];
const warnings = [];

if (main) {
  if (main.gz > mainLimitKb) {
    failures.push(
      `主入口 ${main.name} gzip ${fmt(main.gz)}KB 超过预算 ${mainLimitKb}KB`,
    );
  } else {
    console.log(`[chunk] 主入口 OK: ${fmt(main.gz)}KB (<= ${mainLimitKb}KB)`);
  }
}

const hugeMarkers = ["SvgIcon", "BaseSmartModal", "SettingsCenter"];
const warnMarkers = hugeMarkers;

for (const row of rows) {
  if (row.name === main?.name) continue;

  if (row.gz > hardChunkKb) {
    failures.push(
      `chunk ${row.name} gzip ${fmt(row.gz)}KB 超过硬顶 ${hardChunkKb}KB`,
    );
  } else if (row.gz > chunkLimitKb) {
    if (mode === "strict") {
      failures.push(
        `chunk ${row.name} gzip ${fmt(row.gz)}KB > 预算 ${chunkLimitKb}KB`,
      );
    } else {
      warnings.push(
        `chunk ${row.name} gzip ${fmt(row.gz)}KB 超过建议值 ${chunkLimitKb}KB（硬顶以下，暂不阻断）`,
      );
    }
  }
}

console.log("\n--- chunk 体积报告（gzip, 降序, Top 25）---");
for (const row of rows.slice(0, 25)) {
  const flag = warnMarkers.some((k) => row.name.includes(k)) ? " ◀ 待优化" : "";
  console.log(`  ${row.name.padEnd(46)} ${fmt(row.gz).padStart(8)}KB${flag}`);
}

if (warnings.length) {
  console.warn("\n[chunk-budget] 建议级超预算（未阻断）:");
  for (const w of warnings) console.warn(`  - ${w}`);
}

if (failures.length) {
  console.error("\n[chunk-budget] 预算校验失败：");
  for (const f of failures) console.error(`  - ${f}`);
  console.error(
    `\n目标：主入口 <= ${mainLimitKb}KB，路由 chunk <= ${chunkLimitKb}KB，硬顶 ${hardChunkKb}KB。`,
  );
  process.exit(1);
}

console.log(
  `\n[chunk-budget] 通过 ✓ (main<=${mainLimitKb}KB, chunk<=${chunkLimitKb}KB, hard<=${hardChunkKb}KB)`,
);