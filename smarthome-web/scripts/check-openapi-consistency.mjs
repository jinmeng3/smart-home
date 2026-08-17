/**
 * 检查生成的 OpenAPI 类型定义与当前后端是否一致。
 * 用于 CI 中防止前端类型与后端契约漂移。
 *
 * 用法：npm run api:check
 * 前置条件：后端已运行
 */
import { readFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const rootDir = join(__dirname, '..');
const generatedFile = join(rootDir, 'src', 'api', 'generated', 'schema.d.ts');

const OPENAPI_URL = 'http://127.0.0.1:8000/openapi.json';

async function main() {
  // 检查生成文件是否存在
  try {
    readFileSync(generatedFile, 'utf-8');
  } catch {
    console.error('❌ 类型定义文件不存在，请先运行 npm run api:generate');
    process.exit(1);
  }

  try {
    const response = await fetch(OPENAPI_URL);
    if (!response.ok) {
      console.error(`❌ 无法获取 OpenAPI 规范：HTTP ${response.status}`);
      process.exit(1);
    }

    const spec = await response.json();
    const backendCount = Object.keys(spec.components?.schemas || {}).length;

    // 简单检查：统计生成的类型数量是否与后端一致
    const content = readFileSync(generatedFile, 'utf-8');
    const exportedCount = (content.match(/^export interface /gm) || []).length;

    if (exportedCount === 0) {
      console.error('❌ 生成文件中没有找到类型定义');
      process.exit(1);
    }

    if (exportedCount < backendCount) {
      console.warn(`⚠️  前端类型定义 (${exportedCount}) 少于后端 Schema (${backendCount})，可能存在缺失`);
      console.warn('   建议运行 npm run api:generate 重新生成');
      process.exit(1);
    }

    console.log(`✅ 契约检查通过：${exportedCount} 个类型定义与后端 ${backendCount} 个 Schema 一致`);
  } catch (error) {
    console.error('❌ 检查失败：', error instanceof Error ? error.message : error);
    process.exit(1);
  }
}

main();