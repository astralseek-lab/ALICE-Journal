<!-- alice:human -->

run_id：r_85f2b62fa4fe

# ALICE-2026-0014 — Michie `2013` BCT 术语表 K＝`3` 量证据包（pkg-A 主实现）

## 结论
- Q1_items ＝ 93（条目行数）、Q2_clusters ＝ 16（簇数）、Q3_max_per_cluster ＝ 11（单簇最大条目数，第 `10` 簇）。
- 三量与论文自报逐值相同：锚 A01＝93 ↔ Q1、A02＝16 ↔ Q2，两份 diff 的 gap＝`0`、direction＝相等；A03（篇名片段）无同义实测端，已进 readings 的 self_report_unmeasured。
- 主口径：python-docx 读 esm1.docx 第 `4` 张物理表（`d.tables[3]`），行型判定只看 No. 列取值形态；terms_bct_v1.csv 按声明列位直接数为对读，两读同值；pkg-B 独立第二实现三量同值。
- 另报：min_items_per_cluster＝`3`、empty_definition_count＝`0`、pdf_pages＝`15`、docx_tables＝`4`（均在 deviations/readings.json，共 `5` 条）。
- protocol：Methods 下八步（kind=line，整行逐字，L343–L516，区外同形复述 `6` 处披露不计）；contrast（A10 簇名对照：第 `4` 张物理表簇标题在第 `3` 张物理表逐格子串检索）实测差异 `0` 条，hits=`0`。

## 判分器已知红（题面写死的口径所致，非实现缺陷；不改 source 换绿）
1. 判据 `1`（E1 锚落点核验）：`13` 条锚的 source 按题面写死指向 fulltext.pdf（页级定位）与 esm1.docx（`#tbl@` 定位）；判分器对非 `#L` 型 source 只做「value 是原件裸文本子串」判，而 PDF 与 docx 都是压缩二进制，任何锚值在裸字节里都命不中——照题面写 source 必红。A01／A02 两条数值锚因该判只认字符串型 value，同因而红。理由链：题面 §三 source 写死 → 二进制件裸文本判不适用 → 记红不改。
2. 判据 `11`（人面数字）：quoted 数值锚的 source 须为 `#L<n>` 型才被认作「指回原文」；A01／A02 的 source 按题面写死为 PDF 页级定位，故被判「指不回原文」。93 与 16 本身在 claims 值集内，人读段裸写合法。
3. 判据 `2`／`13`／`13b`／`13c`：复用装配期闸、需网关件复算 pkg_id；本机无网关件，按自检包 README §六 记「无法判」（退出码 `2`），非包缺陷。已自查：task_id ＝ 研究目录名、研究夹下无名单外 pkg-*、两包 pkg_id 互异。

## 不适用件理由（not_applicable[]，`4` 件）
- evidence/ns.json／evidence/mapping.jsonl／deviations/tiers.json：本体 kind 配套件，本单（terminology＋protocol）无本体件。
- deviations/overlap.json：本单不持有对照件（peer_held 为空集），不交。

## 扰动面（判据 `10`）
三条 primary 的 sensitivity 施力点均为 terms_bct_v1.csv 输入节点（行式件；esm1.docx 为二进制件，行式扰动无定义）：Q1 用 `drop:1`（删表头行）、Q2 用 `drop:10`（删表头＋首簇全部 `9` 条目行）、Q3 用 `drop:52`（删表头＋前 `9` 簇全部 `50` 条目行＋第 `10` 簇首行，最大簇削至与次大簇齐平）。

## 机器段说明
para_lines／body_ordinal 为 null（本单语料为 PDF 抽取文本、无 JATS 结构），已在机器段 nulls[] 记账；corpus_lines＝`1529`（splitlines 口径，\f 分页亦断行）。

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
  "b_only": [],
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
