from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src" / "usfs_r1_ea_sources"

FORBIDDEN_RUNTIME_EXAMPLE_MARKERS = [
    "west-reservoir-67436",
    "West Reservoir",
    "mud-creek",
    "Mud Creek",
    "region1-example-bitterroot-mud-creek-55744",
    "tylers-kitchen",
    "Tyler's Kitchen",
    "HLC Bonanza",
    "hlc-bonanza",
]


def test_runtime_modules_do_not_hardcode_specific_ea_examples() -> None:
    failures: list[str] = []
    for path in sorted(SRC_ROOT.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        for marker in FORBIDDEN_RUNTIME_EXAMPLE_MARKERS:
            if marker in text:
                failures.append(f"{path.relative_to(REPO_ROOT)} contains {marker!r}")

    assert failures == []
