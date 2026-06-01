from __future__ import annotations

import argparse

from .sidecar_consumer_eval import run_chunk_sidecar_consumer_eval
from .sidecar_consumer_promotion import run_chunk_sidecar_consumer_promotion


_CHUNK_SIDECAR_CONSUMER_EVAL_FIELDS = (
    "output_dir",
    "source_set_id",
    "chunks_v2_dir",
    "sidecar_index_dir",
    "graph_dir",
    "claims_dir",
    "baseline_graph_summary_path",
    "baseline_claim_summary_path",
    "results_dir",
    "rebuild_sidecar",
    "allow_partial_extraction",
    "allow_partial_retrieval",
)


def run_chunk_sidecar_consumer_eval_command(args: argparse.Namespace):
    return run_chunk_sidecar_consumer_eval(
        **{field: getattr(args, field) for field in _CHUNK_SIDECAR_CONSUMER_EVAL_FIELDS}
    )


_CHUNK_SIDECAR_CONSUMER_PROMOTION_FIELDS = (
    "output_dir",
    "source_set_id",
    "consumer_eval_results_path",
    "results_dir",
    "apply",
    "replace_canonical",
)


def run_chunk_sidecar_consumer_promotion_command(args: argparse.Namespace):
    return run_chunk_sidecar_consumer_promotion(
        **{
            field: getattr(args, field)
            for field in _CHUNK_SIDECAR_CONSUMER_PROMOTION_FIELDS
        }
    )
