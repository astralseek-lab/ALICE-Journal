# -*- coding: utf-8 -*-
import os, re, io, base64, sys
from PIL import Image

# 用法：python build_html.py <篇目录> [--logo ...] [--out ...]
# 篇目录内需有 article.txt 与 Figure_N.png；输出默认写回同一目录。
import argparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))  # <root>/00_规范/脚本 -> <root>

parser = argparse.ArgumentParser(description='期刊人面 HTML 生成（2026-11-02 去硬编码版）')
parser.add_argument('folder', nargs='?', default=None, help='篇目录（含 article.txt）')
parser.add_argument('--logo', default=None, help='logo 路径，默认 <root>/00_规范/素材/AstralSeek_Lab_logo.png')
parser.add_argument('--out', default=None, help='输出目录，默认同篇目录')
parser.add_argument('--max-width', type=int, default=750)
parser.add_argument('--quality', type=int, default=85)
args = parser.parse_args()

folder = os.path.abspath(args.folder) if args.folder else os.getcwd()
article_path = os.path.join(folder, 'article.txt')
logo_path = os.path.abspath(args.logo) if args.logo else os.path.join(PROJECT_ROOT, '00_规范', '素材', 'AstralSeek_Lab_logo.png')
out_folder = os.path.abspath(args.out) if args.out else folder

if not os.path.exists(article_path):
    sys.exit('错误：未找到 ' + article_path)
logo_missing = not os.path.exists(logo_path)
if logo_missing:
    print('警告：logo 不存在（2026-11-03 用户决定 --logo 跳过）：' + logo_path)

# Read article
with open(article_path, 'r', encoding='utf-8') as f:
    text = f.read().strip()

# Title is first line (## heading)
lines = text.split('\n')
title_line = lines[0].lstrip('#').strip()

# Extract file metadata from HTML comment like <!-- 文件信息：Nature Aging IF=25.0 Q1 -->
file_info = '《期刊名》 IF=暂无'
meta_match = re.search(r'<!--\s*文件信息[：:]\s*(.*?)\s*-->', text)
if meta_match:
    parts = meta_match.group(1).strip().split()
    # 注释约定（2026-11-02 起）：<!-- 文件信息：期刊名 IF=x.x -->
    # JCR 分区位已取消；注释里若仍有分区字样，忽略并提示。
    if_idx = next((i for i, p in enumerate(parts) if p.upper().startswith('IF=')), None)
    if if_idx is not None:
        journal = ' '.join(parts[:if_idx]).replace('_', ' ') or '预印本'
        if_j = parts[if_idx]
        extra = parts[if_idx + 1:]
        if extra:
            print('提示：文件信息中的「' + ' '.join(extra) + '」不再进入文件名（2026-11-02 取消 JCR 分区位）')
        if if_j.upper().startswith('IF=暂无'):
            file_info = 'IF=暂无，预印本'
        else:
            # 2026-11-03 用户裁定：标题已含期刊名时，文件名后缀不再重复期刊名
            if journal.replace(' ', '') in title_line.replace(' ', ''):
                file_info = if_j
            else:
                file_info = f'《{journal}》 {if_j}'
    else:
        file_info = meta_match.group(1).strip().replace('_', ' ')

# Separate core highlights
hl_match = re.search(r'\n## 核心亮点\s*\n', text)
if hl_match:
    pre_hl = text[:hl_match.start()]
    post_hl = text[hl_match.end():]
    # core section ends at next ## heading or 引用 section; since v0.9-article
    # change (2026-11-03) it also ends at the first non-bullet paragraph after
    # the bullet list, so a heading-less body cannot leak into the abstract.
    next_heading = re.search(r'\n## ', post_hl)
    next_ref = re.search(r'\n引用\s*\n', post_hl)
    end_pos = len(post_hl)
    if next_heading and next_ref:
        end_pos = min(next_heading.start(), next_ref.start())
    elif next_heading:
        end_pos = next_heading.start()
    elif next_ref:
        end_pos = next_ref.start()
    core_lines_full = post_hl[:end_pos].split('\n')
    seen_bullet = False
    cut_line = None
    for i, ln in enumerate(core_lines_full):
        s = ln.strip()
        if not s:
            continue
        if s.startswith('- ') or s.startswith('* '):
            seen_bullet = True
        elif seen_bullet:
            cut_line = i
            break
    if cut_line is not None:
        end_pos = sum(len(l) + 1 for l in core_lines_full[:cut_line])
    core_text = post_hl[:end_pos].strip()
    # Rebuild core text: convert markdown bullets to HTML
    core_lines = core_text.split('\n')
    core_html_lines = []
    in_ul = False
    for line in core_lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('- ') or line.startswith('* '):
            if not in_ul:
                core_html_lines.append('<ul>')
                in_ul = True
            item = line[2:].strip()
            # Convert **text** to <strong>text</strong>
            item = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', item)
            core_html_lines.append(f'<li>{item}</li>')
        else:
            if in_ul:
                core_html_lines.append('</ul>')
                in_ul = False
            # Convert **text** to <strong>text</strong>
            line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
            core_html_lines.append(f'<p>{line}</p>')
    if in_ul:
        core_html_lines.append('</ul>')
    core = '\n'.join(core_html_lines)
    # Body excludes core highlights section but includes pre-core title/metadata and post-core content
    post_core = post_hl[end_pos:].strip() if end_pos < len(post_hl) else ''
    ref_match_post = re.search(r'^引用\s*\n', post_core, re.MULTILINE)
    if ref_match_post:
        body_text = (pre_hl + '\n\n' + post_core[:ref_match_post.start()]).strip()
        ref_text_start = post_core[ref_match_post.end():].strip()
    else:
        body_text = pre_hl.strip()
        ref_text_start = post_core
else:
    print('警告：未找到「## 核心亮点」段落，核心亮点暂为空占位')
    core = '<p>待补充</p>'
    body_text = text
    ref_text_start = ''

# Separate references
ref_match = re.search(r'\n引用\s*\n', body_text)
if ref_match:
    body_text = body_text[:ref_match.start()].strip()
    ref_text = body_text[ref_match.end():].strip() if ref_match else ''
else:
    # Try from ref_text_start
    ref_match2 = re.search(r'^引用\s*\n', ref_text_start)
    if ref_match2:
        ref_text = ref_text_start[ref_match2.end():].strip()
    elif ref_text_start.strip():
        ref_text = ref_text_start.strip()
    else:
        ref_text = ''

# Remove HTML metadata comment from body so it doesn't render as text
body_text = re.sub(r'<!--\s*文件信息[：:]\s*.*?\s*-->', '', body_text).strip()

# Remove title from body (will be in filename, not HTML body)
body_text = re.sub(r'^## .*\n?', '', body_text).strip()

# Convert image to base64 JPEG
def img_to_base64(path, max_width=750, quality=85):
    img = Image.open(path)
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')
    if img.width > max_width:
        ratio = max_width / img.width
        new_size = (max_width, int(img.height * ratio))
        img = img.resize(new_size, Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=quality)
    return base64.b64encode(buf.getvalue()).decode('utf-8')

logo_b64 = None if logo_missing else img_to_base64(logo_path, max_width=750, quality=85)
logo_html = (f'<img src="data:image/jpeg;base64,{logo_b64}" alt="AstralSeek Lab logo" style="max-width:100%;"/>\n'
             if logo_b64 else '')

# Figure captions from ## 图注 section if present
fig_captions = {}
cap_match = re.search(r'\n## 图注\s*\n', text)
if cap_match:
    cap_section = text[cap_match.end():]
    next_sec = re.search(r'\n## ', cap_section)
    if next_sec:
        cap_section = cap_section[:next_sec.start()]
    for line in cap_section.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        m = re.match(r'(?:Fig\.?|Figure|图)\s*(\d+)\s*[|．.:：]\s*(.+)', line, re.I)
        if m:
            fig_captions[int(m.group(1))] = m.group(2).strip()

# Figure insertion: find first mention of Figure N and insert image after the paragraph
figure_files = sorted([f for f in os.listdir(folder) if re.match(r'Figure_\d+\.png', f)],
                      key=lambda x: int(re.search(r'\d+', x).group()))

fig_html_map = {}
for fig_file in figure_files:
    n = int(re.search(r'\d+', fig_file).group())
    b64 = img_to_base64(os.path.join(folder, fig_file), max_width=750, quality=85)
    caption = fig_captions.get(n, f'Figure {n}')
    full_caption = f'Figure {n} | {caption}'
    fig_html = f'''<p style="text-align:center;"><img src="data:image/jpeg;base64,{b64}" alt="{full_caption}" style="max-width:100%;"/></p>\n<p style="text-align:center; font-size:0.85em; color:#555;">{full_caption}</p>\n'''
    fig_html_map[n] = fig_html

# Insert figures after paragraph that first mentions them in the main text only,
# not inside the ## 图注 caption section. The caption section may appear before
# or after the main body, so we remove just that section and keep everything else.
caption_match = re.search(r'(?:^|\n)## 图注\s*\n', body_text)
if caption_match:
    # Start at the ## 图注 heading, not the optional leading newline
    caption_start = caption_match.start() + (1 if body_text[caption_match.start()] == '\n' else 0)
    caption_end = caption_match.end()
    # caption section ends at the next ## heading or at end of text
    next_heading = re.search(r'\n## ', body_text[caption_end:])
    if next_heading:
        caption_section = body_text[caption_start:caption_end + next_heading.start()]
        main_text = body_text[:caption_start] + '\n\n' + body_text[caption_end + next_heading.start():]
    else:
        caption_section = body_text[caption_start:]
        main_text = body_text[:caption_start]
else:
    main_text = body_text
    caption_section = ''


def convert_bullets(block):
    """正文 markdown bullet -> <ul><li>；**加粗** -> <strong>（反向引用必须有捕获组，否则产生字面量 \\1 乱码）"""
    ls = block.split('\n')
    out, in_ul = [], False
    for ln in ls:
        s = ln.strip()
        if s.startswith('- ') or s.startswith('* '):
            if not in_ul:
                out.append('<ul>')
                in_ul = True
            item = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s[2:].strip())
            out.append(f'<li>{item}</li>')
        else:
            if in_ul:
                out.append('</ul>')
                in_ul = False
            out.append(ln)
    if in_ul:
        out.append('</ul>')
    return '\n'.join(out)


paragraphs = re.split(r'\n\n+', convert_bullets(main_text))
inserted = set()
new_paragraphs = []
for p in paragraphs:
    new_paragraphs.append(p)
    # Match Fig/Figure/图 followed by optional . and number
    m = re.search(r'(?:[Ff]ig(?:ure)?\.?|图)\s*(\d+)', p)
    if m:
        n = int(m.group(1))
        if n in fig_html_map and n not in inserted:
            new_paragraphs.append(fig_html_map[n])
            inserted.add(n)

body_html = '\n\n'.join(new_paragraphs)

# Uncited figures go right after the 核心亮点 blockquote（2026-11-03 用户裁定「开门见山就是图」：
# 摘要后直出图，正文无需引用句；此前为追加到文末）。
uncited_figs = '\n\n'.join(fig_html_map[n] for n in sorted(fig_html_map.keys()) if n not in inserted)
if uncited_figs:
    body_html = uncited_figs + '\n\n' + body_html

# The ## 图注 section is used only to extract captions; do not append it again,
# because each figure already carries its caption directly underneath the image.

# Convert markdown ### and ## in body to h3/h2, but NO h1
body_html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', body_html, flags=re.MULTILINE)
body_html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', body_html, flags=re.MULTILINE)
body_html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', body_html)
# Wrap plain paragraphs in <p style="text-align:justify;">
def wrap_p(seg):
    txt = seg.strip()
    if not txt:
        return ''
    if txt.startswith(('<h', '<p', '<blockquote', '<img', '<ul', '<li', '</ul')):
        return seg
    return f'<p style="text-align:justify;">{txt}</p>'
body_html = '\n\n'.join([wrap_p(seg) for seg in body_html.split('\n\n') if seg.strip()])

# Build full HTML
html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title_line}</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; line-height: 1.8; color: #333; max-width: 750px; margin: 0 auto; padding: 20px; }}
h2 {{ font-size: 1.4em; margin-top: 1.6em; margin-bottom: 0.6em; color: #1a1a1a; }}
h3 {{ font-size: 1.15em; margin-top: 1.4em; margin-bottom: 0.5em; color: #222; }}
p {{ margin: 0.8em 0; }}
blockquote {{ border-left: 4px solid #333; padding-left: 16px; margin: 1em 0; color: #444; background: #f9f9f9; padding: 12px 16px; }}
blockquote p {{ margin: 0.4em 0; }}
ul {{ margin: 0.6em 0; padding-left: 1.5em; }}
li {{ margin: 0.3em 0; }}
img {{ display: block; margin: 0 auto; max-width: 100%; height: auto; }}
</style>
</head>
<body>
{logo_html}<blockquote>
{core}
</blockquote>
{body_html}
<blockquote>
<p><strong>引用：</strong>{ref_text}</p>
</blockquote>
</body>
</html>'''

# Output filename: Chinese title - Journal IF info
# 2026-11-03 增补：Windows 文件名非法字符 < > : " / \ | ? * 全角化（<>:"/\\|?* -> 全角），
# 仅影响文件名，不动标题正文；起因：锁定标题含直引号与竖线致 OSError 22。
_SAFE_MAP = {'<': '＜', '>': '＞', ':': '：', '"': '＂', '/': '／', '\\': '＼', '|': '｜', '?': '？', '*': '＊'}
def safe_name(s):
    s = ''.join(_SAFE_MAP.get(c, c) for c in s)
    return s.strip(' .')
out_name = safe_name(f'{title_line} - {file_info}') + '.html'
out_path = os.path.join(out_folder, out_name)
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f'HTML written: {out_path}')
print(f'Size: {os.path.getsize(out_path) / 1024 / 1024:.2f} MB')

# QC checks
import re as re_qc
errs = []
if '<h1' in html:
    errs.append('Found <h1>')
if re.search(r'\\1', html):
    errs.append('Found literal backslash-1 (bullet 转换反向引用失效)')

if '😀' in html or '🎉' in html:
    errs.append('Found emoji')
# Core highlights word count
m = re_qc.search(r'<blockquote>(.*?)</blockquote>', html, re_qc.DOTALL)
if m:
    qc_text = re_qc.sub(r'<img[^>]*>', '', m.group(1))
    qc_text = re_qc.sub(r'<[^>]+>', '', qc_text)
    cn_total = len(re_qc.findall(r'[\u4e00-\u9fff]', qc_text))
    lines = [l.strip() for l in qc_text.split('\n') if l.strip()]
    first_line = lines[0] if lines else ''
    cn_first = len(re_qc.findall(r'[\u4e00-\u9fff]', first_line))
    total_chars = len(qc_text.replace(' ', '').replace('\n', ''))
    print(f'一句话速读: {cn_first} 字 (<=80)')
    print(f'核心亮点总计: {cn_total} 字 (<=300)')
    print(f'总非空白字符: {total_chars} (<=600)')
    if cn_first > 80 or cn_total > 300 or total_chars > 600:
        errs.append('Core highlights length exceeded')
# Check cover not embedded
cover_pattern = re_qc.compile(r'<img[^>]*src="[^"]*cover\.png"', re_qc.IGNORECASE)
if cover_pattern.search(html):
    errs.append('Cover embedded in HTML')
if os.path.getsize(out_path) > 5 * 1024 * 1024:
    errs.append('HTML > 5MB')
if errs:
    print('QC ERRORS:', errs)
else:
    print('QC PASSED')
