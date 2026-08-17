/**
 * 检查生产构建的 chunk 体积预算。
 * 超过 250KB 的 chunk 输出警告，超过 500KB 输出错误。
 */
import { readdirSync, statSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const distAssetsDir = join(__dirname, '..', 'dist', 'assets');

const WARN_LIMIT = 250 * 1024; // 250KB
const ERROR_LIMIT = 500 * 1024; // 500KB

let hasError = false;
let assets;

try {
  assets = readdirSync(distAssetsDir);
} catch {
  console.log('⚠️  dist 目录不存在，跳过 chunk 预算检查');
  process.exit(0);
}

for (const file of assets) {
  if (!file.endsWith('.js') && !file.endsWith('.css')) continue;
  const size = statSync(join(distAssetsDir, file)).size;
  const sizeKB = (size / 1024).toFixed(1);

  if (size > ERROR_LIMIT) {
    console.error(`❌  ${file}  ${sizeKB}KB (超过 ${ERROR_LIMIT / 1024}KB 预算)`);
    hasError = true;
  } else if (size > WARN_LIMIT) {
    console.warn(`⚠️  ${file}  ${sizeKB}KB (接近 ${WARN_LIMIT / 1024}KB 预算)`);
  }
}

if (hasError) {
  console.error('\n❌ 存在超过预算的 chunk，请优化或拆分大模块');
  process.exit(1);
} else {
  console.log('✅ 所有 chunk 体积在预算范围内');
}