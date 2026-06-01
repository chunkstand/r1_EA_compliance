from __future__ import annotations

import ast
import json
import re
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPO_ROOT / "src" / "usfs_r1_ea_sources"
CODE_ROOTS = (
    REPO_ROOT / "src",
    REPO_ROOT / "tests",
    REPO_ROOT / "viewer",
)
CODE_GLOBS = ("*.py", "*.js")
MAX_REVIEWABLE_LINES = 800
MAX_ALLOWED_OVERSIZED_FILES = 15
MAX_ALLOWED_FAN_OUT = 20
MAX_README_LINES = 220
ALLOWED_HIGH_FAN_OUT_MODULES: set[str] = set()
REPLAY_CONTEXT_DIR = REPO_ROOT / "config" / "replay_contexts"
LARGE_FILE_INVENTORY_PATH = REPO_ROOT / "config" / "architecture_large_file_inventory_v1.json"
CURRENT_ROUTING_PATH = REPO_ROOT / "docs" / "CURRENT_ROUTING.md"
MAX_CURRENT_ROUTING_LINES = 40
ARCHITECTURE_GOVERNANCE_PLAN_PATH = (
    REPO_ROOT / "docs" / "ARCHITECTURE_GOVERNANCE_REBASELINE_MILESTONE_PLAN.md"
)
OVERALL_ARCHITECTURE_PLAN_PATH = REPO_ROOT / "docs" / "OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md"
UNDER_800_PLAN_PATH = REPO_ROOT / "docs" / "UNDER_800_HOTSPOT_REDUCTION_MILESTONE_PLAN.md"
README_PATH = REPO_ROOT / "README.md"
CURRENT_SYSTEM_STATE_PATH = REPO_ROOT / "docs" / "CURRENT_SYSTEM_STATE.md"
SESSION_HANDOFF_PATH = REPO_ROOT / "docs" / "SESSION_HANDOFF.md"
FULL_CANONICAL_GOLD_PLAN_PATH = (
    REPO_ROOT / "docs" / "FULL_CANONICAL_COMPLIANCE_GOLD_REBASELINE_MILESTONE_PLAN.md"
)
README_VOLATILE_MARKERS = (
    "Current routed state on",
    "Canonical source-register refoundation status on",
    "Historical local import baseline on",
    "current_promotion_ready",
    "reviewer_ready=true",
    "candidate_authority_count",
    "failure_category_counts=",
)
README_LIVE_SOURCE_SET_PATTERN = re.compile(r"source-set-[0-9a-f]{16}")


def test_large_file_count_does_not_grow() -> None:
    oversized = _oversized_code_paths()

    assert len(oversized) == MAX_ALLOWED_OVERSIZED_FILES


def test_large_file_inventory_matches_follow_on_queue() -> None:
    inventory = _large_file_inventory()
    families = inventory["families"]
    owner_counts = {"source": 0, "test": 0}

    expected_paths: set[Path] = set()
    expected_count = 0

    assert inventory["plan_path"] == "docs/ARCHITECTURE_GOVERNANCE_REBASELINE_MILESTONE_PLAN.md"
    assert inventory["plan_status"] == "resolved_rebaseline_backlog_routed"
    historical = inventory["historical_closeout"]
    assert historical["plan_path"] == "docs/UNDER_800_HOTSPOT_REDUCTION_MILESTONE_PLAN.md"
    assert historical["status"] == "resolved_historical_closeout"
    assert historical["closeout_commit"] == "a6c5459"

    for family in families:
        owner_kind = family["owner_kind"]
        assert owner_kind in owner_counts, family["name"]
        owner_counts[owner_kind] += 1
        assert family["required_tests"], family["name"]
        files = family["files"]
        assert files, family["name"]

        for entry in files:
            path = Path(entry["path"])
            expected_paths.add(path)
            expected_count += 1

            actual_line_count = _line_count(REPO_ROOT / path)
            assert actual_line_count == entry["line_count"], path
            assert actual_line_count > MAX_REVIEWABLE_LINES, path

    assert families
    assert owner_counts == {"source": 9, "test": 6}
    assert expected_count == MAX_ALLOWED_OVERSIZED_FILES
    assert _oversized_code_paths() == expected_paths


def test_no_new_high_fan_out_modules() -> None:
    over_limit = {
        module: len(imports)
        for module, imports in _source_imports().items()
        if len(imports) > MAX_ALLOWED_FAN_OUT
    }

    assert set(over_limit).issubset(ALLOWED_HIGH_FAN_OUT_MODULES)


def test_architecture_doc_path_stays_canonical() -> None:
    result = subprocess.run(
        ["git", "ls-files", "docs/ARCHITECTURE.md", "docs/architecture.md"],
        check=True,
        capture_output=True,
        cwd=REPO_ROOT,
        text=True,
    )
    tracked_paths = [line.strip() for line in result.stdout.splitlines() if line.strip()]

    assert tracked_paths == ["docs/ARCHITECTURE.md"]
    architecture_doc = REPO_ROOT / "docs" / "ARCHITECTURE.md"
    assert architecture_doc.exists()
    assert "Canonical architecture doc path: `docs/ARCHITECTURE.md`" in architecture_doc.read_text(
        encoding="utf-8"
    )


def test_replay_context_package_paths_stay_repo_relative() -> None:
    for config_path in sorted(REPLAY_CONTEXT_DIR.glob("*.json")):
        payload = json.loads(config_path.read_text(encoding="utf-8"))
        package_path = payload.get("package_path")
        if not package_path:
            continue
        declared_path = Path(str(package_path))
        assert not declared_path.is_absolute(), config_path
        assert ".." not in declared_path.parts, config_path


def test_current_routing_doc_stays_short_and_linked() -> None:
    assert CURRENT_ROUTING_PATH.exists()

    current_routing = CURRENT_ROUTING_PATH.read_text(encoding="utf-8")
    assert len(current_routing.splitlines()) <= MAX_CURRENT_ROUTING_LINES
    assert "## Live Facts" not in current_routing
    assert "candidate_authority_count" not in current_routing
    assert "reviewer_ready_slot_count" not in current_routing
    assert "source-set-" not in current_routing
    assert "docs/CURRENT_SYSTEM_STATE.md" in current_routing
    assert "docs/SESSION_HANDOFF.md" in current_routing
    assert "docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md" in current_routing
    assert "docs/ARCHITECTURE_GOVERNANCE_REBASELINE_MILESTONE_PLAN.md" in current_routing

    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    start_here = (REPO_ROOT / "docs" / "AGENT_START_HERE.md").read_text(encoding="utf-8")
    assert "docs/CURRENT_ROUTING.md" in readme
    assert "docs/CURRENT_ROUTING.md" in start_here


def test_readme_routes_to_current_state_owners() -> None:
    readme = README_PATH.read_text(encoding="utf-8")

    assert len(readme.splitlines()) <= MAX_README_LINES
    assert "docs/CURRENT_ROUTING.md" in readme
    assert "docs/CURRENT_SYSTEM_STATE.md" in readme
    assert "docs/SESSION_HANDOFF.md" in readme
    assert f"`{MAX_ALLOWED_OVERSIZED_FILES}` code files above `800`" not in readme
    for marker in README_VOLATILE_MARKERS:
        assert marker not in readme, marker
    assert README_LIVE_SOURCE_SET_PATTERN.search(readme) is None


def test_historical_under_800_closeout_and_rebaseline_packet_are_discoverable() -> None:
    under_800_plan = UNDER_800_PLAN_PATH.read_text(encoding="utf-8")
    architecture_plan = ARCHITECTURE_GOVERNANCE_PLAN_PATH.read_text(encoding="utf-8")
    current_system_state = CURRENT_SYSTEM_STATE_PATH.read_text(encoding="utf-8")
    handoff = SESSION_HANDOFF_PATH.read_text(encoding="utf-8")

    assert "config/architecture_large_file_inventory_v1.json" in under_800_plan
    assert "docs/UNDER_800_HOTSPOT_REDUCTION_MILESTONE_PLAN.md" in architecture_plan
    assert "docs/ARCHITECTURE_GOVERNANCE_REBASELINE_MILESTONE_PLAN.md" in current_system_state
    assert "docs/ARCHITECTURE_GOVERNANCE_REBASELINE_MILESTONE_PLAN.md" in handoff
    assert "historical truth" in handoff


def test_overall_architecture_plan_closeout_stays_current() -> None:
    plan = OVERALL_ARCHITECTURE_PLAN_PATH.read_text(encoding="utf-8")

    current_brittle = _section_text(plan, "### Current brittle places", "## Goal")
    assert "large-file count is now `24`" in current_brittle
    assert "code files over `800` lines" in current_brittle
    assert "`50` code files over `800` lines" not in current_brittle
    assert "`1418` lines" not in current_brittle
    assert "typed_blocked" in current_brittle

    weak_points = _section_text(plan, "## Weak-Point Register", "## Large-File Inventory Over 800 Lines")
    assert "reduced from the Milestone 0 baseline of `57` to `24` code files over `800` lines" in weak_points
    assert "no local module exceeds the `20`-import fan-out gate" in weak_points
    assert "| Large-file concentration | `54` code files over `800` lines |" not in weak_points

    acceptance = _section_text(plan, "## Acceptance Criteria", "## Stop Conditions")
    assert "live closeout count of `24`" in acceptance
    assert "current baseline of `57` to `45` or" not in acceptance

    sequence_52 = _section_text(
        plan,
        "Progress after Sequence 52 on 2026-05-21:",
        "Remaining issue after closeout:",
    )
    assert "PYTHONPATH=src python -m usfs_r1_ea_sources compliance-gold-eval" in sequence_52
    assert "PYTHONPATH=src python -m usfs_r1_ea_sources real-package-review-coverage-eval" in sequence_52
    assert "git diff --check" in sequence_52


def test_live_architecture_state_is_owned_by_current_state_and_handoff() -> None:
    current_system_state = CURRENT_SYSTEM_STATE_PATH.read_text(encoding="utf-8")
    handoff = SESSION_HANDOFF_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    current_routing = CURRENT_ROUTING_PATH.read_text(encoding="utf-8")
    expected_count_marker = f"`{MAX_ALLOWED_OVERSIZED_FILES}` code files above `800`"

    for name, text in {
        "Current System State": current_system_state,
        "Session Handoff": handoff,
    }.items():
        assert "docs/ARCHITECTURE_GOVERNANCE_REBASELINE_MILESTONE_PLAN.md" in text, name
        assert "config/architecture_large_file_inventory_v1.json" in text, name
        assert expected_count_marker in text, name

    for name, text in {
        "README": readme,
        "Current Routing": current_routing,
    }.items():
        assert expected_count_marker not in text, name


def test_gold_state_markers_live_only_in_owner_docs() -> None:
    owner_docs = {
        "Current System State": CURRENT_SYSTEM_STATE_PATH.read_text(encoding="utf-8"),
        "Session Handoff": SESSION_HANDOFF_PATH.read_text(encoding="utf-8"),
    }
    non_owner_docs = {
        "README": README_PATH.read_text(encoding="utf-8"),
        "Current Routing": CURRENT_ROUTING_PATH.read_text(encoding="utf-8"),
    }
    markers = (
        "five still-unmapped live authorities",
        "zero-link structural surface",
        "generated diagnostic",
    )

    for name, text in owner_docs.items():
        for marker in markers:
            assert marker in text, f"{name}: {marker}"

    for name, text in non_owner_docs.items():
        for marker in markers:
            assert marker not in text, f"{name}: {marker}"


def _code_paths() -> list[Path]:
    paths: list[Path] = []
    for root in CODE_ROOTS:
        if not root.exists():
            continue
        for pattern in CODE_GLOBS:
            paths.extend(sorted(root.rglob(pattern)))
    return paths


def _oversized_code_paths() -> set[Path]:
    return {
        path.relative_to(REPO_ROOT)
        for path in _code_paths()
        if _line_count(path) > MAX_REVIEWABLE_LINES
    }


def _line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def _large_file_inventory() -> dict[str, object]:
    return json.loads(LARGE_FILE_INVENTORY_PATH.read_text(encoding="utf-8"))


def _source_modules() -> set[str]:
    return {path.stem for path in SOURCE_ROOT.glob("*.py")}


def _source_imports() -> dict[str, set[str]]:
    modules = _source_modules()
    imports: dict[str, set[str]] = {module: set() for module in modules}
    for module in modules:
        path = SOURCE_ROOT / f"{module}.py"
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                imports[module].update(_relative_import_targets(node, modules))
            elif isinstance(node, ast.Import):
                imports[module].update(_absolute_import_targets(node, modules))
    return imports


def _relative_import_targets(node: ast.ImportFrom, modules: set[str]) -> set[str]:
    if node.level != 1:
        return set()
    if node.module:
        target = node.module.split(".", 1)[0]
        return {target} if target in modules else set()
    return {alias.name.split(".", 1)[0] for alias in node.names if alias.name in modules}


def _absolute_import_targets(node: ast.Import, modules: set[str]) -> set[str]:
    package_prefix = "usfs_r1_ea_sources."
    targets = set()
    for alias in node.names:
        if alias.name.startswith(package_prefix):
            target = alias.name[len(package_prefix) :].split(".", 1)[0]
            if target in modules:
                targets.add(target)
    return targets


def _section_text(text: str, start_marker: str, end_marker: str) -> str:
    start = text.index(start_marker)
    end = text.index(end_marker, start)
    return text[start:end]
