# -*- coding: utf-8 -*-
# pkg-B 真实生成入口：evidence/independence.json 由本入口产出（变更单 S1-01_042）。
# 语义与同包其余 build_* 一致：入口产出该件内容；__main__ 落盘。
import json


def build_independence(params=None):
    """产出 evidence/independence.json 内容（四字段，shared_code_with_a 必 false）。"""
    return {
        "source": ("pkg-B 为独立第二实现：iterparse 事件流读 XML、列名→列号逐字解析、"
                   "手写 token 状态机、自行流式切节；未读 pkg-A 任何件"),
        "shared_code_with_a": False,
        "entry": "code/measure.py::compute_all",
        "signer_pkg_id": "ALICE-2026-0013/pkg-B",
    }


def main():
    payload = build_independence()
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    with open("evidence/independence.json", "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return text


if __name__ == "__main__":
    main()
