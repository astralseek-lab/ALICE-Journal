<!-- alice:human -->
run_id：`r_074a2f703f02`

# ALICE-2026-0001 · pkg-A（主实现）

本包是 Marques `2024`（Wellcome Open Research，BCTO 首发版）本体任务包的主实现：
六个 K 量（L1–L6）全部从 `bcto.owl` 全件结构遍历自算（只做 XML 结构解析，不做 OWL
推理、不联网、不手改输入）；`paper_text.txt` 只作锚与 protocol 的文本面；
`fulltext__PMC10427801.xml` 只是锚 A11 的取位面。实现路径：`xml.etree.ElementTree`
整树解析＋递归遍历＋建索引计数＋IRI 前缀比较外的 urlsplit 划界（题面 §5.3bis 允许面）。
命名空间判定链：宿主＝`owl:Ontology@rdf:about` 的 netloc，在该 host 下取类最集中的目录
（留痕 `evidence/ns.json` 八字段）；题面 §2.4 禁用三条（类名前缀／versionIRI 退段／
rdf:about 去文件名）一律未用于主值，三读数的事后对照在 `deviations/contrast.json`，
本件三读数与主口径同值属巧合、不作判据。

## 复跑

在本包目录下执行 `python code/build_evidence.py` 可从研究夹根的三件输入重算
`evidence/` 与 `deviations/` 全部内容；六个 K 量入口在 `code/ontology_metrics.py`
（`def <entry>(input_path, params)`）。

## 口径备注与记伤（供 F9 人判）

- L5 主口径按题面 §2.1 写死：起点＝全图根（含外部顶层类），深度＝到最远本地类节点的边数；
  本件实算 L5 加一后与论文自报层级数（锚 A05）不一致，差异大于一，不属「计数惯例 clash」
  的差一情形——如实登记在此，不判实现错、不改口径迁就（题面 §2.1 L5 行预登记）。
  另读法 L5_alt（只走两端皆本地的边）与自检值 L5_selfcheck 在 `deviations/readings.json`。
- 匿名子类另报：本件全树匿名主语的 subClassOf 为 `0` 条（`deviations/tiers.json` 的
  tier3 主体均为具名外部类），故无匿名子类叶计入问题。
- A05 记伤（题面 §三已披露）：范围单原文写「Conclusion 节内」，F2 新语料实测该句在
  Discussion 首段；定位串全文恰 `1` 处、取值规则不受影响。
- `deviations/readings.json` 第 `7` 条 `self_report_unmeasured` 采用签面模板
  键集（name/kind/value/sha256，map 的 value 为对象）：判分器的 map 逐项校验只收
  整数或串，而 A03／A04 自报信度是小数——按「题面与判分器冲突时以判分器为准」处置，
  值与 `evidence/anchors.json` 逐字同值。
- `inputs.lock` 的 `paper_text.txt` 行同时带 `uri`（基名＝研究夹根相对路径，供
  定位串文法与发布面白名单）与 `doi`（全串，题面 §10.1「本单语料件用 doi」）。
- 本单不持有对照件：`deviations/overlap.json` 两数组在场、内容为空（空集不等于不交）。
- 判分器已知红：无（本件 K 数源为 RDF/XML，drop 族探针四型实体均有定义面，
  判据 `10`／`12`／`20` 实测全绿）。

<!-- alice:machine -->
```json
{
  "b_only": [],
  "body_ordinal": 1,
  "corpus_lines": 99,
  "extras": [
    "evidence/ns.json",
    "evidence/anchors.json",
    "evidence/protocol.json",
    "deviations/tiers.json",
    "deviations/overlap.json",
    "deviations/contrast.json",
    "deviations/readings.json",
    "deviations/diff_A01.json"
  ],
  "files": [
    "README.md",
    "task.json",
    "evidence.graph.json",
    "claims.jsonl",
    "env.lock",
    "inputs.lock",
    "code/"
  ],
  "must": [
    "evidence/ns.json",
    "evidence/anchors.json",
    "evidence/protocol.json",
    "deviations/tiers.json",
    "deviations/overlap.json",
    "deviations/contrast.json",
    "deviations/readings.json",
    "deviations/diff_A01.json"
  ],
  "not_applicable": [
    "evidence/mapping.jsonl"
  ],
  "nulls": [
    {
      "path": "protocol.steps[0].input",
      "reason": "范围单未给逐步的逐字输入/输出串，自撰即违「只许引用」（题面 §4.2）"
    },
    {
      "path": "protocol.steps[0].output",
      "reason": "范围单未给逐步的逐字输入/输出串，自撰即违「只许引用」（题面 §4.2）"
    },
    {
      "path": "protocol.steps[1].input",
      "reason": "范围单未给逐步的逐字输入/输出串，自撰即违「只许引用」（题面 §4.2）"
    },
    {
      "path": "protocol.steps[1].output",
      "reason": "范围单未给逐步的逐字输入/输出串，自撰即违「只许引用」（题面 §4.2）"
    },
    {
      "path": "protocol.steps[2].input",
      "reason": "范围单未给逐步的逐字输入/输出串，自撰即违「只许引用」（题面 §4.2）"
    },
    {
      "path": "protocol.steps[2].output",
      "reason": "范围单未给逐步的逐字输入/输出串，自撰即违「只许引用」（题面 §4.2）"
    },
    {
      "path": "protocol.steps[3].input",
      "reason": "范围单未给逐步的逐字输入/输出串，自撰即违「只许引用」（题面 §4.2）"
    },
    {
      "path": "protocol.steps[3].output",
      "reason": "范围单未给逐步的逐字输入/输出串，自撰即违「只许引用」（题面 §4.2）"
    },
    {
      "path": "protocol.steps[4].input",
      "reason": "范围单未给逐步的逐字输入/输出串，自撰即违「只许引用」（题面 §4.2）"
    },
    {
      "path": "protocol.steps[4].output",
      "reason": "范围单未给逐步的逐字输入/输出串，自撰即违「只许引用」（题面 §4.2）"
    },
    {
      "path": "protocol.steps[5].input",
      "reason": "范围单未给逐步的逐字输入/输出串，自撰即违「只许引用」（题面 §4.2）"
    },
    {
      "path": "protocol.steps[5].output",
      "reason": "范围单未给逐步的逐字输入/输出串，自撰即违「只许引用」（题面 §4.2）"
    }
  ],
  "para_lines": 66
}
```
