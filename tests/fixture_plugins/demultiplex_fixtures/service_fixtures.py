from pathlib import Path

import pytest

from cg.apps.lims import LimsAPI
from cg.services.illumina.sample_sheet.creator import SampleSheetCreator
from cg.services.illumina.sample_sheet.parser import SampleSheetParser
from cg.services.illumina.sample_sheet.sample_updater import SamplesUpdater


@pytest.fixture
def samples_updater() -> SamplesUpdater:
    return SamplesUpdater()


@pytest.fixture
def sample_sheet_parser() -> SampleSheetParser:
    return SampleSheetParser()


@pytest.fixture
def sample_sheet_creator(
    lims_api: LimsAPI,
    samples_updater: SamplesUpdater,
    illumina_sequencing_runs_directory: Path,
) -> SampleSheetCreator:
    return SampleSheetCreator(
        sequencing_dir=illumina_sequencing_runs_directory.as_posix(),
        lims_api=lims_api,
        updater=samples_updater,
    )
