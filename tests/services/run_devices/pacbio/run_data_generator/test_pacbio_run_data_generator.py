"""Tests for the PacBioRunDataGenerator."""

from pathlib import Path

import pytest

from cg.services.run_devices.exc import PostProcessingRunDataGeneratorError
from cg.services.run_devices.pacbio.run_data_generator.pacbio_run_data_generator import (
    PacBioRunDataGenerator,
)
from cg.services.run_devices.pacbio.run_data_generator.run_data import PacBioRunData


def test_get_run_data(
    pac_bio_runs_dir: Path,
    pac_bio_test_run_name: str,
    pac_bio_smrt_cell_name: str,
    expected_pac_bio_run_data: PacBioRunData,
):
    # GIVEN a run directory, a run name and a SMRT cell name
    run_name: str = "/".join([pac_bio_test_run_name, pac_bio_smrt_cell_name])

    # WHEN Generating run data
    run_data_generator = PacBioRunDataGenerator()
    run_data: PacBioRunData = run_data_generator.get_run_data(
        run_name=run_name, sequencing_dir=pac_bio_runs_dir.as_posix()
    )

    # THEN the correct run data are returned
    assert run_data == expected_pac_bio_run_data


@pytest.mark.parametrize("run_name", ["rimproper_name", "d_improper_name "])
def test_get_run_data_improper_name(
    pac_bio_runs_dir: Path,
    run_name: str,
):
    # GIVEN a PacBioRunDataGenerator and an improper run name
    run_data_generator = PacBioRunDataGenerator()

    # WHEN Generating run data

    # THEN an PostProcessingRunDataGeneratorError is raised
    with pytest.raises(PostProcessingRunDataGeneratorError):
        run_data_generator.get_run_data(
            run_name=run_name, sequencing_dir=pac_bio_runs_dir.as_posix()
        )
