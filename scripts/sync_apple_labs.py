#!/usr/bin/env python3
"""同步 Apple 实验到离线手册（仅 Python 标准库）。--check 检查是否已同步。
Markdown 渲染只覆盖 APPLE_CONTAINER_GUIDE.md 使用的标题、段落、表格和围栏代码。
"""
import argparse
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
START = '<!-- APPLE-CONTAINER-APPENDIX:START -->'
END = '<!-- APPLE-CONTAINER-APPENDIX:END -->'


def inline(text):
    tokens = []
    def code(match):
        tokens.append('<code>' + html.escape(match[1]) + '</code>')
        return f'\x00{len(tokens)-1}\x00'
    text = re.sub(r'`([^`]+)`', code, text)
    text = html.escape(text)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)',
                  lambda m: '<a href="' + html.escape(html.unescape(m[2]), quote=True) + '">' + m[1] + '</a>', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    return re.sub(r'\x00(\d+)\x00', lambda m: tokens[int(m[1])], text)


def pre(code, lang='bash'):
    return '<pre class="apple-command"><code class="lang-' + lang + '">' + html.escape(code) + '</code></pre>'


def markdown(source):
    lines = source.splitlines()
    output = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.startswith('# '):
            i += 1
            continue
        if line.startswith('```'):
            lang = line[3:].strip() or 'text'
            i += 1
            code = []
            while i < len(lines) and not lines[i].startswith('```'):
                code.append(lines[i]); i += 1
            if i == len(lines):
                raise ValueError('Unclosed Markdown code fence')
            output.append(pre('\n'.join(code), lang)); i += 1
            continue
        heading = re.match(r'(#{2,3}) (.+)', line)
        if heading:
            level = len(heading[1]) + 1
            anchor = re.match(r'(E\d{2}(?:\.\d+)?)', heading[2])
            attr = ' id="apple-' + anchor[1].lower().replace('.', '-') + '"' if anchor else ''
            output.append(f'<h{level}{attr}>' + inline(heading[2]) + f'</h{level}>')
            i += 1
            continue
        if line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                rows.append([x.strip() for x in lines[i].strip().strip('|').split('|')]); i += 1
            if len(rows) < 2 or not all(re.fullmatch(r':?-+:?', x) for x in rows[1]):
                raise ValueError('Invalid Markdown table')
            output.append('<div class="tw"><table><thead><tr>' + ''.join('<th>'+inline(x)+'</th>' for x in rows[0]) + '</tr></thead><tbody>')
            for row in rows[2:]:
                output.append('<tr>' + ''.join('<td>'+inline(x)+'</td>' for x in row) + '</tr>')
            output.append('</tbody></table></div>')
            continue
        paragraph = [line]
        i += 1
        while i < len(lines) and lines[i].strip() and not lines[i].startswith(('##', '```', '|')):
            paragraph.append(lines[i]); i += 1
        output.append('<p>' + inline(' '.join(paragraph)) + '</p>')
    return '\n\n'.join(output)


def chapter_block(lab):
    ch = lab['chapter']
    section = lab['section'].lower()
    parts = [f'<!-- APPLE-CONTAINER-CHAPTER:{ch}:START -->',
             f'<details class="box note apple-lab" id="apple-ch{ch}">',
             '<summary><span class="lab-title">Apple container 实验<span class="lab-level">' + html.escape(lab['level']) + '</span></span>',
             '<span class="lab-preview">' + html.escape(lab['goal']) + '</span><span class="lab-toggle" aria-hidden="true"></span></summary>',
             '<div class="lab-body"><dl class="lab-meta"><div><dt>准备环境</dt><dd>' + html.escape(lab['prerequisite']) + ' <a href="#apple-' + section + '">查看 ' + lab['section'] + ' 完整步骤</a>。</dd></div></dl>',
             pre(lab['commands']),
             '<dl class="lab-meta"><div><dt>观察结果</dt><dd>' + html.escape(lab['expected']) + '</dd></div>',
             '<div class="lab-boundary"><dt>适用范围</dt><dd>' + html.escape(lab['boundary']) + '</dd></div></dl>',
             '<p class="lab-footer"><a href="#apple-e09">各章环境要求</a><a href="#apple-e10">清理与恢复</a></p></div>',
             '</details>', f'<!-- APPLE-CONTAINER-CHAPTER:{ch}:END -->']
    return '\n'.join(parts)


def generate(source, labs, guide):
    source = re.sub(r'<!-- APPLE-CONTAINER-CHAPTER:\d+:START -->[\s\S]*?<!-- APPLE-CONTAINER-CHAPTER:\d+:END -->\s*', '', source)
    for lab in labs:
        pattern = r'(<h2 id="ch' + str(lab['chapter']) + r'">[\s\S]*?</h2>\s*<p class="lead">[\s\S]*?</p>\s*)'
        source, count = re.subn(pattern, lambda m: m[1] + chapter_block(lab) + '\n\n', source, count=1)
        if count != 1:
            raise ValueError(f"Missing chapter/lead: {lab['chapter']}")
    matrix = ['<h3 id="apple-chapter-map">E09.1 · 43 章实验索引</h3>',
              '<div class="tw"><table><thead><tr><th>章节</th><th>环境</th><th>任务</th><th>路线</th></tr></thead><tbody>']
    for lab in labs:
        matrix.append(f'<tr><td><a href="#apple-ch{lab["chapter"]}">第 {lab["chapter"]} 章</a></td><td>' + html.escape(lab['level']) + '</td><td>' + html.escape(lab['goal']) + '</td><td><a href="#apple-' + lab['section'].lower() + '">' + lab['section'] + '</a></td></tr>')
    matrix.append('</tbody></table></div>')
    body = markdown(guide)
    body = body.replace('<h3 id="apple-e10">', '\n'.join(matrix) + '\n\n<h3 id="apple-e10">')
    steps = ['准备', '隔离', '构建', '生命周期', '网络', '存储', '配置与安全', '排障', '进入 Kubernetes', '各章前提', '清理']
    step_nav = '<nav class="lab-steps" aria-label="Apple 实验步骤">' + ''.join(
        f'<a href="#apple-e{i:02}"><span>E{i:02}</span>{title}</a>' for i, title in enumerate(steps)) + '</nav>'
    appendix = START + '\n<h2 id="appE"><span class="num">E</span>Apple container 全章节实验路线</h2>\n\n' + step_nav + '\n\n' + body + '\n' + END
    if START in source:
        source, count = re.subn(re.escape(START) + r'[\s\S]*?' + re.escape(END), lambda _: appendix, source)
        if count != 1:
            raise ValueError('Duplicate Apple appendix markers')
    else:
        source = source.replace('</main>', appendix + '\n\n</main>', 1)
    nav = '  <a href="#appE">E · Apple container 实验路线</a>'
    if nav not in source:
        source = source.replace('  <a href="#appD">D · 学习路径与自测题</a>', '  <a href="#appD">D · 学习路径与自测题</a>\n' + nav)
    return source


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    labs = json.loads((ROOT/'examples/apple-container/chapter-labs.json').read_text())
    if [x['chapter'] for x in labs] != list(range(1, 44)):
        raise ValueError('Chapter labs must cover exactly chapters 1–43')
    path = ROOT/'index.html'
    source = path.read_text()
    result = generate(source, labs, (ROOT/'APPLE_CONTAINER_GUIDE.md').read_text())
    if args.check and result != source:
        raise SystemExit('FAIL: Apple content is not synchronized; run scripts/sync_apple_labs.py')
    if not args.check:
        path.write_text(result)
    print('PASS: Apple 实验已同步，覆盖 43 章及完整离线附录 E。')

if __name__ == '__main__':
    main()
