"""Housekeeper fixtures for demultiplex tests."""

from datetime import datetime
from pathlib import Path

import pytest

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from tests.store_helpers import StoreHelpers


@pytest.fixture(scope="function")
def illumina_demultiplexed_runs_post_processing_hk_api(
    canonical_flow_cell_ids_and_sample_sheet_paths,
    tmp_fastq_files_for_all_canonical_illumina_demultiplexed_runs: dict[str, list[Path]],
    helpers: StoreHelpers,
    real_housekeeper_api: HousekeeperAPI,
) -> HousekeeperAPI:
    """Return a Housekeeper API instance with Illumina demultiplexed runs."""
    for flow_cell_id in canonical_flow_cell_ids_and_sample_sheet_paths.keys():
        sample_sheet_path: Path = canonical_flow_cell_ids_and_sample_sheet_paths[flow_cell_id]
        run_sample_sheet_bundle: dict = {
            "name": flow_cell_id,
            "created": datetime.now(),
            "version": "1.0",
            "files": [
                {
                    "path": sample_sheet_path.as_posix(),
                    "tags": ["samplesheet", flow_cell_id],
                    "archive": False,
                }
            ],
        }
        helpers.ensure_hk_bundle(store=real_housekeeper_api, bundle_data=run_sample_sheet_bundle)

        sample_ids: list[str] = tmp_fastq_files_for_all_canonical_illumina_demultiplexed_runs[
            flow_cell_id
        ].keys()
        for sample_id in sample_ids:
            tmp_fastq_path: Path = tmp_fastq_files_for_all_canonical_illumina_demultiplexed_runs[
                flow_cell_id
            ][sample_id]
            bundle_data: dict = {
                "name": sample_id,
                "created": datetime.now(),
                "version": "1.0",
                "files": [
                    {
                        "path": tmp_fastq_path.as_posix(),
                        "tags": [SequencingFileTag.FASTQ, flow_cell_id],
                        "archive": False,
                    },
                ],
            }
            helpers.ensure_hk_bundle(store=real_housekeeper_api, bundle_data=bundle_data)
    return real_housekeeper_api
