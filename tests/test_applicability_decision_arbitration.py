from __future__ import annotations

import unittest

from usfs_r1_ea_sources.applicability_decision_arbitration import arbitrate_trigger_matches
from usfs_r1_ea_sources.applicability_decision_arbitration import arbitration_summary
from usfs_r1_ea_sources.applicability_decision_arbitration import flatten_groups
from usfs_r1_ea_sources.applicability_decision_arbitration import missing_trigger_groups
from usfs_r1_ea_sources.applicability_decision_arbitration import trigger_arbitration_not_evaluated
from usfs_r1_ea_sources.applicability_decision_arbitration import trigger_groups


class ApplicabilityDecisionArbitrationTests(unittest.TestCase):
    def test_trigger_groups_and_flatten_groups_normalize_terms(self) -> None:
        groups = trigger_groups([["road", "right-of-way"], [], "trail", None])
        self.assertEqual(groups, [["road", "right-of-way"], ["trail"]])
        self.assertEqual(flatten_groups(groups), ["right-of-way", "road", "trail"])

    def test_arbitrate_trigger_matches_accepts_required_strong_groups(self) -> None:
        arbitration = arbitrate_trigger_matches(
            candidate={
                "trigger_arbitration_contract": {
                    "required_trigger_groups": [["road"], ["right-of-way"]],
                    "minimum_strong_trigger_groups": 2,
                }
            },
            positive_match={
                "matched": True,
                "adjudication_notes": ["weak trail signal retained"],
                "trigger_group_results": [
                    _group_result("road", observed=2),
                    _group_result("right-of-way", observed=1),
                    _group_result("trail", weak=1),
                ],
            },
            negative_match={"matched": False, "adjudication_notes": []},
            coverage_boundary={"coverage_sufficient": True},
        )

        self.assertTrue(arbitration["positive_trigger_sufficient"])
        self.assertFalse(arbitration["requires_adjudication"])
        self.assertEqual(
            arbitration["arbitration_status"],
            "strong_positive_with_weak_auxiliary",
        )
        self.assertEqual(
            {tuple(group) for group in arbitration["decisive_trigger_groups"]},
            {("road",), ("right-of-way",)},
        )
        self.assertEqual(arbitration["weak_auxiliary_trigger_groups"], [["trail"]])
        self.assertEqual(arbitration["minimum_strong_trigger_groups"], 2)

    def test_arbitrate_trigger_matches_keeps_positive_negative_conflict_open(self) -> None:
        arbitration = arbitrate_trigger_matches(
            candidate={"trigger_arbitration_contract": {"required_trigger_groups": [["road"]]}},
            positive_match={
                "matched": True,
                "adjudication_notes": [],
                "trigger_group_results": [_group_result("road", observed=1)],
            },
            negative_match={
                "matched": True,
                "adjudication_notes": ["negative scope note"],
            },
            coverage_boundary={"coverage_sufficient": True},
        )

        self.assertFalse(arbitration["positive_trigger_sufficient"])
        self.assertTrue(arbitration["requires_adjudication"])
        self.assertEqual(arbitration["arbitration_status"], "positive_negative_conflict")
        self.assertEqual(arbitration["decisive_trigger_groups"], [["road"]])
        self.assertIn("negative scope note", arbitration["arbitration_notes"])

    def test_arbitrate_trigger_matches_supports_positive_precedence_policy(self) -> None:
        arbitration = arbitrate_trigger_matches(
            candidate={
                "trigger_arbitration_contract": {
                    "minimum_strong_trigger_groups": 1,
                    "positive_negative_conflict_policy": "positive_precedence",
                }
            },
            positive_match={
                "matched": True,
                "adjudication_notes": [],
                "trigger_group_results": [_group_result("road", observed=1)],
            },
            negative_match={
                "matched": True,
                "adjudication_notes": ["negative scope note"],
            },
            coverage_boundary={"coverage_sufficient": True},
        )

        self.assertTrue(arbitration["positive_trigger_sufficient"])
        self.assertFalse(arbitration["requires_adjudication"])
        self.assertEqual(arbitration["arbitration_status"], "strong_positive_decisive")
        self.assertEqual(
            arbitration["contract"]["positive_negative_conflict_policy"],
            "positive_precedence",
        )

    def test_arbitration_summary_reports_decision_effect_and_notes(self) -> None:
        summary = arbitration_summary(
            status="needs_adjudication",
            basis_type="unresolved_evidence_conflict",
            predicate_name="trigger_arbitration",
            positive_match={
                "matched": True,
                "adjudication_notes": ["weak trail signal"],
                "trigger_group_results": [_group_result("trail", weak=1)],
            },
            negative_match={
                "matched": False,
                "requires_adjudication": False,
                "adjudication_notes": [],
                "trigger_group_results": [],
            },
            trigger_arbitration={
                "arbitration_status": "weak_positive_only",
                "requires_adjudication": True,
                "decisive_trigger_groups": [],
                "weak_auxiliary_trigger_groups": [],
                "weak_only_trigger_groups": [["trail"]],
                "missing_required_trigger_groups": [["road"]],
                "minimum_strong_trigger_groups": 1,
                "arbitration_rationale": "Only weak positive trigger evidence was found.",
                "arbitration_notes": ["contract requires strong road evidence"],
            },
            source_evidence=[{"evidence_id": "SRC-1"}, {"evidence_id": "SRC-2"}],
            selected_retrieval_result_ids=["RET-1"],
            retrieval_trace_ids=["TRACE-1"],
            graph_path_ids=["GRAPH-1"],
        )

        self.assertEqual(
            summary["schema_version"],
            "applicability-evidence-arbitration-v0",
        )
        self.assertEqual(summary["decision_effect"], "blocked_by_weak_positive_trigger")
        self.assertTrue(summary["requires_adjudication"])
        self.assertEqual(summary["source_evidence_ids"], ["SRC-1", "SRC-2"])
        self.assertIn("weak trail signal", summary["arbitration_notes"])
        self.assertIn("contract requires strong road evidence", summary["arbitration_notes"])

    def test_arbitration_summary_reports_positive_precedence_effect(self) -> None:
        summary = arbitration_summary(
            status="applicable",
            basis_type="positive_package_trigger",
            predicate_name="trigger_arbitration",
            positive_match={
                "matched": True,
                "adjudication_notes": [],
                "trigger_group_results": [_group_result("road", observed=1)],
            },
            negative_match={
                "matched": True,
                "requires_adjudication": False,
                "adjudication_notes": [],
                "trigger_group_results": [_group_result("not part of project", observed=1)],
            },
            trigger_arbitration={
                "arbitration_status": "strong_positive_decisive",
                "requires_adjudication": False,
                "decisive_trigger_groups": [["road"]],
                "weak_auxiliary_trigger_groups": [],
                "weak_only_trigger_groups": [],
                "missing_required_trigger_groups": [],
                "minimum_strong_trigger_groups": 1,
                "arbitration_rationale": "Positive trigger evidence takes precedence.",
                "arbitration_notes": [],
                "contract": {"positive_negative_conflict_policy": "positive_precedence"},
            },
            source_evidence=[],
            selected_retrieval_result_ids=[],
            retrieval_trace_ids=[],
            graph_path_ids=[],
        )

        self.assertEqual(
            summary["decision_effect"],
            "positive_precedence_over_negative_trigger",
        )
        self.assertFalse(summary["requires_adjudication"])

    def test_missing_trigger_groups_and_not_evaluated_contract_are_traceable(self) -> None:
        self.assertEqual(
            missing_trigger_groups(
                {
                    "explicit_trigger_miss_evidence": [
                        {"missing_trigger_groups": [["road"], ["trail"]]}
                    ]
                }
            ),
            [["road"], ["trail"]],
        )
        self.assertEqual(
            trigger_arbitration_not_evaluated(
                "baseline authority does not require arbitration",
                arbitration_status="mandatory_baseline",
            ),
            {
                "arbitration_status": "mandatory_baseline",
                "positive_trigger_sufficient": False,
                "requires_adjudication": False,
                "decisive_trigger_groups": [],
                "weak_auxiliary_trigger_groups": [],
                "weak_only_trigger_groups": [],
                "missing_required_trigger_groups": [],
                "minimum_strong_trigger_groups": 0,
                "strong_trigger_group_count": 0,
                "arbitration_rationale": "baseline authority does not require arbitration",
                "arbitration_notes": [],
                "contract": {},
            },
        )


def _group_result(
    trigger_term: str,
    *,
    observed: int = 0,
    weak: int = 0,
    negative_context: int = 0,
) -> dict:
    counts = {}
    if observed:
        counts["observed"] = observed
    if weak:
        counts["weak_signal"] = weak
    if negative_context:
        counts["negative_context"] = negative_context
    return {
        "trigger_group": [trigger_term],
        "matched": True,
        "evidence_strength_counts": counts,
    }
