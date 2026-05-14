from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest

from usfs_r1_ea_sources.replay_context import ReplayContextError
from usfs_r1_ea_sources.replay_context import load_replay_context
from usfs_r1_ea_sources.replay_context import tracked_replay_context_path


class ReplayContextTests(unittest.TestCase):
    def test_tracked_ecid_replay_context_uses_archived_current_promotion_catalog_surface(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]

        context = load_replay_context(
            repo_root / "config" / "replay_contexts" / "v1-cg-ecid-compliance-review.json"
        )

        self.assertEqual(
            context.catalog_dir,
            Path("source_library/runs/corpus-update-2026-05-01-cg-support-batches/catalog_gate"),
        )

    def test_load_replay_context_derives_child_catalog_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            config_path = _write_replay_context(
                repo_root,
                review_id="tracked-replay-review",
                source_set_id="source-set-test",
                catalog_dir="source_library/runs/archived_catalog",
            )

            context = load_replay_context(config_path)

            self.assertEqual(context.review_id, "tracked-replay-review")
            self.assertEqual(context.source_set_id, "source-set-test")
            self.assertEqual(context.catalog_dir, Path("source_library/runs/archived_catalog"))
            self.assertEqual(
                context.resolved_catalog_dir,
                (repo_root / "source_library" / "runs" / "archived_catalog").resolve(),
            )
            self.assertEqual(
                context.resolved_source_catalog_path,
                (
                    repo_root
                    / "source_library"
                    / "runs"
                    / "archived_catalog"
                    / "source_catalog.jsonl"
                ).resolve(),
            )
            self.assertEqual(
                context.resolved_source_set_manifest_path,
                (
                    repo_root
                    / "source_library"
                    / "runs"
                    / "archived_catalog"
                    / "source_set_manifest.json"
                ).resolve(),
            )
            self.assertEqual(
                context.resolved_catalog_sqlite_path,
                (
                    repo_root
                    / "source_library"
                    / "runs"
                    / "archived_catalog"
                    / "review_sources.sqlite"
                ).resolve(),
            )

    def test_load_replay_context_rejects_mismatched_child_catalog_echo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            config_path = _write_replay_context(
                repo_root,
                review_id="tracked-replay-review",
                source_set_id="source-set-test",
                catalog_dir="source_library/runs/archived_catalog",
                extra_fields={
                    "source_catalog_path": "source_library/catalog/source_catalog.jsonl",
                },
            )

            with self.assertRaises(ReplayContextError):
                load_replay_context(config_path)

    def test_tracked_replay_context_path_uses_output_dir_parent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            output_dir = repo_root / "source_library"

            path = tracked_replay_context_path(output_dir, "tracked-replay-review")

            self.assertEqual(
                path,
                repo_root / "config" / "replay_contexts" / "tracked-replay-review.json",
            )


def _write_replay_context(
    repo_root: Path,
    *,
    review_id: str,
    source_set_id: str,
    catalog_dir: str,
    extra_fields: dict | None = None,
) -> Path:
    path = repo_root / "config" / "replay_contexts" / f"{review_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "review_id": review_id,
        "source_set_id": source_set_id,
        "catalog_dir": catalog_dir,
    }
    if extra_fields:
        payload.update(extra_fields)
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return path
