<!-- alice:human -->

run_id：`r_c7f99925a970`

# ALICE-2026-0005 · upper-level BCIO 六量复算（pkg-B）

## 一句话结论

按题面 §二 主口径自算：L1=`66`、L2=`255`（三档 `39`/`30`/`186`，三档之和＝L2）、L3=`50`、L4=`56`、L5=`8`、L6=`36`；L2 主遍历与独立复核遍历同值，无不一致事项可记。

- **能拿去干什么**：upper-level BCIO 本件的结构画像；对外依赖强度由 L2 第②档正面量（`30` 条主体本地·宾语外部的边）。
- **复现入口**：`code/quant_b.py` 内六个固定入口（§九）；产物生成入口 `emit_artifacts`（A-1）。
- **原文转述的数**：A01=`12`／A02=`21`／A03=`10`（标 quoted，指回 `paper_text.txt#L39` 与 `#L58`）。
- **另报**：`deviations/readings.json` 七条；其中 `L5_selfcheck`＝`0`——本地类全部有父类（含外部父类），按「无任何父类」数当然是零，它不是深度；「本地根」口径曾把一半单算成零，病根就是把这条自检值当成了 L5。
- **版本与imports**：`A12` 锚为本体自述版本串（本件自读、不跨件复用）；`owl:imports` 为空（`deviations/contrast.json` 第四行）。
- **对照件**：`bcio_style.owl` 只用于 `deviations/overlap.json` 求交集，不取任何 K 值。

<!-- alice:machine -->

```json
{
 "task_id": "ALICE-2026-0005",
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
 "corpus_lines": 95,
 "para_lines": 95,
 "body_ordinal": 1,
 "nulls": [],
 "entry": "code/quant_b.py::l1_local_classes",
 "params": [],
 "judge": "task.json#judge"
}
```
