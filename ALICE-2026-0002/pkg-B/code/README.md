# code/ · 人门件（pkg-B 独立实现）

唯一入口：`code/moa_entry_b.py::parse(input_path, params)`；锚对账：`code/b_anchors.py`。

- 解析器：`xml.dom.minidom` 建 DOM 后显式栈迭代（不用另一套解析器族）；
- 遍历：显式栈，无递归；
- 计数：单次遍历边扫边累计，不先建元素索引再回头数；
- IRI 划界：`urllib.parse.urlsplit` 取 scheme／netloc／path 再比命名空间；
- 不导入任何另一实现包的模块。

`params["quantity"]` 七键同另一实现包口径；返回 `{"quantity", "v", "unit"[, "by_namespace"]}`。
