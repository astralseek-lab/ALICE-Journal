<!-- alice:human -->

run_id：r_edb2cb362816

# ALICE-2026-0007 · Norris `2021`《Intervention Source Ontology》结构取证（独立第二实现包）

## 一句话结论

本包以 minidom＋显式栈迭代＋流式一次过计数独立重算，六量读数：本地类 202、子类边 391、对象属性 50、注释属性 56、最大层级深度 11（边数）、本地叶类 147，与主实现包逐量同值；论文自报侧（v0.1 实体 190／v0.2 实体 186／v0.3 层级 6）的差额与本包实测的对账见 `deviations/`。

## 独立性自述（人读）

- 解析器、遍历方式、计数方式、IRI 划界均独立选型；命名空间主口径按本包自己的判定函数独立算一次，三个对照读数（去文件名／`BCIO_` 前缀／最多前缀）各附推导写进 `deviations/contrast.json`，三者与主值同数处均写明「巧合，不是判据」。
- 步数判定独立：先定位 `Methods`／`Results` 两个节标题整行，再按位置取其间连续的 `7` 个 `Step` 小节，不按标题去重（`Results` 内同形重列不进区间）。
- 匿名类清单由本包独立判定（扫描后统一回填编号），未读另一实现包的任何清单；`code/` 中对另一实现包的路径与标识引用为 `0` 处。
- 本包独有 `evidence/independence.json`（机器段 `b_only[]`）。

## 读数要点（与主实现包同值，口径各自实现）

- L2＝391 的三档：「本地→本地」`160`、「本地→外部」`45`、「主体外部」`186`（外部→外部 `182`＋外部→本地 `4`）；匿名宾语 `13` 条；`partition_total＝404`。两次独立遍历同值。
- 另报 `7` 条：`L3_local=18`、`L4_local=0`、`L5_alt=6`、`L5_selfcheck=0`、`L6_alt=144`、`anonymous_class=4`、`anonymous_class_direct=0`；两个匿名读法不同（`4` vs `0`），按题面 §二.3 记分歧一条。
- `diff_A03.json` 的 `measured` 为 `L5＋1`（`12`），`gap=6`、`direction=实测多`；`items[]` 按判分器 D7 口径只列子类为本地类的 `7` 条链边，根段 `4` 条外部边（`BFO_0000001`→…→`BFO_0000023`）在此记述。
- 对照件：`0005` 共有 `66`／仅本件 `136`／仅对照件 `0`（包含）；`0008` 共有 `82`／仅本件 `120`／仅对照件 `1222`（交叠）。
- 语料：`86` 行、p 行 `55`、主文 `body_ordinal=1`（母件 XML 未投递，按规则取文档序第一个 `<body>`，与主实现包判出同号）。
- `evidence/mapping.jsonl` 不适用，已登记 `not_applicable[]`；自检包旧 schema 的 `license` 列要求以判分器（`35B82345`）为准。

## 能拿去干什么

- 交叉验证：本包与主实现包同题独立作答，六量与另报可逐数对账；入口定名见 `evidence/entries.json`。


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
    "evidence/independence.json",
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
  "entry": "code/metrics.py",
  "params": [
    "peer_held",
    "readings_names",
    "reads_count"
  ],
  "judge": "task.json#judge"
}
```
