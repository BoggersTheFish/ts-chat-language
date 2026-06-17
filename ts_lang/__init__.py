"""TSLC input compiler: normalize, dialogue acts, semantic frames, meaning graph."""

from ts_lang.compiler import compile_utterance
from ts_lang.frame_rules import evaluate_frame_rules
from ts_lang.resources import active_packs, pack_info, reload_resources, semantic_rules
from ts_lang.graph_diff import GraphDiff, diff_meaning_graphs
from ts_lang.graph_queries import acceptable_frame_nodes, rejected_scopes
from ts_lang.meaning_graph import (
    GraphValidationReport,
    MeaningEdge,
    MeaningGraph,
    MeaningNode,
    build_meaning_graph,
    validate_meaning_graph,
)
from ts_lang.slot_normalize import normalize_frame_slots
from ts_lang.types import CompiledTurn, DialogueActResult, NormalizedUtterance, SemanticFrame

__all__ = [
    "acceptable_frame_nodes",
    "active_packs",
    "CompiledTurn",
    "diff_meaning_graphs",
    "GraphDiff",
    "DialogueActResult",
    "GraphValidationReport",
    "MeaningEdge",
    "MeaningGraph",
    "MeaningNode",
    "NormalizedUtterance",
    "SemanticFrame",
    "build_meaning_graph",
    "compile_utterance",
    "evaluate_frame_rules",
    "normalize_frame_slots",
    "pack_info",
    "reload_resources",
    "semantic_rules",
    "rejected_scopes",
    "validate_meaning_graph",
]