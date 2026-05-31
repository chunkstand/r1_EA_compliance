from __future__ import annotations

from pathlib import Path
import tempfile

from usfs_r1_ea_sources.box_folder_intake import build_box_folder_inventory
from usfs_r1_ea_sources.box_folder_intake import download_box_folder_inventory
from usfs_r1_ea_sources.box_folder_intake import _FetchedBoxFolderPage
from usfs_r1_ea_sources.config import NetworkConfig


NETWORK = NetworkConfig(
    user_agent="test-agent",
    connect_timeout_seconds=1.0,
    read_timeout_seconds=1.0,
    max_attempts=1,
    global_concurrency=1,
    default_host_concurrency=1,
    default_host_delay_seconds=0.0,
    hosts={},
)


def test_build_box_folder_inventory_tracks_folder_pages_and_relative_paths() -> None:
    pages = {
        (100, 1): _FetchedBoxFolderPage(
            shared_name="shared-name",
            folder_id=100,
            folder_name="Dead Laundry (57827)",
            folder_url="https://usfs-public.app.box.com/v/PinyonPublic/folder/100",
            page_count=1,
            page_number=1,
            items=[
                {"id": 200, "type": "folder", "name": "Analysis", "typedID": "d_200"},
                {
                    "id": 900,
                    "type": "file",
                    "name": "Readme.pdf",
                    "typedID": "f_900",
                    "itemSize": 11,
                    "extension": "pdf",
                    "created": 1,
                    "contentUpdated": 2,
                },
            ],
        ),
        (200, 1): _FetchedBoxFolderPage(
            shared_name="shared-name",
            folder_id=200,
            folder_name="Analysis",
            folder_url="https://usfs-public.app.box.com/v/PinyonPublic/folder/200",
            page_count=2,
            page_number=1,
            items=[
                {"id": 300, "type": "folder", "name": "Reports", "typedID": "d_300"},
                {
                    "id": 901,
                    "type": "file",
                    "name": "Final EA.pdf",
                    "typedID": "f_901",
                    "itemSize": 21,
                    "extension": "pdf",
                    "created": 3,
                    "contentUpdated": 4,
                },
            ],
        ),
        (200, 2): _FetchedBoxFolderPage(
            shared_name="shared-name",
            folder_id=200,
            folder_name="Analysis",
            folder_url="https://usfs-public.app.box.com/v/PinyonPublic/folder/200",
            page_count=2,
            page_number=2,
            items=[
                {
                    "id": 902,
                    "type": "file",
                    "name": "Appendix A.pdf",
                    "typedID": "f_902",
                    "itemSize": 31,
                    "extension": "pdf",
                    "created": 5,
                    "contentUpdated": 6,
                }
            ],
        ),
        (300, 1): _FetchedBoxFolderPage(
            shared_name="shared-name",
            folder_id=300,
            folder_name="Reports",
            folder_url="https://usfs-public.app.box.com/v/PinyonPublic/folder/300",
            page_count=1,
            page_number=1,
            items=[
                {
                    "id": 903,
                    "type": "file",
                    "name": "Hydrology Report.pdf",
                    "typedID": "f_903",
                    "itemSize": 41,
                    "extension": "pdf",
                    "created": 7,
                    "contentUpdated": 8,
                }
            ],
        ),
    }

    inventory = build_box_folder_inventory(
        review_id="region1-example-nez-perce-clearwater-dead-laundry-57827",
        root_folder_url="https://usfs-public.app.box.com/v/PinyonPublic/folder/100",
        network=NETWORK,
        fetch_folder_page=lambda folder_id, page_number, _network: pages[(folder_id, page_number)],
    )

    assert inventory["schema_version"] == "box-folder-inventory-v1"
    assert inventory["root_box_folder_id"] == 100
    assert inventory["shared_name"] == "shared-name"
    assert inventory["folder_count"] == 4
    assert inventory["file_count"] == 4
    assert inventory["expected_total_byte_size"] == 104
    assert inventory["folders"][1]["relative_path"] == "Analysis"
    assert inventory["folders"][2]["page_number"] == 2
    assert inventory["files"][0]["relative_path"] == "Analysis/Appendix A.pdf"
    assert inventory["files"][-1]["relative_path"] == "Readme.pdf"


def test_download_box_folder_inventory_filters_selected_prefixes() -> None:
    inventory = {
        "review_id": "region1-example-nez-perce-clearwater-dead-laundry-57827",
        "root_folder_url": "https://usfs-public.app.box.com/v/PinyonPublic/folder/100",
        "root_box_folder_id": 100,
        "shared_name": "shared-name",
        "folder_count": 4,
        "files": [
            {
                "box_file_id": 900,
                "box_folder_id": 100,
                "box_folder_name": "Dead Laundry (57827)",
                "box_typed_id": "f_900",
                "content_updated": 2,
                "created": 1,
                "download_url_template": (
                    "https://usfs-public.app.box.com/index.php?rm=box_download_shared_file"
                    "&shared_name=<shared_name>&file_id=f_<box_file_id>"
                ),
                "expected_byte_size": 9,
                "extension": "pdf",
                "folder_page": 1,
                "folder_relative_path": "",
                "name": "Readme.pdf",
                "relative_path": "Readme.pdf",
                "source_folder_url": "https://usfs-public.app.box.com/v/PinyonPublic/folder/100",
            },
            {
                "box_file_id": 901,
                "box_folder_id": 200,
                "box_folder_name": "Analysis",
                "box_typed_id": "f_901",
                "content_updated": 4,
                "created": 3,
                "download_url_template": (
                    "https://usfs-public.app.box.com/index.php?rm=box_download_shared_file"
                    "&shared_name=<shared_name>&file_id=f_<box_file_id>"
                ),
                "expected_byte_size": 9,
                "extension": "pdf",
                "folder_page": 1,
                "folder_relative_path": "Analysis",
                "name": "Final EA.pdf",
                "relative_path": "Analysis/Final EA.pdf",
                "source_folder_url": "https://usfs-public.app.box.com/v/PinyonPublic/folder/200",
            },
        ],
    }

    with tempfile.TemporaryDirectory() as tmp:
        destination_dir = Path(tmp) / "source_library" / "reviews" / "_intake" / "dead-laundry"

        manifest = download_box_folder_inventory(
            inventory=inventory,
            destination_dir=destination_dir,
            network=NETWORK,
            include_relative_path_prefixes=["Analysis"],
            download_bytes=lambda url, _network: f"payload::{url[-5:-1]}".encode("utf-8"),
        )

        assert manifest["schema_version"] == "box-import-manifest-v1"
        assert manifest["document_count"] == 1
        assert manifest["downloaded_count"] == 1
        assert manifest["existing_count"] == 0
        assert manifest["failure_count"] == 0
        assert manifest["selection_relative_path_prefixes"] == ["Analysis"]
        document = manifest["documents"][0]
        assert document["relative_path"] == "Analysis/Final EA.pdf"
        assert document["status"] == "downloaded"
        assert destination_dir.joinpath("Analysis", "Final EA.pdf").exists()
