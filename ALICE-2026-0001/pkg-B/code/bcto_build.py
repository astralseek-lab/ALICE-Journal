"""ALICE-2026-0001 · pkg-B 证据/偏差件构建器（独立第二实现）。

XML 母件用 xml.dom.minidom 读（与 A 的 ElementTree 不同 API）；语料按行流式读、
自行切节（先定 Methods/Results 标题行，再取区间内 Step 前缀标题行，各算止界）。
用法：在包目录下 `python code/bcto_build.py`（输入副本在研究夹根）。
"""
from __future__ import annotations

import hashlib
import json
import re
import xml.dom.minidom
from pathlib import Path

from bcto_scan import scan_owl, local_set, iri_dir, _all, EVD, DVD, SEP, _p

HERE = Path(__file__).resolve().parent.parent
RESEARCH = HERE.parent


def canon_sha(payload) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def dump(rel: str, obj) -> None:
    p = HERE / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def set_block(keys) -> dict:
    items = [{"key": k, "ord": i + 1} for i, k in enumerate(keys)]
    return {"items": items, "rows": len(items), "sha256": canon_sha(items)}


def map_block(pairs) -> dict:
    items = [{"key": k, "value": v} for k, v in sorted(pairs, key=lambda kv: kv[0])]
    return {"items": items, "rows": len(items), "sha256": canon_sha(items)}


# ── 语料：按行流式读 ─────────────────────────────────────────────────────────
def iter_lines():
    with open(RESEARCH / "paper_text.txt", encoding="utf-8") as fh:
        for ln in fh:
            yield ln.rstrip("\n")


def squash(s: str) -> str:
    return re.sub(r"\s+", " ", s)


def section_steps():
    """自行切节：Methods 标题行到 Results 标题行为界；区间内整行逐字匹配 `Step N: ` 前缀
    （N=1..6 连续）的标题行；每步止于下一标题行前一行，末步止于 Results 前一行。
    禁用「按位置取前 N 个」与「标题去重读数」。"""
    lines = [squash(ln) for ln in iter_lines()]
    m_line = next(i for i, ln in enumerate(lines, 1) if ln == "Methods")
    r_line = next(i for i, ln in enumerate(lines, 1) if ln == "Results")
    steps = []
    for i in range(m_line, r_line):
        ln = lines[i - 1]
        m = re.match(r"^Step (\d+): ", ln)
        if m:
            steps.append((int(m.group(1)), i, ln))
    assert [s[0] for s in steps] == [1, 2, 3, 4, 5, 6], "Step 前缀未连续成 1..6"
    out = []
    for j, (n, start, title) in enumerate(steps):
        end = (steps[j + 1][1] - 1) if j + 1 < len(steps) else (r_line - 1)
        out.append((n, start, end, title))
    return m_line, r_line, out


def build_protocol():
    m_line, r_line, steps = section_steps()
    return {
        "rule": "步骤＝Methods 直系 sub-sec 中标题以 `Step N: `（N=1..6 连续）起头的 6 个；"
                "起止行＝该步标题行至下一 title 行前一行（不分层级）；"
                "「按位置取前 N 个」与「标题去重读数」都禁用",
        "source": f"paper_text.txt#L{m_line}-L{r_line - 1}",
        "steps": [
            {"pos": n, "label": f"S{n}", "title": title, "src": "paper_text.txt", "kind": "line",
             "target": f"paper_text.txt#L{start}-L{end}",
             "evidence_loc": f"paper_text.txt#L{start}-L{end}",
             "input": None, "output": None}
            for n, start, end, title in steps
        ],
    }


def build_anchors(scan):
    lines = [squash(ln) for ln in iter_lines()]

    def grab(line_no, pattern):
        m = re.search(pattern, lines[line_no - 1])
        if not m:
            raise RuntimeError(f"锚定位失败 L{line_no}")
        return m.group(1)

    a01 = int(grab(58, r"The first release of the BCTO consisted of (\d+)"))
    a02 = int(grab(53, r"The revised version of the BCTO following expert review had (\d+)"))
    a34 = re.findall(r"a=(\d+\.\d+)", lines[54])
    a05 = grab(80, r"(\w+) hierarchical levels")

    dom = xml.dom.minidom.parse(str(RESEARCH / "fulltext__PMC10427801.xml"))
    a11 = None
    for am in dom.getElementsByTagName("article-meta"):
        for c in am.childNodes:
            if c.nodeType == c.ELEMENT_NODE and c.tagName == "article-id" and c.getAttribute("pub-id-type") == "doi":
                a11 = "".join(n.data for n in c.childNodes if n.nodeType == n.TEXT_NODE).strip()
                break
        if a11:
            break
    a07 = None
    for tw in dom.getElementsByTagName("table-wrap"):
        lab = tw.getElementsByTagName("label")
        if lab and "".join(n.data for n in lab[0].childNodes if n.nodeType == n.TEXT_NODE).strip() == "Table 2.":
            th = tw.getElementsByTagName("thead")[0].getElementsByTagName("th")[0]
            a07 = "".join(n.data for n in _text_nodes(th)).strip()
            break

    a12, a13 = scan.version_iri, scan.ont_about
    return [
        {"id": "A01", "value": a01, "source": "paper_text.txt#L58"},
        {"id": "A02", "value": a02, "source": "paper_text.txt#L53"},
        {"id": "A03", "value": float(a34[0]), "source": "paper_text.txt#L55"},
        {"id": "A04", "value": float(a34[1]), "source": "paper_text.txt#L55"},
        {"id": "A05", "value": a05, "source": "paper_text.txt#L80"},
        {"id": "A06", "value": lines[58], "source": "paper_text.txt#L59"},
        {"id": "A07", "value": a07, "source": "paper_text.txt#L60"},
        {"id": "A08", "value": lines[10], "source": "paper_text.txt#L11"},
        {"id": "A09", "value": lines[14], "source": "paper_text.txt#L15"},
        {"id": "A10", "value": lines[19], "source": "paper_text.txt#L20"},
        {"id": "A11", "value": a11, "source": "fulltext__PMC10427801.xml#front/article-meta/article-id[@pub-id-type='doi']"},
        {"id": "A12", "value": a12, "source": f"bcto.owl#{a12}"},
        {"id": "A13", "value": a13, "source": f"bcto.owl#{a13}"},
    ]


def _text_nodes(el):
    out = []

    def rec(e):
        for n in e.childNodes:
            if n.nodeType == n.TEXT_NODE:
                out.append(n)
            elif n.nodeType == n.ELEMENT_NODE:
                rec(n)
    rec(el)
    return out


def para_and_body():
    """归行口径（题面 §5.2）：body_ordinal＝文档序第一个 <body>；para_lines＝主文 body 内
    在 sec 内、不在 table-wrap／table-wrap-foot／fn／list-item／fig 内的 <p> 数
    （boxed-text 内的 p 属正文 sec 内，起行）。迭代（显式栈），不递归。"""
    dom = xml.dom.minidom.parse(str(RESEARCH / "fulltext__PMC10427801.xml"))
    bodies = dom.getElementsByTagName("body")
    main = bodies[0]
    count = 0
    stack = [main]
    while stack:
        el = stack.pop()
        if el.nodeType != el.ELEMENT_NODE:
            continue
        if el.tagName == "p":
            anc = []
            p = el.parentNode
            while p is not None and p.nodeType == p.ELEMENT_NODE:
                anc.append(p.tagName)
                p = p.parentNode
            if "sec" in anc and not ({"table-wrap", "table-wrap-foot", "fn", "list-item", "fig"} & set(anc)):
                count += 1
        stack.extend(reversed(el.childNodes))
    return count, 1, len(bodies)


def contrast_rows(scan):
    """三个命名空间对照值（禁用读法的事后对照，不作判据）。"""
    _host, _dir, local, named = local_set(scan)
    base = scan.ont_about.rsplit("/", 1)[0] + "/"
    c1 = sum(1 for i in named if i.startswith(base))

    def lname(iri):
        i = max(iri.rfind("/"), iri.rfind("#"))
        return iri[i + 1:]

    c2 = sum(1 for i in named if lname(i).startswith("BCIO_"))
    pref = {}
    for i in named:
        m = re.match(r"[A-Za-z]+", lname(i))
        p = m.group(0) if m else ""
        pref[p] = pref.get(p, 0) + 1
    top = None
    for k in sorted(pref):
        if top is None or pref[k] > pref[top]:
            top = k
    c3 = sum(1 for i in named if lname(i).startswith(top + "_"))
    ref = {"code": _p("code", "bcto_build.py"), "entry": "contrast_rows", "params": {}}
    return [
        {"rule": "rdf:about 去文件名当目录（禁用读法对照；与主口径同值纯属巧合，不是判据）", "hits": c1, "derivation_ref": ref},
        {"rule": "类名前缀 BCIO_ 判本地（禁用读法对照；与主口径同值纯属巧合，不是判据）", "hits": c2, "derivation_ref": ref},
        {"rule": "出现最多的前缀判本地（禁用读法对照；与主口径同值纯属巧合，不是判据）", "hits": c3, "derivation_ref": ref},
    ]


def main():
    scan = scan_owl(RESEARCH / "bcto.owl")
    d = _all(scan)
    host, nsdir, local, named = d["host"], d["dir"], d["local"], d["named"]

    def lname(iri):
        i = max(iri.rfind("/"), iri.rfind("#"))
        return iri[i + 1:]

    prefix_iris = sorted(i for i in named if lname(i).startswith("BCIO_"))
    sym = sorted(set(prefix_iris) ^ local)
    dump(_p(EVD, "ns.json"), {
        "rule": "宿主＝owl:Ontology@rdf:about 的 netloc，在该 host 下取类最集中的目录；"
                "IRI 逐条 urlsplit 划界（不用类名前缀／versionIRI 退段／rdf:about 去文件名）",
        "host": host, "dir": nsdir, "count": len(local), "prefix_count": len(prefix_iris),
        "coincidence": {"equal": len(sym) == 0, "sym_diff": sym},
        "classes": [{"iri": i, "in_ns": i in local} for i in sorted(named)],
        "prefix_iris": prefix_iris,
    })

    anchors = build_anchors(scan)
    dump(_p(EVD, "anchors.json"), anchors)
    dump(_p(EVD, "protocol.json"), build_protocol())

    edges = scan.edges_res
    t1 = sorted(f"{s}|{o}" for s, o in edges if s in local and o in local)
    t2 = sorted(f"{s}|{o}" for s, o in edges if s in local and o not in local)
    t3 = sorted(f"{s if s else '@anonymous#0'}|{o}" for s, o in edges if s not in local)
    anon_keys = sorted(f"{s}|{o}" for s, o in scan.edges_anon)
    dump(_p(DVD, "tiers.json"), {
        "tier1": set_block(t1), "tier2": set_block(t2), "tier3": set_block(t3),
        "anon_subclass_objects": set_block(anon_keys),
        "readings_alt": map_block([("partition_total", len(edges) + len(scan.edges_anon))]),
    })
    dump(_p(DVD, "overlap.json"), {"peers": {}, "unavailable": []})
    dump(_p(DVD, "contrast.json"), contrast_rows(scan))

    self_un = {a["id"]: a["value"] for a in anchors if a["id"] in ("A02", "A03", "A04", "A05")}
    readings = []
    from bcto_scan import iri_netloc
    l3_local = sum(1 for i in set(scan.obj_props) if iri_netloc(i) == host and iri_dir(i) == nsdir)
    l4_local = sum(1 for i in set(scan.ann_props) if iri_netloc(i) == host and iri_dir(i) == nsdir)
    for name, val in (
        ("L3_local", l3_local),
        ("L4_local", l4_local), ("L5_alt", d["L5_alt"]), ("L5_selfcheck", d["L5_selfcheck"]),
        ("L6_alt", d["L6_alt"]),
        ("anonymous_class", scan.anon_class_count),
    ):
        el = {"name": name, "kind": "scalar", "value": val}
        el["sha256"] = canon_sha({"name": name, "kind": "scalar", "value": val})
        readings.append(el)
    el = {"name": "self_report_unmeasured", "kind": "map", "value": self_un}
    el["sha256"] = canon_sha({"name": "self_report_unmeasured", "kind": "map", "value": self_un})
    readings.append(el)
    dump(_p(DVD, "readings.json"), readings)

    a01 = next(a["value"] for a in anchors if a["id"] == "A01")
    items = [{"key": iri, "ord": i + 1} for i, iri in enumerate(sorted(local))]
    gap = len(local) - a01
    dump(_p(DVD, "diff_A01.json"), {
        "anchor": "A01", "measured": len(local), "self_reported": a01,
        "items": items, "rows": len(items), "gap": gap,
        "direction": "实测多" if gap > 0 else ("自报多" if gap < 0 else "相等"),
        "sha256": canon_sha({"anchor": "A01", "measured": len(local), "self_reported": a01, "items": items}),
    })

    dump(_p(EVD, "independence.json"), {
        "source": "pkg-B 由 xml.sax 流式＋迭代遍历＋urlsplit 划界独立实现；语料按行流式自行切节",
        "shared_code_with_a": False,
        "entry": _p("code", "bcto_scan.py"),
        "signer_pkg_id": "pkg-B",
    })
    print(json.dumps({k: d[k] for k in sorted(d) if k.startswith("L")}, sort_keys=True))


if __name__ == "__main__":
    main()
