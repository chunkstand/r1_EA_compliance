from __future__ import annotations


def _markdown_report(summary: dict[str, object]) -> str:
    full_canonical_source_set_id = summary.get("full_canonical_source_set_id") or "None"
    lines = [
        "# Promotion Suite Report",
        "",
        f"- Suite: `{summary['suite_id']}`",
        f"- Source set: `{summary['source_set_id']}`",
        f"- Full canonical source set: `{full_canonical_source_set_id}`",
        f"- Rule pack: `{summary['rule_pack_id']}` `{summary['rule_pack_version']}`",
        f"- Current promotion ready: `{summary['current_promotion_ready']}`",
        f"- Full canonical corpus ready: `{summary['full_canonical_corpus_ready']}`",
        f"- Expansion ready: `{summary['expansion_ready']}`",
        f"- Promotion ready: `{summary['promotion_ready']}`",
        f"- Strict expansion: `{summary['strict_expansion']}`",
        f"- Failure categories: `{summary['failure_category_counts']}`",
        f"- Full canonical failure categories: `{summary['full_canonical_failure_category_counts']}`",
        f"- Expansion failure categories: `{summary['expansion_failure_category_counts']}`",
        f"- Open expansion slots: `{summary['open_expansion_slot_count']}`",
        "",
        "## Review Cases",
        "",
        "| Case | Review ID | Ready | Failed Categories |",
        "| --- | --- | --- | --- |",
    ]
    for case in summary["review_cases"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    _md_cell(case["id"]),
                    _md_cell(case["review_id"]),
                    _md_cell(case["promotion_ready"]),
                    _md_cell(", ".join(case["failure_categories"]) or "None"),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Suite Results",
            "",
            "| Result | Passed | Required | Failed Categories |",
            "| --- | --- | --- | --- |",
        ]
    )
    for result in summary["suite_results"]:
        lines.append(_result_markdown_row(result))
    lines.extend(
        [
            "",
            "## Expansion Slots",
            "",
            "| Slot | Status | Ready | Review ID | Package Path | Failed Categories | Next Action |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for slot in summary["expansion_slots"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    _md_cell(slot["id"]),
                    _md_cell(slot.get("status")),
                    _md_cell(slot["ready"]),
                    _md_cell(slot.get("review_id") or ""),
                    _md_cell(slot.get("package_path") or ""),
                    _md_cell(", ".join(slot.get("failure_categories") or []) or "None"),
                    _md_cell(slot.get("next_action") or ""),
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def _result_markdown_row(result: dict[str, object]) -> str:
    return (
        "| "
        + " | ".join(
            [
                _md_cell(result["id"]),
                _md_cell(result["passed"]),
                _md_cell(result["required_for_current_promotion"]),
                _md_cell(", ".join(result["failure_categories"]) or "None"),
            ]
        )
        + " |"
    )


def _md_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()
