/**
 * 从后端生成的 OpenAPI JSON 中提取类型定义，输出为 TypeScript 类型文件。
 * 用法：npm run api:generate
 *
 * 前置条件：后端已运行并可通过 /openapi.json 获取 OpenAPI 规范。
 */
import { writeFileSync, readFileSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { tmpdir } from 'node:os';

const __dirname = dirname(fileURLToPath(import.meta.url));
const rootDir = join(__dirname, '..');
const apiDir = join(rootDir, 'src', 'api', 'generated');

const OPENAPI_URL = 'http://127.0.0.1:8000/openapi.json';
// 回退：本地 openapi.json（先后端 export:backend 生成到 smarthome-api/openapi.json）
const LOCAL_FALLBACKS = [
  process.env.OPENAPI_JSON_PATH,
  join(rootDir, '..', 'smarthome-api', 'openapi.json'),
  join(tmpdir(), 'openapi.json'),
].filter(Boolean);
const OUTPUT_PATH = join(apiDir, 'schema.d.ts');

async function main() {
  let spec;
  let usedSource = OPENAPI_URL;
  try {
    const response = await fetch(OPENAPI_URL);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    spec = await response.json();
  } catch (httpError) {
    const localPath = LOCAL_FALLBACKS.find((p) => existsSync(p));
    if (!localPath) {
      console.error(`❌ 无法获取 OpenAPI 规范：${httpError.message}`);
      console.error(`   也未找到本地回退文件，尝试过：`);
      LOCAL_FALLBACKS.forEach((p) => console.error(`     - ${p}`));
      console.error(`   请先运行：cd smarthome-api && python -c "import json; from app.main import app; json.dump(app.openapi(), open('openapi.json','w'), ensure_ascii=False)"`);
      process.exit(1);
    }
    spec = JSON.parse(readFileSync(localPath, 'utf-8'));
    usedSource = `local file ${localPath}`;
  }
  console.log(`[generate] 数据源：${usedSource}`);
  const schemas = (spec.components && spec.components.schemas) || {};

  let output = `// 自动生成，请勿手动修改。\n`;
  output += `// 生成时间: ${new Date().toISOString()}\n`;
  output += `// 来源: ${usedSource}\n\n`;

  for (const [name, schema] of Object.entries(schemas)) {
    output += `export interface ${name} {\n`;
    const properties = schema.properties || {};
    const required = Array.isArray(schema.required) ? schema.required : [];
    for (const [propName, propSchema] of Object.entries(properties)) {
      const ps = propSchema || {};
      const type = ps.type || 'unknown';
      const optional = required.includes(propName) ? '' : '?';
      const tsType = mapType(type, ps);
      const description = ps.description ? ` /* ${ps.description} */` : '';
      output += `  ${propName}${optional}: ${tsType};${description}\n`;
    }
    output += `}\n\n`;
  }

  writeFileSync(OUTPUT_PATH, output, 'utf-8');
  console.log(`✅ 已生成 ${Object.keys(schemas).length} 个类型定义到 ${OUTPUT_PATH}`);
}

main().catch((error) => {
  console.error('❌ 生成失败：', error instanceof Error ? error.message : error);
  process.exit(1);
});

function mapType(type, schema) {
  const items = schema.items;
  const ref = schema.$ref;
  const anyOf = schema.anyOf;
  const enumValues = schema.enum;

  if (ref) {
    const name = String(ref).split('/').pop() || 'unknown';
    return name;
  }
  if (Array.isArray(anyOf)) {
    return anyOf.map((s) => mapType('', s)).join(' | ');
  }
  if (Array.isArray(enumValues)) {
    return enumValues.map((v) => `"${v}"`).join(' | ');
  }
  if (type === 'array' && items) {
    return `${mapType(items.type || '', items)}[]`;
  }
  if (type === 'object') {
    return 'Record<string, unknown>';
  }
  const typeMap = {
    string: 'string',
    integer: 'number',
    number: 'number',
    boolean: 'boolean',
    null: 'null',
  };
  return typeMap[type] || 'unknown';
}

main();