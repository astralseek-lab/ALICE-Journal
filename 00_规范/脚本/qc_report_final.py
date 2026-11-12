import re
import sys
import argparse
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString

ROOT = Path(".")  # 由 main() 按参数覆盖

SECTION_KEYWORDS = {
    "数据集": ["数据", "数据集", "数据规模", "队列", "样本", "单细胞", "scRNA", "RNA", "蛋白", "蛋白质", "测序", "表达谱", "语料", "训练数据"],
    "模型架构/创新": ["模型", "架构", "方法", "框架", "网络", "Transformer", "扩散", "diffusion", "注意力", "attention", "自监督", "预训练", "基础模型", "foundation model", "算法", "模块", "编码器", "图神经网络", "GNN"],
    "结果": ["结果", "性能", "表现", "指标", "AUC", "AUROC", "accuracy", "精确度", "F1", "p值", "p ", "显著", "提升", "优于", "对比", "baseline", "误差", "相关性", "SOTA", "准确率"],
    "结论": ["结论", "总结", "表明", "提示", "揭示", "证明", "展示", "发现", "意义", "展望", "贡献"],
}


def count_chinese(text):
    return len(re.findall(r'[\u4e00-\u9fff]', text))


def clean_text(text):
    return re.sub(r'\s+', '', text)


def has_emoji(text):
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U0001F900-\U0001F9FF"
        "\U0001FA00-\U0001FA6F"
        "\U00002600-\U000026FF"
        "\U00002700-\U000027BF"
        "]+", flags=re.UNICODE
    )
    return bool(emoji_pattern.search(text))


def is_reference_block(tag):
    text = tag.get_text('\n', strip=True)
    if 'http' in text or 'doi.org' in text.lower() or 'DOI' in text:
        return True
    if 'et al.' in text and len(text) > 80:
        return True
    return False


def collect_following_text(start_tag, stop_tags=('h2', 'h3', 'h4', 'hr')):
    """收集 start_tag 之后直到下一个 stop_tags 标签的所有文本"""
    contents = []
    sibling = start_tag.next_sibling
    while sibling:
        if sibling.name in stop_tags:
            break
        if sibling.name:
            if sibling.name in ('p', 'div', 'ul', 'ol', 'blockquote', 'span'):
                txt = sibling.get_text('\n', strip=True)
                if txt:
                    contents.append(txt)
        elif isinstance(sibling, NavigableString):
            txt = str(sibling).strip()
            if txt:
                contents.append(txt)
        sibling = sibling.next_sibling
    return '\n'.join(contents)


def find_tag_by_label(body, labels):
    """
    查找以 labels 中某个词作为标签/标题的元素。
    返回 [(tag, content_text), ...]
    """
    results = []
    # heading
    for heading in body.find_all(['h2', 'h3', 'h4']):
        text = heading.get_text(strip=True)
        if any(text.startswith(lb) for lb in labels):
            results.append((heading, collect_following_text(heading)))
    # p/div/blockquote 直接以"标签："开头
    for tag in body.find_all(['p', 'div', 'blockquote']):
        text = tag.get_text(strip=True)
        if any(text.startswith(lb + '：') or text.startswith(lb + ':') for lb in labels):
            content = collect_following_text(tag)
            if not content:
                # 内容在标签自身内，去掉前缀
                content = re.sub(r'^(' + '|'.join(re.escape(lb) for lb in labels) + r')[：:]\s*', '', text)
            results.append((tag, content))
    # p/div 中包含标签关键词（无冒号，如 <p>核心亮点</p>）
    for tag in body.find_all(['p', 'div']):
        text = tag.get_text(strip=True)
        if any(lb in text and len(text) < 20 for lb in labels):
            # 这是一个标签行，内容在后续兄弟节点
            results.append((tag, collect_following_text(tag)))
    return results


def extract_one_sentence(text):
    """从文本中提取一句话速读：只取第一段/第一句"""
    # 去掉前缀
    text = re.sub(r'^一句话速读[：:]\s*', '', text).strip()
    # 优先按换行取第一段
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if lines:
        first = lines[0]
        # 如果第一段太长，按句号取第一句
        if len(first) > 100:
            m = re.split(r'(?<=[。\.])', first)
            if m:
                return m[0]
        return first
    return text


def find_highlight_and_one_sentence(body):
    hl_tag = None
    hl_text = ""
    is_bq = False
    one_sentence = ""

    # 1. 找一句话速读（优先）
    os_results = find_tag_by_label(body, ['一句话速读'])
    if os_results:
        raw_os = os_results[0][1]
        one_sentence = extract_one_sentence(raw_os)

    # 2. 找核心亮点
    # 2a. 优先：blockquote 形式的核心亮点
    for bq in body.find_all('blockquote'):
        if is_reference_block(bq):
            continue
        text = bq.get_text('\n', strip=True)
        lower = text.lower()
        if '核心亮点' in text or '一句话速读' in text or \
           sum(1 for kws in SECTION_KEYWORDS.values() if any(k.lower() in lower for k in kws)) >= 2:
            hl_tag = bq
            hl_text = text
            is_bq = True
            if not one_sentence:
                # 2026-11-02：速读句不带前缀标签时，取 blockquote 内首个 <p>，并从亮点正文中剔除
                first_p = bq.find('p')
                parts = [l for l in text.split('\n') if l.strip()]
                if first_p is not None and first_p.get_text(strip=True):
                    one_sentence = extract_one_sentence(first_p.get_text(' ', strip=True))
                    if len(parts) > 1:
                        hl_text = '\n'.join(parts[1:])
                elif len(parts) > 1:
                    one_sentence = extract_one_sentence(parts[0])
                    hl_text = '\n'.join(parts[1:])
            break

    # 2b. heading 形式的核心亮点
    if hl_tag is None:
        hl_results = find_tag_by_label(body, ['核心亮点'])
        if hl_results:
            hl_tag, hl_text = hl_results[0]
            is_bq = hl_tag.name == 'blockquote'

    # 2c. 兜底：p/div 中包含"核心亮点"且不是标签
    if hl_tag is None:
        for tag in body.find_all(['p', 'div']):
            text = tag.get_text('\n', strip=True)
            if '核心亮点' in text and len(text) > 50:
                hl_tag = tag
                hl_text = text
                is_bq = False
                break

    # 2d. 兜底：如果一句话速读前面有长段落，当作核心亮点
    if hl_tag is None and os_results:
        tag = os_results[0][0]
        prev = tag.previous_sibling
        while prev and not prev.name:
            prev = prev.previous_sibling
        if prev and prev.name in ('p', 'div', 'blockquote'):
            prev_text = prev.get_text('\n', strip=True)
            if len(prev_text) > 50:
                hl_tag = prev
                hl_text = prev_text
                is_bq = prev.name == 'blockquote'

    # 从核心亮点中去掉一句话速读部分（避免重复）
    if hl_text and one_sentence:
        # 找到"一句话速读"的位置并截断
        idx = hl_text.find('一句话速读')
        if idx > 0:
            hl_text = hl_text[:idx].strip()

    return hl_tag, hl_text, one_sentence, is_bq


def get_body_front_elements(body, n=12):
    elements = []
    for child in body.children:
        if child.name:
            elements.append((child.name, child))
        elif str(child).strip():
            elements.append(('#text', str(child).strip()))
        if len(elements) >= n:
            break
    return elements


def check_file(html_path):
    result = {"path": str(html_path), "ok": True, "issues": []}
    raw = html_path.read_text(encoding='utf-8', errors='ignore')
    result["file_size_mb"] = len(raw.encode('utf-8')) / (1024 * 1024)

    soup = BeautifulSoup(raw, 'html.parser')
    body = soup.find('body')
    if not body:
        result["issues"].append("未找到 <body> 标签")
        result["ok"] = False
        return result

    front_elements = get_body_front_elements(body, 12)
    result["front_elements"] = []
    for t, e in front_elements:
        if hasattr(e, 'get_text'):
            txt = e.get_text(' ', strip=True)[:70]
        else:
            txt = str(e)[:70]
        result["front_elements"].append((t, txt))

    # 1. 检查封面是否在正文前
    cover_before_text = False
    text_seen = False
    for tag_name, elem in front_elements:
        if tag_name in ('#text', 'p', 'h2', 'h3', 'blockquote') and not text_seen:
            txt = (elem.get_text(' ', strip=True) if hasattr(elem, 'get_text') else str(elem)).strip()
            if len(txt) > 15 and not any(k in txt for k in ['封面', 'cover', '首页', 'Article in Press', '论文首页', '论文封面']):
                text_seen = True
        if tag_name in ('figure', 'img') and not text_seen:
            # logo banner 不是封面图，排除
            if tag_name == 'img' and elem.get('alt') == 'AstralSeek Lab logo':
                continue
            cover_before_text = True
            break
    result["cover_before_text"] = cover_before_text
    if cover_before_text:
        result["issues"].append("封面图位于正文文本之前，违反‘文本前不需要 cover 截图’的要求")
        result["ok"] = False

    # 2. h1
    h1s = soup.find_all('h1')
    result["h1_count"] = len(h1s)
    if h1s:
        result["issues"].append(f"存在 {len(h1s)} 个 <h1> 标签")
        result["ok"] = False

    # 3. 核心亮点与一句话速读
    highlight_tag, highlight_text, one_sentence, is_bq = find_highlight_and_one_sentence(body)
    result["highlight_found"] = highlight_tag is not None
    result["highlight_in_blockquote"] = is_bq
    result["highlight_text"] = highlight_text[:500]

    if highlight_tag is None:
        result["issues"].append("未找到核心亮点区块")
        result["ok"] = False
    else:
        if not is_bq:
            result["issues"].append("核心亮点未使用 <blockquote> 包裹")
            result["ok"] = False

        result["highlight_cn_chars"] = count_chinese(highlight_text)
        result["highlight_total_chars"] = len(clean_text(highlight_text))

        result["one_sentence"] = one_sentence
        result["one_sentence_cn"] = count_chinese(one_sentence)
        result["one_sentence_total"] = len(clean_text(one_sentence))

        if not one_sentence:
            result["issues"].append("未找到明确的一句话速读")
            result["ok"] = False
        else:
            if result["one_sentence_cn"] > 80:
                result["issues"].append(f"一句话速读 {result['one_sentence_cn']} 中文字，超过 80 字")
                result["ok"] = False
            if result["one_sentence_total"] > 120:
                result["issues"].append(f"一句话速读总字符 {result['one_sentence_total']}，可能过长")
                result["ok"] = False

        if result["highlight_cn_chars"] > 300:
            result["issues"].append(f"核心亮点中文字数 {result['highlight_cn_chars']}，超过 300 字")
            result["ok"] = False
        if result["highlight_total_chars"] > 450:
            result["issues"].append(f"核心亮点总非空白字符 {result['highlight_total_chars']}，超过 450")
            result["ok"] = False

        highlight_lower = highlight_text.lower()
        missing_sections = []
        for section, keywords in SECTION_KEYWORDS.items():
            if not any(kw.lower() in highlight_lower for kw in keywords):
                missing_sections.append(section)
        result["missing_sections"] = missing_sections
        if missing_sections:
            result["issues"].append(f"核心亮点缺少板块：{', '.join(missing_sections)}")
            result["ok"] = False

        # 3b. logo banner 检查（必须位于核心亮点 blockquote 之前，为 body 首元素）
        logo_img = None
        prev = highlight_tag.previous_sibling
        while prev and not prev.name:
            prev = prev.previous_sibling
        if prev and prev.name == 'img' and prev.get('alt') == 'AstralSeek Lab logo':
            logo_img = prev
        result["has_logo_banner"] = logo_img is not None
        if not logo_img:
            result["issues"].append("AstralSeek Lab logo banner 缺失或未位于核心亮点 blockquote 之前")
            result["ok"] = False

    # 4. 文末引用
    blockquotes = body.find_all('blockquote')
    result["blockquote_count"] = len(blockquotes)
    if len(blockquotes) >= 2:
        result["has_end_reference"] = True
    elif len(blockquotes) == 1:
        ref_text = blockquotes[0].get_text('\n', strip=True)
        if highlight_tag is not None and highlight_tag == blockquotes[0]:
            result["has_end_reference"] = False
            result["issues"].append("<blockquote> 被核心亮点占用，文末引用缺失")
            result["ok"] = False
        elif 'http' in ref_text or 'et al.' in ref_text or 'DOI' in ref_text or 'doi' in ref_text:
            result["has_end_reference"] = True
            if highlight_tag is None:
                result["issues"].append("核心亮点缺失，仅有文末引用")
                result["ok"] = False
        else:
            result["has_end_reference"] = False
            result["issues"].append("文末引用 blockquote 可能缺失")
            result["ok"] = False
    else:
        result["has_end_reference"] = False
        result["issues"].append("未检测到 <blockquote>")
        result["ok"] = False

    # 5. 段落对齐（2026-11-02 修正：原口径把 justify 当违例）
    # 正文段落须 justify；图注等居中小块允许 center；blockquote 内不计。
    total_align = 0
    bad_align = []
    for tag in soup.find_all('p'):
        style = tag.get('style', '') or ''
        if tag.find_parent('blockquote') is not None:
            continue
        if 'text-align' in style:
            total_align += 1
            if 'justify' not in style and 'center' not in style:
                bad_align.append(style[:40])
        else:
            bad_align.append('缺少 text-align')
    result["text_align_total"] = total_align
    result["text_align_bad"] = bad_align
    if bad_align:
        result["issues"].append(f"{len(bad_align)} 处段落未设置 justify")
        result["ok"] = False

    # 6. </strong>：
    bad_strong = raw.count('</strong>：')
    result["bad_strong_colon_count"] = bad_strong
    if bad_strong > 0:
        result["issues"].append(f"存在 {bad_strong} 处 '</strong>：' 断行风险")
        result["ok"] = False

    # 7. emoji
    if has_emoji(soup.get_text()):
        result["issues"].append("检测到 emoji")
        result["ok"] = False

    # 8. 图片
    imgs = soup.find_all('img')
    figures = soup.find_all('figure')
    result["img_count"] = len(imgs)
    result["figure_count"] = len(figures)

    # 9. figcaption
    figcaptions = soup.find_all('figcaption')
    result["figcaption_count"] = len(figcaptions)
    vague_captions = []
    for fc in figcaptions:
        text = fc.get_text(strip=True)
        if any(v in text for v in ["关键结果展示", "结果展示", "关键结果", "如图所示", "Fig"]) and len(text) < 25:
            vague_captions.append(text[:60])
    if vague_captions:
        result["issues"].append(f"存在 {len(vague_captions)} 处可能泛泛的 fig-caption")
        result["ok"] = False
    result["vague_captions"] = vague_captions

    # 10. end-note
    if soup.find_all(class_="end-note"):
        result["issues"].append("存在 <div class=\"end-note\">（微信编辑器解析异常风险）")
        result["ok"] = False

    # 11. 免责两层（v5.9.4：两层措辞用户亲改——「智能体环境实测可运行 / 可被复现，不构成对其科学性的认可」；
    #     旧句「不构成对论文科学结论的认可」不再检查；「不构成医疗建议」与尾注「校验通过 ≠ 结论正确」仍废止）
    text_all = soup.get_text(' ', strip=True)
    has_liability = ('不构成对其科学性的认可' in text_all)
    result["has_liability"] = has_liability
    if not has_liability:
        result["issues"].append("免责两层不完整：须出现「不构成对其科学性的认可」")
        result["ok"] = False
    for retired in ('不构成医疗建议', '校验通过 ≠ 结论正确'):
        if retired in text_all:
            result["issues"].append(f"已废止文案仍出现：「{retired}」（顶层 v5.9 起不得写入）")
            result["ok"] = False

    return result


def format_result(res):
    lines = []
    lines.append("=" * 80)
    lines.append(f"文件：{res['path']}")
    lines.append(f"大小：{res.get('file_size_mb', 0):.2f} MB | 图片：{res.get('img_count', 0)} | figure：{res.get('figure_count', 0)}")
    lines.append(f"<h1>：{res.get('h1_count', 0)} | <blockquote>：{res.get('blockquote_count', 0)}")
    lines.append(f"body 前部元素：")
    for tag, text in res.get('front_elements', []):
        lines.append(f"  <{tag}> {text[:80]}")
    lines.append(f"封面在正文前：{'是' if res.get('cover_before_text') else '否'}")
    lines.append(f"核心亮点使用 blockquote：{'是' if res.get('highlight_in_blockquote') else '否'}")
    lines.append(f"logo banner：{'有' if res.get('has_logo_banner') else '缺失'}")
    lines.append(f"段落对齐：{res.get('text_align_total', 0)} 处声明 justify/center，异常 {len(res.get('text_align_bad', []))} 处")
    if 'one_sentence' in res:
        lines.append(f"一句话速读：{res['one_sentence_cn']} 中文字 | {res['one_sentence_total']} 总字符")
        lines.append(f"  内容：{res['one_sentence'][:220]}")
    if 'highlight_cn_chars' in res:
        lines.append(f"核心亮点中文字数：{res['highlight_cn_chars']}（≤300）| 总字符：{res['highlight_total_chars']}（≤450）")
        lines.append(f"  核心亮点摘要：{res.get('highlight_text', '')[:220]}")
    if 'missing_sections' in res:
        lines.append(f"核心亮点板块覆盖：{'完整' if not res['missing_sections'] else '缺少 ' + ', '.join(res['missing_sections'])}")
    lines.append(f"</strong>：数量：{res.get('bad_strong_colon_count', 0)}")
    lines.append(f"文末引用：{'有' if res.get('has_end_reference') else '缺失/存疑'}")
    if res.get("vague_captions"):
        lines.append(f"泛泛 caption：{', '.join(res['vague_captions'])}")
    if res["issues"]:
        lines.append("问题：")
        for issue in res["issues"]:
            lines.append(f"  - {issue}")
    else:
        lines.append("问题：无")
    lines.append("结论：" + ("通过" if res["ok"] else "未通过"))
    return "\n".join(lines)


def gather(paths):
    files = []
    for p in paths:
        pp = Path(p)
        if pp.is_file() and pp.suffix.lower() == '.html':
            files.append(pp)
        elif pp.is_dir():
            files.extend(sorted(x for x in pp.rglob('*.html') if not x.name.endswith('.bak')))
        else:
            print("跳过（不存在或非 HTML）：" + str(p))
    return sorted(set(files))


def main():
    ap = argparse.ArgumentParser(description='期刊 HTML 交付前 QA（2026-11-02 版）')
    ap.add_argument('paths', nargs='*', default=['.'], help='目录或 HTML 文件，可多个')
    ap.add_argument('--report', default=None, help='报告输出路径，默认写到第一个目录下的 QC记录.txt')
    args = ap.parse_args()

    paths = args.paths or ['.']
    html_files = gather(paths)
    if not html_files:
        sys.exit('未找到 HTML 文件')

    report_lines = []
    print("共发现 " + str(len(html_files)) + " 个 HTML 文件")
    for idx, html_path in enumerate(html_files, 1):
        print("[" + str(idx) + "/" + str(len(html_files)) + "] " + html_path.name)
        res = check_file(html_path)
        report_lines.append(format_result(res))
        print("    通过=" + str(res["ok"]))

    report_text = "\n\n".join(report_lines)
    if args.report:
        report_path = Path(args.report)
    else:
        base = Path(paths[0]) if Path(paths[0]).is_dir() else Path(paths[0]).parent
        report_path = base / 'QC记录.txt'
    report_path.write_text(report_text, encoding='utf-8')
    print("报告已保存至：" + str(report_path))

    failed = sum(1 for l in report_lines if '结论：未通过' in l)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())