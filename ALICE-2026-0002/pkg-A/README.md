<!-- alice:human -->

# Schenk2023MoA · MoA 本体六量自算（pkg-A）

## 一句话结论

从 bcio_moa.owl 做纯 RDF/XML 结构解析（不推理、不联网、不改输入），自算六个量并逐量钉回证据图节点；四条计数 claim 带真扰动探针且扰动后值真动，两条属性 claim 因算子射程写明免探针理由。

- 本地类数 L1 ＝ 1705
- 子类边数 L2 ＝ 1905（内部 1449 ／ 指向外部 456，两者之和与总数相等）
- 对象属性数 L3 ＝ 53
- 注释属性数 L4 ＝ 56
- 最大层级深度 L5 ＝ 7（按边数；遍历中未遇到环，故无环断记录件）
- 叶类数 L6 ＝ 1220
- 另报：外部类 193（obo 169 ／ addicto 24 ／ other 0）

- **能拿去干什么**：作为 pkg-B 独立重算与论文锚对账的基准；六量口径逐字按题面，外部命名空间单列不进六量。
- **复现入口**：`code/moa_entry.py::parse`（唯一入口，按 `quantity` 分派）
- **原文转述的数**：论文自报最终版实体数 284、初始版 261、中间步骤识别 202、候选 MoA 分组 104（均标 `quoted` 并指回 paper_text.txt 行号）。论文口径只数 MoA 专域实体；本包 L1 的本地命名空间口径覆盖整个 BCIO 命名空间，两种口径不同属预期，逐项对账与偏离落名见 pkg-B 的 verdict。

<!-- alice:machine -->

```json
{
  "task_id": "ALICE-2026-0002",
  "files": ["README.md", "task.json", "evidence.graph.json", "claims.jsonl", "env.lock", "inputs.lock", "code/"],
  "entry": "code/moa_entry.py::parse",
  "params": ["quantity"],
  "judge": "task.json#judge"
}
```
