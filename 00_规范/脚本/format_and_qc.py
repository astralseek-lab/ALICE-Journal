"""核心亮点格式化 + QC（2026-11-02 去硬编码版）：
1. 删除 <body> 核心亮点之前的 h1/h2/h3 标题与杂质图片。
2. 把核心亮点 blockquote 整理为：
   <p>速读句（无前缀标签）</p>
   <ul>
     <li><strong>数据/模型/方法/结果/结论：</strong>...</li>
   </ul>
3. 缺「数据」bullet 时报错，不再自动补写（脚本不代写事实）。
4. 校验：logo 为 body 首元素、核心亮点为 bulletpoint、速读 ≤80 字、亮点 ≤600 字。
   2026-11-03：亮点总字符上限 300→360（顶层 v5.9.1），同日再 360→450（顶层 v5.9.2，用户裁定摘要提至 450 字），
   再 450→600（顶层 v5.9.3，用户裁定：摘要升为全局内容——意义要点收归摘要，正文只留图表内容）。
用法：python format_and_qc.py <目录或 HTML 文件> [更多路径 ...]
"""
import re
import sys
import argparse
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString

REQUIRED_BULLET_LABELS = {'数据', '数据集', '数据规模'}


def clean_for_count(text):
    return re.sub(r'\s+', '', text)


def count_chinese(text):
    return len(re.findall(r'[\u4e00-\u9fff]', text))


def is_reference_blockquote(bq):
    text = bq.get_text('\n', strip=True)
    return ('http' in text or 'DOI' in text or 'doi' in text or
            'et al.' in text or '期刊：' in text)


def find_first_highlight_blockquote(body):
    for child in body.children:
        if child.name == 'blockquote':
            if not is_reference_blockquote(child):
                return child
    return None



def parse_highlight_html(bq):
    """从核心亮点 blockquote 中解析一句话速读与 bullet 列表。"""
    bullets = []

    # 1. 一句话速读：优先第一个非空 <p>
    one_sentence = ''
    for p_candidate in bq.find_all('p'):
        txt = p_candidate.get_text(strip=True)
        if txt:
            one_sentence = txt
            break
    if not one_sentence:
        # 兜底：从文本第一行取
        first_line = bq.get_text('\n', strip=True).splitlines()[0]
        one_sentence = first_line
    if one_sentence.startswith('一句话速读：') or one_sentence.startswith('一句话速读:'):
        one_sentence = one_sentence.split('：', 1)[1] if '：' in one_sentence else one_sentence.split(':', 1)[1]

    # 2. bullet 列表：优先解析 <ul><li>
    ul = bq.find('ul')
    if ul:
        items = [li.get_text(' ', strip=True) for li in ul.find_all('li')]
        i = 0
        while i < len(items):
            text = items[i]
            # 当前项仅含 label（如“数据集：”），与下一项合并为内容
            if re.match(r'^[^：:]{1,10}[：:]$', text):
                label = text[:-1].strip()
                if i + 1 < len(items):
                    content = items[i + 1]
                    i += 2
                else:
                    content = ''
                    i += 1
                bullets.append((label, content))
                continue
            # 普通 label：content
            m = re.match(r'^(.{1,10}?)[：:]\s*(.+)$', text)
            if m:
                bullets.append((m.group(1).strip(), m.group(2)))
            else:
                bullets.append(('', text))
            i += 1
    else:
        # 纯文本 fallback
        lines = [l.strip() for l in bq.get_text('\n', strip=True).splitlines() if l.strip()]
        for line in lines[1:]:
            if line.startswith('- ') or line.startswith('– ') or line.startswith('• '):
                line = line[2:]
            m = re.match(r'^(.{1,10}?)[：:]\s*(.+)$', line)
            if m:
                bullets.append((m.group(1).strip(), m.group(2)))
            else:
                bullets.append(('', line))
    return one_sentence, bullets


def rebuild_highlight(soup, bq, one_sentence, bullets):
    bq.clear()
    p = soup.new_tag('p')
    p.string = one_sentence  # 2026-11-02：速读句不带前缀标签
    bq.append(p)
    if bullets:
        ul = soup.new_tag('ul')
        for label, content in bullets:
            li = soup.new_tag('li')
            if label:
                strong = soup.new_tag('strong')
                strong.string = f'{label}：'
                li.append(strong)
                li.append(content)
            else:
                li.string = content
            ul.append(li)
        bq.append(ul)


def find_logo_banner(body):
    """在 body 中查找 AstralSeek Lab logo banner（无论当前在 blockquote 内还是外）。"""
    for img in body.find_all('img'):
        if img.get('alt') == 'AstralSeek Lab logo':
            return img
    return None


def ensure_logo_before_highlight(body, highlight, logo_img):
    """确保 logo banner 位于核心亮点 blockquote 之前，且为 body 首元素。"""
    if logo_img is None:
        return

    # 统一样式
    logo_img['style'] = 'max-width:100%; height:auto; display:block; margin:0;'

    # 若 logo 当前在 blockquote 内，先移出
    if highlight and logo_img.find_parent('blockquote') is highlight:
        logo_img.extract()

    # 插入到 body 最开头（或确保在 highlight 之前）
    if highlight:
        highlight.insert_before(logo_img)
    else:
        body.insert(0, logo_img)


def clean_after_highlight(body, highlight):
    """删除核心亮点之后、正文之前的 IF/论文元信息段落/blockquote。"""
    nxt = highlight.next_sibling
    while nxt and not nxt.name:
        nxt = nxt.next_sibling
    if nxt is None:
        return None
    if nxt.name == 'p':
        txt = nxt.get_text(strip=True)
        # 只删除期刊/IF 信息行，不删除正文段落
        if txt.startswith('《') or 'IF' in txt or '预印本' in txt or txt.startswith('期刊：') or txt.startswith('论文：'):
            nxt.decompose()
            return 'p-meta'
    if nxt.name == 'blockquote':
        txt = nxt.get_text(strip=True)
        if txt.startswith('论文：') or '期刊：' in txt or 'DOI' in txt or 'et al.' in txt:
            nxt.decompose()
            return 'blockquote-meta'
    return None


def remove_elements_before_logo(body, logo_img):
    """删除 logo banner 之前的标题/图片等杂质，保留 logo 本身。"""
    removed = []
    if logo_img is None:
        return removed
    for child in list(body.children):
        if child is logo_img:
            break
        if not child.name:
            continue
        if child.name in ('h1', 'h2', 'h3', 'h4', 'figure', 'img'):
            child.decompose()
            removed.append(child.name)
        elif child.name == 'p':
            txt = child.get_text(strip=True)
            # 删除位于 logo 之前的文章标题段落（非 IF 信息）
            if len(txt) > 10 and 'IF' not in txt and not txt.startswith('《'):
                child.decompose()
                removed.append('p-title')
    return removed


def process_html(path):
    raw = path.read_text(encoding='utf-8', errors='ignore')
    soup = BeautifulSoup(raw, 'html.parser')
    body = soup.find('body')
    if not body:
        return {'path': str(path), 'ok': False, 'issues': ['未找到 body']}

    issues = []

    # 1. 找到核心亮点 blockquote
    hl = find_first_highlight_blockquote(body)
    if not hl:
        issues.append('未找到核心亮点 blockquote')
        return {'path': str(path), 'ok': False, 'issues': issues}

    # 2. 找到 logo banner（可能位于 blockquote 内外）
    logo_img = find_logo_banner(body)

    # 3. 解析并重建核心亮点（不含 logo）
    one_sentence, bullets = parse_highlight_html(hl)
    if not one_sentence:
        issues.append('核心亮点中未提取到一句话速读')
        return {'path': str(path), 'ok': False, 'issues': issues}

    # 去重（不再自动补写任何 bullet）
    seen = set()
    deduped = []
    for b in bullets:
        key = (b[0], b[1])
        if key not in seen:
            seen.add(key)
            deduped.append(b)
    bullets = deduped

    labels = {b[0] for b in bullets}
    if not (labels & REQUIRED_BULLET_LABELS):
        issues.append('核心亮点缺少「数据」类 bullet（不再自动补写，请作者补）')

    rebuild_highlight(soup, hl, one_sentence, bullets)

    # 4. 将 logo banner 放到 blockquote 之前，并清理 logo 之前的杂质
    ensure_logo_before_highlight(body, hl, logo_img)
    removed = remove_elements_before_logo(body, logo_img)

    # 清理核心亮点后的 IF/论文元信息
    cleaned = clean_after_highlight(body, hl)
    if cleaned:
        removed.append(cleaned)

    # 4. 校验
    hl_text = hl.get_text('\n', strip=True)
    total_chars = len(clean_for_count(hl_text))
    cn_chars = count_chinese(hl_text)

    one_sentence_cn = count_chinese(one_sentence)
    if one_sentence_cn > 80:
        issues.append(f'一句话速读中文字数 {one_sentence_cn}，超过 80')
    if total_chars > 600:
        issues.append(f'核心亮点总字符（文字+符号）{total_chars}，超过 600')

    # 板块覆盖
    lower = hl_text.lower()
    section_keywords = {
        '数据集': ['数据', '数据集', '样本', '细胞', '语料'],
        '模型架构/创新': ['模型', '架构', '方法', '框架', 'Transformer', '扩散', 'attention', '图神经网络', '预训练'],
        '结果': ['结果', '性能', '指标', '优于', '领先', '准确', 'AUC', 'p值'],
        '结论': ['结论', '总结', '表明', '揭示', '提供', '路径', '框架'],
    }
    missing = [s for s, kws in section_keywords.items() if not any(k in lower for k in kws)]
    if missing:
        issues.append('核心亮点缺少板块：' + '、'.join(missing))

    # body 开头元素检查
    front = []
    for child in body.children:
        if child.name:
            front.append((child.name, child.get_text(' ', strip=True)[:60]))
        if len(front) >= 3:
            break
    if front[0][0] != 'img':
        issues.append(f'body 首元素为 <{front[0][0]}>，非 logo banner <img>')
    if len(front) < 2 or front[1][0] != 'blockquote':
        issues.append('logo banner 之后未紧跟核心亮点 <blockquote>')

    # 保存
    path.write_text(str(soup), encoding='utf-8')

    return {
        'path': str(path),
        'ok': len(issues) == 0,
        'issues': issues,
        'removed': removed,
        'front': front,
        'one_sentence': one_sentence,
        'one_sentence_cn': count_chinese(one_sentence),
        'bullets': bullets,
        'total_chars': total_chars,
        'cn_chars': cn_chars,
    }


def format_result(r):
    lines = []
    lines.append('=' * 70)
    lines.append(f"文件：{r['path']}")
    lines.append(f"body 前部元素：{r['front']}")
    lines.append(f"删除前置元素：{r.get('removed', [])}")
    lines.append(f"一句话速读：{r['one_sentence_cn']} 中文字 | 全文：{r['one_sentence'][:80]}")
    lines.append(f"核心亮点 bullet 数：{len(r['bullets'])} | 总字符（文字+符号）：{r['total_chars']} | 中文字：{r['cn_chars']}")
    for label, content in r['bullets']:
        lines.append(f"  - {label}：{content[:60]}")
    if r['issues']:
        lines.append('问题：')
        for issue in r['issues']:
            lines.append(f'  - {issue}')
    else:
        lines.append('问题：无')
    lines.append('结论：' + ('通过' if r['ok'] else '未通过'))
    return '\n'.join(lines)


def gather(paths):
    files = []
    for p in paths:
        pp = Path(p)
        if pp.is_file() and pp.suffix.lower() == '.html':
            files.append(pp)
        elif pp.is_file():
            print("跳过（非 HTML）：" + str(p))
        elif pp.is_dir():
            files.extend(sorted(x for x in pp.rglob('*.html') if not x.name.endswith('.bak')))
        else:
            print("跳过（不存在）：" + str(p))
    return sorted(set(files))


def main():
    ap = argparse.ArgumentParser(description='核心亮点格式化 + QC（2026-11-02 版）')
    ap.add_argument('paths', nargs='*', default=['.'], help='目录或 HTML 文件，可多个')
    ap.add_argument('--report', default=None, help='报告输出路径，默认写到第一个目录下的 QC记录_format.txt')
    args = ap.parse_args()

    paths = args.paths or ['.']
    html_files = gather(paths)
    if not html_files:
        sys.exit('未找到 HTML 文件')

    results = []
    for path in html_files:
        print('处理：' + path.name[:60])
        results.append(process_html(path))

    report = chr(10).join(x for x in (format_result(r) for r in results))
    if args.report:
        report_path = Path(args.report)
    else:
        base = Path(paths[0]) if Path(paths[0]).is_dir() else Path(paths[0]).parent
        report_path = base / 'QC记录_format.txt'
    report_path.write_text(report, encoding='utf-8')

    passed = sum(1 for r in results if r['ok'])
    print()
    print(f'共 {len(results)} 篇，通过 {passed} 篇')
    print(f'报告：{report_path}')
    return 0 if passed == len(results) else 1


if __name__ == '__main__':
    sys.exit(main())