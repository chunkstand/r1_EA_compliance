from __future__ import annotations

import unittest

from usfs_r1_ea_sources.applicability_decision_forest_plan import forest_plan_component_result


class ApplicabilityDecisionForestPlanTests(unittest.TestCase):
    def test_forest_plan_component_result_accepts_matching_scope(self) -> None:
        result = forest_plan_component_result(
            candidate=_candidate(),
            package_nodes=_matching_package_nodes(),
            positive_match=_match(matched=True, matched_groups=[["Crazy Mountains Backcountry Area"]]),
            negative_match=_match(matched=False),
            coverage_boundary={"coverage_sufficient": True},
        )

        self.assertEqual(result["status"], "applicable")
        self.assertEqual(result["basis_type"], "forest_plan_component")
        self.assertEqual(
            result["basis"]["matched_package_values"],
            {
                "geography": ["geo-bridger-bangtail-crazy"],
                "management_area": ["mgmt-crazy-mountains-bca"],
                "overlay": ["overlay-inventoried-roadless"],
            },
        )

    def test_forest_plan_component_result_keeps_negative_scope_not_applicable(self) -> None:
        result = forest_plan_component_result(
            candidate=_candidate(),
            package_nodes=_matching_package_nodes(),
            positive_match=_match(matched=True, matched_groups=[["Crazy Mountains Backcountry Area"]]),
            negative_match=_match(matched=True, matched_groups=[["outside project area"]]),
            coverage_boundary={"coverage_sufficient": True},
        )

        self.assertEqual(result["status"], "not_applicable")
        self.assertEqual(result["basis_type"], "negative_package_evidence")
        self.assertEqual(
            result["basis"]["matched_negative_trigger_groups"],
            [["outside project area"]],
        )

    def test_forest_plan_component_result_records_weak_trigger_as_not_applicable(self) -> None:
        result = forest_plan_component_result(
            candidate=_candidate(),
            package_nodes=_matching_package_nodes(),
            positive_match=_match(
                matched=True,
                matched_groups=[["Crazy Mountains Backcountry Area"]],
                requires_adjudication=True,
                adjudication_notes=["weak package signal"],
            ),
            negative_match=_match(matched=False),
            coverage_boundary={"coverage_sufficient": True},
        )

        self.assertEqual(result["status"], "not_applicable")
        self.assertEqual(result["basis_type"], "forest_plan_component")
        self.assertEqual(result["contradiction_notes"], [])
        self.assertEqual(
            result["basis"]["weak_trigger_groups"],
            [["Crazy Mountains Backcountry Area"]],
        )
        self.assertEqual(
            result["basis"]["missing_trigger_groups"],
            [["Crazy Mountains Backcountry Area"]],
        )
        self.assertEqual(result["basis"]["weak_trigger_notes"], ["weak package signal"])

    def test_forest_plan_component_result_keeps_strong_trigger_with_weak_auxiliary(self) -> None:
        result = forest_plan_component_result(
            candidate=_candidate(),
            package_nodes=_matching_package_nodes(),
            positive_match=_match(
                matched=True,
                matched_groups=[
                    ["Crazy Mountains Backcountry Area"],
                    ["Inventoried Roadless Area"],
                ],
                requires_adjudication=True,
                adjudication_notes=["weak auxiliary signal"],
            ),
            negative_match=_match(matched=False),
            coverage_boundary={"coverage_sufficient": True},
            trigger_arbitration={
                "positive_trigger_sufficient": True,
                "arbitration_status": "strong_positive_with_weak_auxiliary",
            },
        )

        self.assertEqual(result["status"], "applicable")
        self.assertEqual(result["basis_type"], "forest_plan_component")
        self.assertEqual(result["contradiction_notes"], [])

    def test_forest_plan_component_result_records_scope_miss_with_insufficient_coverage(self) -> None:
        result = forest_plan_component_result(
            candidate=_candidate(),
            package_nodes=[
                {
                    "node_type": "geography",
                    "normalized_value": "geo-absent",
                    "confidence_class": "observed",
                }
            ],
            positive_match=_match(matched=False),
            negative_match=_match(matched=False),
            coverage_boundary={"coverage_sufficient": False},
        )

        self.assertEqual(result["status"], "unresolved")
        self.assertEqual(result["basis_type"], "forest_plan_profile_resolution")
        self.assertIn("geography:geo-bridger-bangtail-crazy", result["missing_evidence"])
        self.assertIn(
            "sufficient forest-plan search coverage",
            result["missing_evidence"],
        )


def _candidate() -> dict:
    return {
        "positive_trigger_groups": [["Crazy Mountains Backcountry Area"]],
        "forest_plan": {
            "geographic_area_ids": ["geo-bridger-bangtail-crazy"],
            "management_area_ids": ["mgmt-crazy-mountains-bca"],
            "overlay_ids": ["overlay-inventoried-roadless"],
        },
    }


def _matching_package_nodes() -> list[dict]:
    return [
        {
            "node_type": "geography",
            "normalized_value": "geo-bridger-bangtail-crazy",
            "confidence_class": "observed",
        },
        {
            "node_type": "management_area",
            "normalized_value": "mgmt-crazy-mountains-bca",
            "confidence_class": "observed",
        },
        {
            "node_type": "overlay",
            "normalized_value": "overlay-inventoried-roadless",
            "confidence_class": "observed",
        },
    ]


def _match(
    *,
    matched: bool,
    matched_groups: list[list[str]] | None = None,
    requires_adjudication: bool = False,
    adjudication_notes: list[str] | None = None,
) -> dict:
    return {
        "matched": matched,
        "matched_groups": matched_groups or [],
        "requires_adjudication": requires_adjudication,
        "adjudication_notes": adjudication_notes or [],
    }
