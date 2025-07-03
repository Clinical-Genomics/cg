from pathlib import Path
from unittest.mock import create_autospec

import pytest
from housekeeper.store.models import File
from pytest_mock import MockerFixture

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.raredisease import (
    RarediseaseSampleSheetCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.rnafusion import (
    RNAFusionSampleSheetCreator,
)


@pytest.fixture
def raredisease_sample_sheet_creator(
    raredisease_context: CGConfig,
) -> RarediseaseSampleSheetCreator:
    return RarediseaseSampleSheetCreator(
        store=raredisease_context.status_db,
        housekeeper_api=raredisease_context.housekeeper_api,
        lims=raredisease_context.lims_api,
    )


@pytest.fixture
def rnafusion_sample_sheet_creator(
    cg_context, fastq_path_1: Path, fastq_path_2: Path, mocker: MockerFixture
) -> RNAFusionSampleSheetCreator:
    housekeeper_mock = create_autospec(HousekeeperAPI)
    fastq_file1 = create_autospec(File)
    fastq_file1.full_path = fastq_path_1.as_posix()
    fastq_file2 = create_autospec(File)
    fastq_file2.full_path = fastq_path_2.as_posix()
    mocker.patch.object(housekeeper_mock, "files", return_value=[fastq_file1, fastq_file2])
    return RNAFusionSampleSheetCreator(
        store=cg_context.status_db,
        housekeeper_api=housekeeper_mock,
    )
