# -*- coding: utf-8 -*-
"""ALICE-2026-0009 六个 K 量的固定入口（pkg-B 独立实现；题面 §九 给定名，两包同名）。

实现面与 pkg-A 相互独立：minidom 解析、迭代遍历、流式一次过计数、urlsplit 划界。
每个入口签名 (path, params=None)，返回裸整数。
"""
from __future__ import annotations

import sdo_dom


def l1_local_classes(path, params=None):
    """L1 本地类数：有 rdf:about 且 IRI 落在本地命名空间的 owl:Class，按 IRI 去重。"""
    return len(sdo_dom.scan(path)["local_set"])


def l2_subclass_edges(path, params=None):
    """L2 子类边数：全件 rdfs:subClassOf@rdf:resource 三元组，按条计、不去重。"""
    return len(sdo_dom.scan(path)["edges"])


def l3_object_properties(path, params=None):
    """L3 对象属性数：owl:ObjectProperty 按 IRI 去重，全件计（含外部内联声明）。"""
    return len(sdo_dom.scan(path)["object_properties"])


def l4_annotation_properties(path, params=None):
    """L4 注释属性数：owl:AnnotationProperty 按 IRI 去重，全件计。"""
    return len(sdo_dom.scan(path)["annotation_properties"])


def l5_max_depth(path, params=None):
    """L5 最大层级深度：全图根沿 subClassOf 下行到最远本地类的边数（环由同边只走一次断开）。"""
    data = sdo_dom.scan(path)
    return sdo_dom.max_depth_from_roots(data, sorted(data["local_set"]))


def l6_leaf_classes(path, params=None):
    """L6 叶类数：本地类中无本地子类者（只看本地→本地的边）。"""
    return sdo_dom.leaf_local(sdo_dom.scan(path))
