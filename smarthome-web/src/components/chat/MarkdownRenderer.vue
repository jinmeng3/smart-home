<script setup lang="ts">
import { computed } from "vue";
import MarkdownIt from "markdown-it";

const md = new MarkdownIt({
    breaks: true,
    linkify: true,
    typographer: true,
});

// === 工具函数 ===

const escapeHtml = (s: string): string =>
    md.utils?.escapeHtml(s) ?? s;

const tokenStr = (tokens: import("markdown-it").Token[], idx: number, key: string): string => {
    const val = (tokens[idx] as Record<string, unknown> | undefined)?.[key];
    return val === undefined || val === null ? "" : String(val);
};

const tokenAttr = (tokens: import("markdown-it").Token[], idx: number, name: string): string => {
    const val = tokens[idx]?.attrGet(name);
    return val === undefined || val === null ? "" : String(val);
};

// === 自定义 renderer 规则 ===

md.renderer.rules.fence = (tokens, idx) => {
    const lang = tokenStr(tokens, idx, "info").trim();
    const code = escapeHtml(tokenStr(tokens, idx, "content"));
    const langAttr = lang ? ` data-language="${lang}"` : "";
    return `<pre class="md-pre"${langAttr}><code class="md-code">${code}</code><button class="md-copy-btn" onclick="(function(btn){var code=btn.parentElement.querySelector('code').textContent;navigator.clipboard.writeText(code);btn.textContent='\u2713';btn.classList.add('copied');setTimeout(function(){btn.textContent='\u2398';btn.classList.remove('copied')},1500)})(this)" title="\u590d\u5236\u4ee3\u7801">\u2398</button></pre>\n`;
};

md.renderer.rules.code_inline = (tokens, idx) => {
    const code = escapeHtml(tokenStr(tokens, idx, "content"));
    return `<code class="md-code-inline">${code}</code>`;
};

md.renderer.rules.heading_open = (tokens, idx) => {
    const level = tokenStr(tokens, idx, "tag");
    return `<${level} class="md-h md-h-${level}">`;
};

md.renderer.rules.paragraph_open = () => '<p class="md-p">\n';
md.renderer.rules.paragraph_close = () => "</p>\n";

md.renderer.rules.bullet_list_open = () => '<ul class="md-ul">\n';
md.renderer.rules.bullet_list_close = () => "</ul>\n";
md.renderer.rules.ordered_list_open = () => '<ol class="md-ol">\n';
md.renderer.rules.ordered_list_close = () => "</ol>\n";
md.renderer.rules.list_item_open = () => '<li class="md-li">\n';
md.renderer.rules.list_item_close = () => "</li>\n";

md.renderer.rules.blockquote_open = () => '<blockquote class="md-blockquote">\n';
md.renderer.rules.blockquote_close = () => "</blockquote>\n";

md.renderer.rules.link_open = (tokens, idx) => {
    const href = escapeHtml(tokenAttr(tokens, idx, "href"));
    return `<a class="md-link" href="${href}" target="_blank" rel="noopener noreferrer">`;
};
md.renderer.rules.link_close = () => "</a>";

md.renderer.rules.hr = () => '<hr class="md-hr">\n';

md.renderer.rules.table_open = () => '<div class="md-table-wrap"><table class="md-table">\n';
md.renderer.rules.table_close = () => "</table></div>\n";
md.renderer.rules.thead_open = () => '<thead class="md-thead">\n';
md.renderer.rules.thead_close = () => "</thead>\n";
md.renderer.rules.tbody_open = () => '<tbody class="md-tbody">\n';
md.renderer.rules.tbody_close = () => "</tbody>\n";
md.renderer.rules.tr_open = () => '<tr class="md-tr">\n';
md.renderer.rules.tr_close = () => "</tr>\n";
md.renderer.rules.th_open = () => '<th class="md-th">\n';
md.renderer.rules.th_close = () => "</th>\n";
md.renderer.rules.td_open = () => '<td class="md-td">\n';
md.renderer.rules.td_close = () => "</td>\n";

md.renderer.rules.image = (tokens, idx) => {
    const src = escapeHtml(tokenAttr(tokens, idx, "src"));
    const alt = escapeHtml(tokenStr(tokens, idx, "content"));
    return `<img class="md-img" src="${src}" alt="${alt}" loading="lazy">`;
};

md.renderer.rules.strong_open = () => '<strong class="md-strong">';
md.renderer.rules.strong_close = () => "</strong>";

md.renderer.rules.em_open = () => '<em class="md-em">';
md.renderer.rules.em_close = () => "</em>";

const props = defineProps<{
    content: string;
    streaming?: boolean;
}>();

const html = computed(() => {
    if (!props.content) return "";

    if (props.streaming) {
        const escaped = escapeHtml(props.content);
        return escaped.replace(/\n/g, "<br>");
    }

    try {
        return md.render(props.content);
    } catch {
        return `<p>${props.content}</p>`;
    }
});
</script>

<template>
    <div class="markdown-body" v-html="html"></div>
</template>

<style>
.markdown-body {
    line-height: 1.7;
    word-break: break-word;
}
.markdown-body > :first-child { margin-top: 0; }
.markdown-body > :last-child { margin-bottom: 0; }

/* 标题 */
.markdown-body .md-h {
    margin: 1.1em 0 0.5em;
    font-weight: 700;
    color: var(--color-text-primary, #1e293b);
    line-height: 1.3;
}
.markdown-body .md-h-1 { font-size: 1.35em; }
.markdown-body .md-h-2 { font-size: 1.2em; }
.markdown-body .md-h-3 { font-size: 1.1em; }
.markdown-body .md-h-4 { font-size: 1em; }

/* 段落 */
.markdown-body .md-p {
    margin: 0.5em 0;
    color: var(--color-text-secondary, #475569);
}

/* 列表 */
.markdown-body .md-ul,
.markdown-body .md-ol {
    margin: 0.5em 0;
    padding-left: 1.5em;
}
.markdown-body .md-li {
    margin: 0.25em 0;
}

/* 行内代码 */
.markdown-body .md-code-inline {
    padding: 0.15em 0.4em;
    border-radius: 4px;
    background: var(--color-surface-subtle, #f1f5f9);
    color: var(--color-danger, #e11d48);
    font-size: 0.88em;
    font-family: var(--font-mono);
}

/* 代码块 */
.markdown-body .md-pre {
    position: relative;
    margin: 0.7em 0;
    border-radius: 10px;
    background: #0f172a !important;
    padding: 18px 16px 14px;
    overflow-x: auto;
    line-height: 1.5;
}
.markdown-body .md-code {
    padding: 0;
    border-radius: 0;
    background: transparent;
    color: #e2e8f0;
    font-size: 0.82em;
    tab-size: 2;
    font-family: var(--font-mono);
}
.markdown-body .md-pre[data-language]::before {
    content: attr(data-language);
    position: sticky;
    display: inline-block;
    top: 0;
    left: 0;
    margin-bottom: 8px;
    font-size: 10px;
    color: #64748b;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* 代码块复制按钮 */
.markdown-body .md-copy-btn {
    position: absolute;
    top: 6px;
    right: 8px;
    display: grid;
    width: 26px;
    height: 26px;
    place-items: center;
    border: none;
    border-radius: 6px;
    background: rgba(255,255,255,0.06);
    color: #94a3b8;
    font-size: 14px;
    cursor: pointer;
    opacity: 0;
    transition: opacity 180ms ease, background 180ms ease, color 180ms ease;
    line-height: 1;
}

.markdown-body .md-pre:hover .md-copy-btn {
    opacity: 1;
}

.markdown-body .md-copy-btn:hover {
    background: rgba(255,255,255,0.14);
    color: #e2e8f0;
}

.markdown-body .md-copy-btn.copied {
    opacity: 1;
    color: #4ade80;
    background: rgba(74,222,128,0.12);
}

/* 引用 */
.markdown-body .md-blockquote {
    margin: 0.7em 0;
    border-left: 3px solid var(--color-primary-300, #93c5fd);
    padding: 0.5em 1em;
    background: var(--color-surface-subtle, #f8fafc);
    border-radius: 0 8px 8px 0;
    color: var(--color-text-tertiary, #64748b);
}
.markdown-body .md-blockquote p {
    margin: 0.3em 0;
}

/* 链接 */
.markdown-body .md-link {
    color: var(--color-primary-600, #2563eb);
    text-decoration: underline;
    text-underline-offset: 2px;
    transition: color 150ms ease;
}
.markdown-body .md-link:hover {
    color: var(--color-primary-700, #1d4ed8);
}

/* 分割线 */
.markdown-body .md-hr {
    margin: 1em 0;
    border: 0;
    border-top: 1px solid var(--color-border, #e2e8f0);
}

/* 表格 */
.markdown-body .md-table-wrap {
    overflow-x: auto;
    margin: 0.7em 0;
    border-radius: 8px;
    border: 1px solid var(--color-border, #e2e8f0);
}
.markdown-body .md-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9em;
}
.markdown-body .md-th,
.markdown-body .md-td {
    border: 1px solid var(--color-border, #e2e8f0);
    padding: 10px 12px;
    text-align: left;
}
.markdown-body .md-th {
    background: var(--color-surface-subtle, #f8fafc);
    font-weight: 700;
    color: var(--color-text-primary, #1e293b);
    font-size: 0.85em;
    text-transform: uppercase;
    letter-spacing: 0.3px;
}
.markdown-body .md-tr:nth-child(even) {
    background: var(--color-surface-subtle, #fafbfc);
}

/* 图片 */
.markdown-body .md-img {
    max-width: 100%;
    border-radius: 8px;
    margin: 0.5em 0;
}

/* 粗体/斜体 */
.markdown-body .md-strong { font-weight: 700; }
.markdown-body .md-em { font-style: italic; }
</style>