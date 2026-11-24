# pkg-A code/ 说明

- `metrics.py`：K=6 量主实现（openpyxl，`data_only=True`）。六个入口函数
  `t1_sheet_count`／`t2_ontology_sheets`／`t3_external_class_count`／
  `t4_data_rows_sum`／`t5_level_cols_sum`／`t6_cross_sheet_ids`，
  签名统一为 `(xlsx_path, params)`；`main()` 一次算全六量并打印 JSON。
- `make_evidence.py`：从输入件实算并写出 `evidence/` 与 `deviations/` 四件
  （protocol／anchors／readings／contrast）。锚值不预填，全部现场定位。

复现：`python code/metrics.py <xlsx 路径>`；`python code/make_evidence.py <研究夹根>`。
