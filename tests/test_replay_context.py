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
            Path("source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate"),
        )
        self.assertEqual(context.source_set_id, "source-set-f70ea11e04ae3d53")

    def test_tracked_south_plateau_replay_context_uses_archived_current_promotion_catalog_surface(
        self,
    ) -> None:
        repo_root = Path(__file__).resolve().parents[1]

        context = load_replay_context(
            repo_root
            / "config"
            / "replay_contexts"
            / "region1-expansion-south-plateau-landscape-treatment.json"
        )

        self.assertEqual(
            context.catalog_dir,
            Path("source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate"),
        )
        self.assertEqual(context.source_set_id, "source-set-f70ea11e04ae3d53")
        self.assertEqual(
            context.package_path,
            Path("source_library/reviews/_intake/region1-expansion-south-plateau-landscape-treatment"),
        )

    def test_tracked_south_otter_replay_context_uses_narrowed_final_package_path(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]

        context = load_replay_context(
            repo_root
            / "config"
            / "replay_contexts"
            / "region1-example-custer-gallatin-south-otter-58396.json"
        )

        self.assertEqual(context.review_id, "region1-example-custer-gallatin-south-otter-58396")
        self.assertEqual(
            context.catalog_dir,
            Path("source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate"),
        )
        self.assertEqual(context.source_set_id, "source-set-f70ea11e04ae3d53")
        self.assertEqual(
            context.package_path,
            Path(
                "source_library/reviews/_intake/"
                "region1-example-custer-gallatin-south-otter-58396/"
                "Final EA and Decision Notice Documents"
            ),
        )

    def test_tracked_west_reservoir_replay_context_uses_migrated_f70_catalog_surface(
        self,
    ) -> None:
        repo_root = Path(__file__).resolve().parents[1]

        context = load_replay_context(
            repo_root / "config" / "replay_contexts" / "west-reservoir-67436.json"
        )

        self.assertEqual(context.review_id, "west-reservoir-67436")
        self.assertEqual(
            context.catalog_dir,
            Path("source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate"),
        )
        self.assertEqual(context.source_set_id, "source-set-f70ea11e04ae3d53")
        self.assertEqual(
            context.package_path,
            Path("source_library/reviews/west-reservoir-67436/package"),
        )

    def test_tracked_hlc_bonanza_replay_context_uses_current_f70_catalog_surface(
        self,
    ) -> None:
        repo_root = Path(__file__).resolve().parents[1]

        context = load_replay_context(
            repo_root
            / "config"
            / "replay_contexts"
            / "region1-example-helena-lewis-and-clark-bonanza-66532.json"
        )

        self.assertEqual(context.review_id, "region1-example-helena-lewis-and-clark-bonanza-66532")
        self.assertEqual(context.forest_unit_id, "helena-lewis-and-clark-nf")
        self.assertEqual(context.catalog_dir, Path("source_library/catalog"))
        self.assertEqual(context.source_set_id, "source-set-f70ea11e04ae3d53")
        self.assertEqual(
            context.package_path,
            Path(
                "source_library/reviews/_intake/"
                "region1-example-helena-lewis-and-clark-bonanza-66532"
            ),
        )

    def test_tracked_beaverhead_south_tobacco_roots_replay_context_uses_current_f70_catalog_surface(
        self,
    ) -> None:
        repo_root = Path(__file__).resolve().parents[1]

        context = load_replay_context(
            repo_root
            / "config"
            / "replay_contexts"
            / "region1-example-beaverhead-deerlodge-south-tobacco-roots-63754.json"
        )

        self.assertEqual(
            context.review_id,
            "region1-example-beaverhead-deerlodge-south-tobacco-roots-63754",
        )
        self.assertEqual(context.forest_unit_id, "beaverhead-deerlodge-nf")
        self.assertEqual(context.catalog_dir, Path("source_library/catalog"))
        self.assertEqual(context.source_set_id, "source-set-f70ea11e04ae3d53")
        self.assertEqual(
            context.package_path,
            Path(
                "source_library/reviews/_intake/"
                "region1-example-beaverhead-deerlodge-south-tobacco-roots-63754"
            ),
        )

    def test_tracked_idaho_panhandle_lacy_lemoosh_replay_context_uses_current_f70_catalog_surface(
        self,
    ) -> None:
        repo_root = Path(__file__).resolve().parents[1]

        context = load_replay_context(
            repo_root
            / "config"
            / "replay_contexts"
            / "region1-example-idaho-panhandle-lacy-lemoosh-60853.json"
        )

        self.assertEqual(
            context.review_id,
            "region1-example-idaho-panhandle-lacy-lemoosh-60853",
        )
        self.assertEqual(context.forest_unit_id, "idaho-panhandle-nfs")
        self.assertEqual(context.catalog_dir, Path("source_library/catalog"))
        self.assertEqual(context.source_set_id, "source-set-f70ea11e04ae3d53")
        self.assertEqual(
            context.package_path,
            Path(
                "source_library/reviews/_intake/"
                "region1-example-idaho-panhandle-lacy-lemoosh-60853"
            ),
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
