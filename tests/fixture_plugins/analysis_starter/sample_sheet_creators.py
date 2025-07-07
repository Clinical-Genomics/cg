from pathlib import Path
from unittest.mock import create_autospec

import pytest
from housekeeper.store.models import File

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.raredisease import (
    RarediseaseSampleSheetCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.rnafusion import (
    RNAFusionSampleSheetCreator,
)
from cg.store.store import Store


@pytest.fixture
def raredisease_sample_sheet_creator(
    raredisease_context: CGConfig,
) -> RarediseaseSampleSheetCreator:
    return RarediseaseSampleSheetCreator(
        store=raredisease_context.status_db,
        housekeeper_api=raredisease_context.housekeeper_api,
    )


@pytest.fixture
def raredisease_sample_sheet_creator2(
    fastq_path_1: Path,
    fastq_path_2: Path,
    mock_store_for_raredisease_file_creators: Store,
) -> RarediseaseSampleSheetCreator:
    fastq_file1 = create_autospec(File)
    fastq_file1.full_path = fastq_path_1.as_posix()
    fastq_file2 = create_autospec(File)
    fastq_file2.full_path = fastq_path_2.as_posix()
    housekeeper_mock = create_autospec(HousekeeperAPI)
    housekeeper_mock.files.return_value = [fastq_file1, fastq_file2]
    return RarediseaseSampleSheetCreator(
        store=mock_store_for_raredisease_file_creators,
        housekeeper_api=housekeeper_mock,
    )


@pytest.fixture
def rnafusion_sample_sheet_creator(
    fastq_path_1: Path, fastq_path_2: Path, mock_store_for_rnafusion_sample_sheet_creator: Store
) -> RNAFusionSampleSheetCreator:
    fastq_file1 = create_autospec(File)
    fastq_file1.full_path = fastq_path_1.as_posix()
    fastq_file2 = create_autospec(File)
    fastq_file2.full_path = fastq_path_2.as_posix()
    housekeeper_mock = create_autospec(HousekeeperAPI)
    housekeeper_mock.files.return_value = [fastq_file1, fastq_file2]
    return RNAFusionSampleSheetCreator(
        store=mock_store_for_rnafusion_sample_sheet_creator,
        housekeeper_api=housekeeper_mock,
    )
