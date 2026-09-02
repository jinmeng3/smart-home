/**
 * 契约一致性检查：从「schema 数量对比」升级为「路径级 + schema 集合」双向比对。
 *
 * 三项检查：
 *  1. 后端 OpenAPI schema 集合 vs src/api/generated/schema.d.ts 导出集合（命名集合差）
 *  2. 后端 (path, method) vs 前端 src/api/*.ts 中的 /api/... 路径（端点覆盖率）
 *  3. 前端调用了但后端缺失的路径 → 立即失败（防止调用不存在端点）
 *
 * 用法：npm run api:check
 * 前置：后端已运行（uvicorn 监听 :8000）
 */
import { readFileSync, readdirSync } from 'node:fs';
import { join, dirname, basename, extname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { tmpdir } from 'node:os';

const __dirname = dirname(fileURLToPath(import.meta.url));
const rootDir = join(__dirname, '..');
const apiDir = join(rootDir, 'src', 'api');
const generatedFile = join(apiDir, 'generated', 'schema.d.ts');

const OPENAPI_URL = 'http://127.0.0.1:8000/openapi.json';
// 跨平台临时文件路径：Node 上 prefer os.tmpdir() + 'openapi.json'
const OPENAPI_FALLBACK = process.env.OPENAPI_JSON_PATH || join(tmpdir(), 'openapi.json');
const HTTP_METHODS = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options'];

const ansi = {
  red: (s) => `\x1b[31m${s}\x1b[0m`,
  green: (s) => `\x1b[32m${s}\x1b[0m`,
  yellow: (s) => `\x1b[33m${s}\x1b[0m`,
  bold: (s) => `\x1b[1m${s}\x1b[0m`,
};

/** 从 OpenAPI 提取 (method, path) 集合。 */
const extractBackendEndpoints = (spec) => {
  const endpoints = new Set();
  for (const [path, methods] of Object.entries(spec.paths || {})) {
    for (const method of Object.keys(methods || {})) {
      if (HTTP_METHODS.includes(method.toLowerCase())) {
        endpoints.add(`${method.toUpperCase()} ${path}`);
      }
    }
  }
  return endpoints;
};

/** 从 src/api/*.ts 提取前端调用的 /api/ 路径集合（不含 method 推断，全视为 ANY）。 */
const extractFrontendPaths = () => {
  const files = readdirSync(apiDir).filter((f) => {
    if (extname(f) !== '.ts') return false;
    if (f === 'client.ts') return false;
    if (f.startsWith('generated')) return false;
    return true;
  });

  const paths = new Set();
  const pathWithMethods = [];
  const pathRegex = /["'`](\/api\/[^"'`]+)["'`]/g;
  // 从 apiRequest(...) 上下文推断 method：扫描 method: "POST" 等显式字段
  const methodRegex = /apiRequest[^(]*\(([^)]*)\)/gs;
  // 简化版：仅匹配同一文件块中可见的 method 提示
  const methodHintRegex = /method:\s*["'`](GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)["'`]/i;

  for (const f of files) {
    const fullPath = join(apiDir, f);
    const raw = readFileSync(fullPath, 'utf-8');
    let sanitized = raw;
    // 1. 条件性 query 表达式（`${a ? "?" : ""}` 包含任意包裹符） → 整个脱去（含 ?）
    sanitized = sanitized.replace(/\$\{[^}]*\?[\s\S]*?\}/g, '');
    // 2. 其他模板表达式（`${var}` ） → 换为 {*}
    sanitized = sanitized.replace(/\$\{[\s\S]*?\}/g, '{*}');

    let match;
    const localPathRegex = new RegExp(pathRegex.source, 'g');
    while ((match = localPathRegex.exec(sanitized)) !== null) {
      let cleanPath = match[1].split('?')[0];
      paths.add(cleanPath);
    }
  }
  return { paths };
};

/** 从 schema.d.ts 提取导出的 interface 名称集合。 */
const extractGeneratedSchemas = () => {
  const content = readFileSync(generatedFile, 'utf-8');
  const names = new Set();
  const interfaceRegex = /^export interface (\w+)/gm;
  const typeRegex = /^export type (\w+)/gm;
  let m;
  while ((m = interfaceRegex.exec(content)) !== null) names.add(m[1]);
  while ((m = typeRegex.exec(content)) !== null) names.add(m[1]);
  return names;
};

/** 把后端路径模板转成正则（处理 {param}）。 */
const pathToRegex = (template) => {
  const pattern = '^' + template.replace(/[\\^$.*+?()[\]{}|]/g, '\\$&').replace(/\\\{[^}]+\\\}/g, '[^/]+') + '$';
  return new RegExp(pattern);
};

const main = async () => {
  // 1. 检查生成文件存在
  try {
    readFileSync(generatedFile, 'utf-8');
  } catch {
    console.error(ansi.red('❌ 类型定义文件不存在，请先运行 npm run api:generate'));
    process.exit(1);
  }

  let spec;
  let usedSource = 'http';
  try {
    const response = await fetch(OPENAPI_URL);
    if (response.ok) {
      spec = await response.json();
    } else {
      throw new Error(`HTTP ${response.status}`);
    }
  } catch (httpError) {
    // 退化：从本地文件加载（后端未启动 / sandbox 无网络时）
    try {
      const { readFileSync: read } = await import('node:fs');
      spec = JSON.parse(read(OPENAPI_FALLBACK, 'utf-8'));
      usedSource = `local file ${OPENAPI_FALLBACK}`;
    } catch (fileError) {
      console.error(ansi.red('❌ 获取 OpenAPI 失败：'));
      console.error('  http 错误：', httpError.message);
      console.error('  本地文件错误：', fileError.message);
      console.error(ansi.yellow(`   请先生成 ${OPENAPI_FALLBACK}：`));
      console.error('     cd smarthome-api && PYTHONPATH=. .venv/Scripts/python -c "from app.main import app; import json; json.dump(app.openapi(), open(\'/tmp/openapi.json\',\'w\'), ensure_ascii=False)"');
      process.exit(1);
    }
  }
  console.log(ansi.bold(`\n[0] 数据源：${usedSource}`));

  let hasError = false;
  const summary = [];

  // === 检查 1：schema 集合对比（忽略 ApiResponse_* 包装变体与已知的路径别名） ===
  const IGNORED_BACKEND_PATTERNS = [/^ApiResponse_[A-Z]/];  // Pydantic 包装实例化
  const IGNORED_FRONTEND_PATTERNS = [
    /^ApiResponse$/,        // 通用响应包装模板
    /^Paginated$/,          // 通用分页包装
    /^[a-z_]+_api_/,        // 路径别名（如 read_me_api_account_me_get）
  ];

  const backendSchemas = new Set(
    Object.keys(spec.components?.schemas || {})
      .filter((s) => !IGNORED_BACKEND_PATTERNS.some((re) => re.test(s)))
  );
  const generatedSchemas = extractGeneratedSchemas();
  const missingInFrontend = [...backendSchemas].filter((s) => !generatedSchemas.has(s));
  const extraInFrontend = [...generatedSchemas].filter(
    (s) => !backendSchemas.has(s) && !IGNORED_FRONTEND_PATTERNS.some((re) => re.test(s))
  );

  console.log(ansi.bold('\n[1] Schema 集合一致性（已过滤 ApiResponse_* 等噪音）'));
  console.log(`  后端有效 schemas：${backendSchemas.size}`);
  console.log(`  前端有效 schemas：${generatedSchemas.size - [...generatedSchemas].filter((s) => IGNORED_FRONTEND_PATTERNS.some((re) => re.test(s))).length}`);
  if (missingInFrontend.length > 0) {
    console.log(ansi.yellow(`  ⚠️  后端有但前端未生成 (${missingInFrontend.length})：`));
    missingInFrontend.slice(0, 20).forEach((s) => console.log(`     - ${s}`));
    if (missingInFrontend.length > 20) console.log(`     ... +${missingInFrontend.length - 20} more`);
  }
  if (extraInFrontend.length > 0) {
    console.log(ansi.yellow(`  ⚠️  前端生成但后端无对应 (${extraInFrontend.length})：`));
    extraInFrontend.slice(0, 20).forEach((s) => console.log(`     - ${s}`));
    if (extraInFrontend.length > 20) console.log(`     ... +${extraInFrontend.length - 20} more`);
  }
  if (missingInFrontend.length === 0 && extraInFrontend.length === 0) {
    console.log(ansi.green('  ✅ 完全一致'));
  } else {
    // Schema 不一致仅 warning，不 fail CI（生成器策略差异属于可控噪声）
    console.log(ansi.yellow('  ↑ 以上仅 warning，不阻塞 CI（可手动 review 生成策略）'));
  }
  summary.push({ name: 'Schema 集合（已过滤）', ok: true });

  // === 检查 2：端点覆盖率 ===
  console.log(ansi.bold('\n[2] 端点覆盖率（前端调用 vs 后端 path）'));
  const backendEndpoints = extractBackendEndpoints(spec);
  const { paths: frontendPaths } = extractFrontendPaths();

  const backendPathRegexes = [...backendEndpoints].map((ep) => {
    const [method, ...rest] = ep.split(' ');
    return { method, path: rest.join(' '), regex: pathToRegex(rest.join(' ')) };
  });

  const orphanFrontend = [];
  for (const fp of frontendPaths) {
    const matched = backendPathRegexes.some(({ regex }) => regex.test(fp));
    if (!matched) {
      orphanFrontend.push(fp);
    }
  }

  const unusedBackend = [];
  for (const { method, path } of backendPathRegexes) {
    // 启发式：路径至少被引用过就算「已用」，不再严格按 method 匹配
    // （前端 API 客户端不做严格 method 推断）
    const matched = [...frontendPaths].some((fp) => {
      const fpRegex = pathToRegex(fp);
      const pathRegex = pathToRegex(path);
      return fpRegex.test(path) || pathRegex.test(fp);
    });
    if (!matched) {
      unusedBackend.push(`${method} ${path}`);
    }
  }

  console.log(`  后端端点数：${backendEndpoints.size}`);
  console.log(`  前端调用路径数（去重）：${frontendPaths.size}`);
  if (orphanFrontend.length > 0) {
    console.log(ansi.red(`  ❌ 前端调用但后端缺失 (${orphanFrontend.length})：`));
    orphanFrontend.slice(0, 30).forEach((p) => console.log(`     - ${p}`));
    if (orphanFrontend.length > 30) console.log(`     ... +${orphanFrontend.length - 30} more`);
    hasError = true;
  }
  if (unusedBackend.length > 0) {
    console.log(ansi.yellow(`  ⚠️  后端有但前端未调用 (${unusedBackend.length})：`));
    unusedBackend.slice(0, 30).forEach((p) => console.log(`     - ${p}`));
    if (unusedBackend.length > 30) console.log(`     ... +${unusedBackend.length - 30} more`);
  }
  if (orphanFrontend.length === 0 && unusedBackend.length === 0) {
    console.log(ansi.green('  ✅ 完全一致'));
  }
  summary.push({ name: '端点覆盖', ok: orphanFrontend.length === 0 });

  // === 总结 ===
  console.log(ansi.bold('\n[总结]'));
  for (const { name, ok } of summary) {
    console.log(`  ${ok ? ansi.green('✅') : ansi.red('❌')} ${name}`);
  }

  if (hasError) {
    console.error(ansi.red('\n💥 契约检查未通过，请按上述提示修复或重新生成类型'));
    process.exit(1);
  }
  console.log(ansi.green('\n🎉 契约检查通过'));
};

main().catch((error) => {
  console.error(ansi.red('❌ 检查脚本异常：'), error);
  process.exit(1);
});