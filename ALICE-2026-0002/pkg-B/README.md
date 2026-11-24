<!-- alice:human -->

# Schenk2023MoA · pkg-B 独立重算与论文锚对账

## 一句话结论

换一套实现（minidom 建 DOM＋显式栈迭代＋单次遍历累计＋urlsplit 划界）把六个量再算一遍，与另一实现包逐量同值；十三锚逐条对账，两条数字锚判为预期内偏离并落名，verdict 按表判为 pass。

- 本地类数 L1 ＝ 1705
- 子类边数 L2 ＝ 1905（内部 1449 ／ 指向外部 456）
- 对象属性数 L3 ＝ 53
- 注释属性数 L4 ＝ 56
- 最大层级深度 L5 ＝ 7（按边数；未遇到环）
- 叶类数 L6 ＝ 1220
- 另报：外部类 193（obo 169 ／ addicto 24 ／ other 0）

- **能拿去干什么**：第二证人。本包不读另一实现包的任何文件；两包同值由监考官核。
- **复现入口**：`code/moa_entry_b.py::parse`（唯一入口）；锚对账 `code/b_anchors.py`。
- **原文转述的数**：论文自报最终版实体数 284、初始版 261（均标 `quoted`）。A01／A02 两条数字锚判为预期内偏离（论文口径只数 MoA 专域实体；本量按整个 BCIO 本地命名空间计），偏离全体落名于 `deviations/A01.jsonl` 与 `deviations/A02.jsonl`。

<!-- alice:machine -->

```json
{
  "task_id": "ALICE-2026-0002",
  "files": ["README.md", "task.json", "evidence.graph.json", "claims.jsonl", "env.lock", "inputs.lock", "code/"],
  "entry": "code/moa_entry_b.py::parse",
  "params": ["quantity"],
  "judge": "task.json#judge"
}
```
