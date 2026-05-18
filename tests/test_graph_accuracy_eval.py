from __future__ import annotations

from pathlib import Path
import tempfile

from usfs_r1_ea_sources.authority_relationship_eval import run_authority_relationship_eval
from usfs_r1_ea_sources.citation_alias_eval import run_citation_alias_eval
from usfs_r1_ea_sources.graph_accuracy_eval import run_graph_accuracy_eval
from usfs_r1_ea_sources.graph_health_eval import run_graph_health_eval

from tests.test_source_register_proving import build_test_proving_slice


def test_phase_1_5_eval_commands_pass_on_proving_slice() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir) / "source_library"
        build_test_proving_slice(output_dir)

        relationship_eval = run_authority_relationship_eval(output_dir=output_dir)
        alias_eval = run_citation_alias_eval(output_dir=output_dir)
        graph_health = run_graph_health_eval(output_dir=output_dir)
        graph_accuracy = run_graph_accuracy_eval(output_dir=output_dir)

        assert relationship_eval.summary["passed"] is True
        assert alias_eval.summary["passed"] is True
        assert graph_health.summary["passed"] is True
        assert graph_accuracy.summary["passed"] is True
