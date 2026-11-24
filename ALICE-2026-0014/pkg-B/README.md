<!-- alice:human -->

run_id：r_85f2b62fa4fe

# ALICE-2026-0014 — Michie `2013` BCT 术语表 K＝`3` 量证据包（pkg-B 独立第二实现）

## 结论
- Q1_items ＝ 93、Q2_clusters ＝ 16、Q3_max_per_cluster ＝ 11（单簇最大条目数，第 `10` 簇），与 pkg-A 三量逐值相同。
- 三量与论文自报逐值相同：锚 A01＝93 ↔ Q1、A02＝16 ↔ Q2，两份 diff 的 gap＝`0`、direction＝相等。
- 独立面：docx 直解 word/document.xml（不经 python-docx）；CSV 手写 RFC4180 逐字符状态机流式一次过（不经标准库 csv）；计数按 No. 整数前缀分组（不读 cluster 列）并做编号守恒判（簇内连续、簇号不缺号，实测守恒）；protocol 自行从 paper_text.txt 重新定位八步标题；未 import 另一实现的任何模块。
- 另报：min_items_per_cluster＝`3`、empty_definition_count＝`0`、pdf_pages＝`15`、docx_tables＝`4`（均在 deviations/readings.json，共 `5` 条）；contrast 实测差异 `0` 条，hits=`0`。

## 判分器已知红（题面写死的口径所致，与 pkg-A 同因）
1. 判据 `1`（E1 锚落点核验）：`13` 条锚的 source 按题面写死指向 PDF／docx 二进制原件，非 `#L` 型 source 的「裸文本子串」判在压缩字节上必然命不中；A01／A02 数值锚同因。
2. 判据 `11`（人面数字）：A01／A02 的 quoted source 非 `#L<n>` 型，被判「指不回原文」；93 与 16 在 claims 值集内，裸写合法。
3. 判据 `2`／`13`／`13b`／`13c`：无网关件，装配期闸记「无法判」（退出码 `2`），非包缺陷。

## 不适用件理由（not_applicable[]，`4` 件）
- evidence/ns.json／evidence/mapping.jsonl／deviations/tiers.json：本体 kind 配套件，本单无本体件。
- deviations/overlap.json：本单不持有对照件（peer_held 为空集），不交。

## 扰动面（判据 `10`）
三条 primary 的 sensitivity 施力点均为 terms_bct_v1.csv 输入节点：Q1 用 `drop:1`、Q2 用 `drop:10`、Q3 用 `drop:52`（结构与 pkg-A 同口径）。

## 机器段说明
para_lines／body_ordinal 为 null（PDF 抽取文本、无 JATS 结构），已在 nulls[] 记账；corpus_lines＝`1529`。

<!-- alice:machine -->

```json
{
  "task_id": "ALICE-2026-0014",
  "files": [
    "README.md",
    "task.json",
    "evidence.graph.json",
    "claims.jsonl",
    "env.lock",
    "inputs.lock",
    "code/"
  ],
  "extras": [
    "evidence/anchors.json",
    "evidence/independence.json",
    "evidence/protocol.json",
    "deviations/contrast.json",
    "deviations/diff_A01.json",
    "deviations/diff_A02.json",
    "deviations/readings.json"
  ],
  "not_applicable": [
    "evidence/ns.json",
    "evidence/mapping.jsonl",
    "deviations/tiers.json",
    "deviations/overlap.json"
  ],
  "must": [
    "evidence/protocol.json",
    "evidence/anchors.json",
    "deviations/contrast.json",
    "deviations/readings.json",
    "deviations/diff_A01.json",
    "deviations/diff_A02.json"
  ],
  "b_only": [
    "evidence/independence.json"
  ],
  "corpus_lines": 1529,
  "para_lines": null,
  "body_ordinal": null,
  "nulls": [
    {
      "path": "readme.para_lines",
      "reason": "本单语料为出版社 PDF 抽取的行级文本，无 JATS <p> 结构，para_lines 不适用"
    },
    {
      "path": "readme.body_ordinal",
      "reason": "本单语料为出版社 PDF 抽取的行级文本，无 JATS <body> 元素，body_ordinal 不适用"
    }
  ],
  "entry": "code/metrics.py::count_items",
  "params": [],
  "judge": "task.json#judge"
}
```
