from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest

from usfs_r1_ea_sources.config import load_config
from usfs_r1_ea_sources.download import DownloadFetchResult, run_download
from usfs_r1_ea_sources.dry_run import run_dry_run
from usfs_r1_ea_sources.overrides import load_url_overrides
from usfs_r1_ea_sources.workbook import load_canonical_sources


ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = ROOT / "usfs_region1_ea_document_checklist_current_2026.xlsx"
BASE_CONFIG = ROOT / "config" / "downloader.toml"


class OverrideTests(unittest.TestCase):
    def test_load_url_overrides_requires_reason(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "overrides.toml"
            path.write_text(
                """
[[overrides]]
source_record_id = "R1EA-001"
override_url = "https://example.test/repaired"
""",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "missing reason"):
                load_url_overrides(path)

    def test_override_changes_effective_url_and_preserves_workbook_url(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = _write_config_with_override(tmp)
            config = load_config(config_path)
            sources = load_canonical_sources(WORKBOOK, config.workbook)
            source = next(source for source in sources if source.source_record_id == "R1EA-001")

            self.assertEqual(
                source.original_url,
                "https://uscode.house.gov/view.xhtml?path=/prelim@title42/chapter55&edition=prelim",
            )
            self.assertEqual(source.effective_url, "https://example.test/repaired-source")
            self.assertEqual(source.normalized_url, "https://example.test/repaired-source")
            self.assertEqual(source.metadata["override_url"], "https://example.test/repaired-source")

    def test_dry_run_manifest_records_effective_and_original_url(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = load_config(_write_config_with_override(tmp))
            result = run_dry_run(
                workbook_path=WORKBOOK,
                output_dir=Path(tmp) / "source_library",
                config=config,
                run_id="override-dry-run",
                id_filter="R1EA-001",
            )
            record = json.loads(result.manifest_path.read_text(encoding="utf-8").splitlines()[0])

            self.assertEqual(record["original_url"], "https://uscode.house.gov/view.xhtml?path=/prelim@title42/chapter55&edition=prelim")
            self.assertEqual(record["effective_url"], "https://example.test/repaired-source")
            self.assertEqual(record["normalized_url"], "https://example.test/repaired-source")
            self.assertEqual(record["metadata"]["override_reason"], "Unit test repair")

    def test_download_fetches_effective_url_not_workbook_url(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = load_config(_write_config_with_override(tmp))
            calls: list[str] = []

            def fake_fetcher(url, network, validation):  # noqa: ANN001
                calls.append(url)
                body = b"<html><body>override content</body></html>" + b" " * 128
                return DownloadFetchResult(
                    status="downloaded",
                    http_status=200,
                    final_url=url,
                    redirect_chain=[],
                    content_type="text/html",
                    content_length=len(body),
                    body=body,
                    attempt_count=1,
                    failure=None,
                    validation={"mode": "download", "passed": True, "reason": None},
                )

            result = run_download(
                workbook_path=WORKBOOK,
                output_dir=Path(tmp) / "source_library",
                config=config,
                run_id="override-download",
                id_filter="R1EA-001",
                fetcher=fake_fetcher,
                sleep_fn=lambda _: None,
            )
            record = json.loads(result.manifest_path.read_text(encoding="utf-8").splitlines()[0])

            self.assertEqual(calls, ["https://example.test/repaired-source"])
            self.assertEqual(record["original_url"], "https://uscode.house.gov/view.xhtml?path=/prelim@title42/chapter55&edition=prelim")
            self.assertEqual(record["effective_url"], "https://example.test/repaired-source")
            self.assertEqual(record["final_url"], "https://example.test/repaired-source")


def _write_config_with_override(tmp: str) -> Path:
    tmp_path = Path(tmp)
    override_path = tmp_path / "overrides.toml"
    override_path.write_text(
        """
[[overrides]]
source_record_id = "R1EA-001"
override_url = "https://example.test/repaired-source"
reason = "Unit test repair"
""",
        encoding="utf-8",
    )
    config_text = BASE_CONFIG.read_text(encoding="utf-8")
    config_text = config_text.replace(
        'overrides_path = "config/url_overrides.toml"',
        f'overrides_path = "{override_path}"',
    )
    config_path = tmp_path / "downloader.toml"
    config_path.write_text(config_text, encoding="utf-8")
    return config_path


if __name__ == "__main__":
    unittest.main()
