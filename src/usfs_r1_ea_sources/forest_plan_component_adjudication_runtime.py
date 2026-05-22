from __future__ import annotations

from pathlib import Path

from .forest_plan_component_adjudication_common import _adjudication_items
from .forest_plan_component_adjudication_common import _components_by_id
from .forest_plan_component_adjudication_common import _findings_by_id
from .forest_plan_component_adjudication_common import _load_adjudication
from .forest_plan_component_adjudication_common import _load_review_artifacts
from .forest_plan_component_adjudication_common import _queue_items
from .forest_plan_component_adjudication_common import _resolve_review_dir
from .forest_plan_component_adjudication_common import _utc_now
from .forest_plan_component_adjudication_common import _write_json
from .forest_plan_component_adjudication_common import _write_text
from .forest_plan_component_adjudication_eval import _check_adjudication_expectations_match
from .forest_plan_component_adjudication_eval import _check_adjudication_identity
from .forest_plan_component_adjudication_eval import _check_adjudication_items_complete
from .forest_plan_component_adjudication_eval import _check_adjudication_items_cover_queue
from .forest_plan_component_adjudication_eval import _eval_summary
from .forest_plan_component_adjudication_eval import _item_results
from .forest_plan_component_adjudication_models import ALLOWED_DISPOSITIONS
from .forest_plan_component_adjudication_models import (
    FOREST_PLAN_COMPONENT_ADJUDICATION_EVAL_SCHEMA_VERSION,
)
from .forest_plan_component_adjudication_models import (
    FOREST_PLAN_COMPONENT_ADJUDICATION_SCHEMA_VERSION,
)
from .forest_plan_component_adjudication_models import (
    ForestPlanComponentAdjudicationEvalResult,
)
from .forest_plan_component_adjudication_models import (
    ForestPlanComponentAdjudicationTemplateResult,
)
from .forest_plan_component_adjudication_models import RESOLVED_DISPOSITIONS
from .forest_plan_component_adjudication_template import _template_item
from .forest_plan_component_adjudication_template import _template_markdown
from .forest_plan_component_adjudication_template import _template_summary

def write_forest_plan_component_adjudication_template(
    *,
    output_dir: Path,
    review_id: str | None = None,
    review_dir: Path | None = None,
    output_path: Path | None = None,
) -> ForestPlanComponentAdjudicationTemplateResult:
    """Write a reviewer-fillable adjudication template for open component items."""

    resolved_review_dir = _resolve_review_dir(
        output_dir=output_dir,
        review_id=review_id,
        review_dir=review_dir,
    )
    artifacts = _load_review_artifacts(resolved_review_dir)
    output_path = Path(output_path) if output_path else (
        resolved_review_dir / "forest_plan_component_adjudication_template.json"
    )
    markdown_path = output_path.with_suffix(".md")
    queue_items = _queue_items(artifacts["queue"])
    findings_by_id = _findings_by_id(artifacts["findings_report"])
    components_by_id = _components_by_id(artifacts["findings_report"])
    items = [
        _template_item(
            item=queue_item,
            finding=findings_by_id.get(str(queue_item.get("finding_id") or "")),
            component=components_by_id.get(str(queue_item.get("component_id") or "")),
        )
        for queue_item in queue_items
    ]
    summary = _template_summary(
        review_dir=resolved_review_dir,
        output_path=output_path,
        markdown_path=markdown_path,
        findings_report=artifacts["findings_report"],
        queue=artifacts["queue"],
        items=items,
    )
    template = {
        "schema_version": FOREST_PLAN_COMPONENT_ADJUDICATION_SCHEMA_VERSION,
        "adjudication_id": f"{summary['review_id']}-component-adjudication",
        "title": "Forest Plan Component Adjudication",
        "created_at": _utc_now(),
        "review_id": summary["review_id"],
        "source_set_id": summary["source_set_id"],
        "component_findings_path": str(resolved_review_dir / "forest_plan_component_findings.json"),
        "reviewer_resolution_queue_path": str(
            resolved_review_dir / "forest_plan_reviewer_resolution_queue.json"
        ),
        "adjudication": {
            "status": "pending",
            "method": "",
            "adjudicated_by": [],
            "adjudicated_at": "",
            "notes": "",
        },
        "allowed_dispositions": sorted(ALLOWED_DISPOSITIONS),
        "resolved_dispositions": sorted(RESOLVED_DISPOSITIONS),
        "summary": summary,
        "items": items,
    }
    _write_json(output_path, template)
    _write_text(markdown_path, _template_markdown(template))
    return ForestPlanComponentAdjudicationTemplateResult(
        review_dir=resolved_review_dir,
        output_path=output_path,
        markdown_path=markdown_path,
        summary=summary,
    )

def run_forest_plan_component_adjudication_eval(
    *,
    output_dir: Path,
    review_id: str | None = None,
    review_dir: Path | None = None,
    adjudication_file: Path | None = None,
    output_path: Path | None = None,
) -> ForestPlanComponentAdjudicationEvalResult:
    """Evaluate completed component adjudications against current review artifacts."""

    resolved_review_dir = _resolve_review_dir(
        output_dir=output_dir,
        review_id=review_id,
        review_dir=review_dir,
    )
    artifacts = _load_review_artifacts(resolved_review_dir)
    adjudication_file = Path(adjudication_file) if adjudication_file else (
        resolved_review_dir / "forest_plan_component_adjudication.json"
    )
    output_path = Path(output_path) if output_path else (
        resolved_review_dir / "forest_plan_component_adjudication_eval.json"
    )
    adjudication = _load_adjudication(adjudication_file)
    queue_items = _queue_items(artifacts["queue"])
    findings_by_id = _findings_by_id(artifacts["findings_report"])
    adjudication_items = _adjudication_items(adjudication)
    item_results = _item_results(
        queue_items=queue_items,
        findings_by_id=findings_by_id,
        adjudication_items=adjudication_items,
    )
    checks = [
        _check_adjudication_identity(
            adjudication=adjudication,
            adjudication_file=adjudication_file,
            findings_report=artifacts["findings_report"],
        ),
        _check_adjudication_items_cover_queue(
            queue_items=queue_items,
            adjudication_items=adjudication_items,
        ),
        _check_adjudication_items_complete(item_results),
        _check_adjudication_expectations_match(item_results),
    ]
    summary = _eval_summary(
        review_dir=resolved_review_dir,
        adjudication_file=adjudication_file,
        output_path=output_path,
        findings_report=artifacts["findings_report"],
        queue_items=queue_items,
        item_results=item_results,
        checks=checks,
    )
    report = {
        "schema_version": FOREST_PLAN_COMPONENT_ADJUDICATION_EVAL_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "review_id": summary["review_id"],
        "source_set_id": summary["source_set_id"],
        "adjudication_file": str(adjudication_file),
        "review_dir": str(resolved_review_dir),
        "summary": summary,
        "checks": checks,
        "item_results": item_results,
    }
    _write_json(output_path, report)
    return ForestPlanComponentAdjudicationEvalResult(
        review_dir=resolved_review_dir,
        adjudication_file=adjudication_file,
        output_path=output_path,
        summary=summary,
    )
