<!-- alice:human -->

run_id：r_edb2cb362816

# ALICE-2026-0007 · Norris `2021`《Intervention Source Ontology》结构取证（主实现包）

## 一句话结论

对 `bcio_source.owl` 的自算结果：本地类 202、子类边 391、对象属性 50、注释属性 56、最大层级深度 11（边数）、本地叶类 147；与论文自报（v0.1 实体 190／v0.2 实体 186／v0.3 层级 6）的差额逐件落在 `deviations/`。

## 口径要点（人读）

- 本地命名空间按「宿主＋最集中目录」一次算主值：`http://humanbehaviourchange.org/ontology/`；三个对照读法（去文件名／`BCIO_` 前缀／最多前缀）各算各的、全与本值同数，已在 `deviations/contrast.json` 逐行写明「巧合，不是判据」。
- L2＝391 与三档划分来自同一次遍历，另一次独立遍历复核同值（两边各自数出，未用减法）；三档为「本地→本地」`160`、「本地→外部」`45`、「主体外部」`186`（其中外部→外部 `182`、外部→本地 `4`）；宾语为匿名 `owl:Restriction` 的 `13` 条单列在 `tiers.json` 的 `anon_subclass_objects`，全件 `subClassOf` 元素总数 `404` 落在 `readings_alt.partition_total`。
- 另报（`deviations/readings.json`，恰 `7` 条）：`L3_local=18`、`L4_local=0`、`L5_alt=6`、`L5_selfcheck=0`、`L6_alt=144`、`anonymous_class=4`、`anonymous_class_direct=0`。两个匿名类读法不同（全树 `4` 个匿名 `owl:Class` 全部嵌在 `owl:equivalentClass` 之下、没有一个是 `owl:Class` 的直接子节点），按题面 §二.3 记此分歧一条。
- L5 的另一读法（本地子图）得 `6`；自检值「本地类中无任何父类者」得 `0`；三个数分列，未混成一个。L6 的另一读法（外部子类也算）得 `144`。L5 最深链有两条并列（`BCIO_010048`／`BCIO_010049`），`diff_A03.json` 取链节点 IRI 字典序最小的那条。
- `diff_A03.json` 的 `measured` 按层级数同尺填 `L5＋1`（`12`），`gap=6`、`direction=实测多`；其 `items[]` 只列最深链上**子类为本地类**的 `7` 条边（`key`＝子类 IRI）——根段 `4` 条边的子类是外部 `BFO` 类，判分器 D7 要求 `items[].key ∈ L1 成员集`，链的全程（含 `4` 条外部边）在此记述：根 `BFO_0000001` → `BFO_0000002` → `BFO_0000020` → `BFO_0000017` → `BFO_0000023` → 本地段 `BCIO_010003` → `BCIO_010004` → `BCIO_010006` → `BCIO_010044` → `BCIO_010045` → `BCIO_010047` → `BCIO_010048`。
- 对照件面：与 `0005`（上层件）算包含——共有 `66`、仅本件 `136`、仅对照件 `0`；与 `0008`（风格件）算交叠——共有 `82`、仅本件 `120`、仅对照件 `1222`；逐类 IRI 全列在 `deviations/overlap.json`。
- 语料面：`paper_text.txt` 实测 `86` 行，其中 p 行 `55`（节标题 `13`＋步骤标题 `14`＋表题 `2`＋表头行 `2` 不计）；母件 XML 未随包投递，主文取文档序第一个 `<body>`，序号 `1`。`13` 个锚的落点与取值见 `evidence/anchors.json` 与 `task.json#quoted`，两处逐条同值。
- `evidence/mapping.jsonl` 不适用（本单不做逐类回指），已在机器段 `not_applicable[]` 登记。
- 自检包内 `schema/selfcheck.py` 仍按旧 schema 要求 `inputs.lock` 带 `license` 列；本题面 §10.1 与判分器（`35B82345`）均已退役该列，以判分器为准。

## 能拿去干什么

- 六个 K 量都可只凭主件复算：入口定名见 `evidence/entries.json`，实现在本包 `code/`。
- 两包对账：本包为主实现（递归遍历），另一实现包用不同解析器与迭代遍历独立重算；六量同值才可信，不等须逐条给理由。


<!-- alice:machine -->

```json
{
  "task_id": "ALICE-2026-0007",
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
    "deviations/contrast.json",
    "deviations/diff_A01.json",
    "deviations/diff_A02.json",
    "deviations/diff_A03.json",
    "deviations/overlap.json",
    "deviations/readings.json",
    "deviations/tiers.json",
    "evidence/anchors.json",
    "evidence/entries.json",
    "evidence/ns.json",
    "evidence/protocol.json"
  ],
  "not_applicable": [
    "evidence/mapping.jsonl"
  ],
  "must": [
    "evidence/ns.json",
    "evidence/anchors.json",
    "evidence/protocol.json",
    "evidence/entries.json",
    "deviations/tiers.json",
    "deviations/overlap.json",
    "deviations/contrast.json",
    "deviations/readings.json",
    "deviations/diff_A01.json",
    "deviations/diff_A02.json",
    "deviations/diff_A03.json"
  ],
  "b_only": [
    "evidence/independence.json"
  ],
  "corpus_lines": 86,
  "para_lines": 55,
  "body_ordinal": 1,
  "nulls": [],
  "entry": "code/quant.py",
  "params": [
    "peer_held",
    "readings_names",
    "reads_count"
  ],
  "judge": "task.json#judge"
}
```
