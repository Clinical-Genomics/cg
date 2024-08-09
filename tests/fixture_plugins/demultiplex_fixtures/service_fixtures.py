from pathlib import Path

import pytest

from cg.apps.lims import LimsAPI
from cg.services.illumina.sample_sheet.creator import SampleSheetCreator
from cg.services.illumina.sample_sheet.parser import SampleSheetParser
from cg.services.illumina.sample_sheet.sample_updater import SamplesUpdater
from cg.services.illumina.sample_sheet.validator import SampleSheetValidator


@pytest.fixture
def samples_updater() -> SamplesUpdater:
    return SamplesUpdater()


@pytest.fixture
def sample_sheet_parser() -> SampleSheetParser:
    return SampleSheetParser()


@pytest.fixture
def sample_sheet_validator(sample_sheet_parser: SampleSheetParser) -> SampleSheetValidator:
    return SampleSheetValidator(parser=sample_sheet_parser)


@pytest.fixture
def sample_sheet_creator(
    lims_api: LimsAPI,
    sample_sheet_validator: SampleSheetValidator,
    samples_updater: SamplesUpdater,
    illumina_sequencing_runs_directory: Path,
) -> SampleSheetCreator:
    return SampleSheetCreator(
        sequencing_dir=illumina_sequencing_runs_directory.as_posix(),
        lims_api=lims_api,
        validator=sample_sheet_validator,
        updater=samples_updater,
    )
