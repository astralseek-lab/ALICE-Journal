# code/ · 人门件

唯一入口：`code/moa_entry.py::parse(input_path, params)`。

- `input_path`：bcio_moa.owl 的路径（判分器扰动后副本同签名）。
- `params["quantity"]`：七键之一（`L1_class_local`／`L2_subclass_edges`／`L3_object_props`／`L4_annotation_props`／`L5_depth_max`／`L6_leaf_classes`／`X_ext_classes`）。
- 返回：`{"quantity", "v", "unit"[, "by_namespace"]}`，断言值在键 `v` 上。

实现口径见 `moa_entry.py` 文件头 docstring；只做 RDF/XML 结构解析，不做 OWL 推理。
