"""Tests for the PacBioRunDataGenerator."""

from pathlib import Path

import pytest

from cg.services.run_devices.exc import PostProcessingRunDataGeneratorError
from cg.services.run_devices.pacbio.run_data_generator.pacbio_run_data_generator import (
    PacBioRunDataGenerator,
)
from cg.services.run_devices.pacbio.run_data_generator.run_data import PacBioRunData


@pytest.mark.parametrize(
    "run_name_fixture, smrt_cell_name_fixture, run_data_fixture",
    [
        (
            "pac_bio_test_run_name",
            "pac_bio_smrt_cell_name",
            "expected_pac_bio_run_data_1_b01",
        ),
        ("pacbio_barcoded_run_name", "pacbio_barcoded_smrt_cell_name", "pacbio_barcoded_run_data"),
    ],
    ids=["1_B01", "1_C01"],
)
def test_get_run_data(
    pac_bio_run_data_generator: PacBioRunDataGenerator,
    pac_bio_runs_dir: Path,
    run_name_fixture: str,
    smrt_cell_name_fixture: str,
    run_data_fixture: str,
    request: pytest.FixtureRequest,
):
    # GIVEN a run directory, a run name and a SMRT cell name
    run_name: str = request.getfixturevalue(run_name_fixture)
    smrt_cell_name: str = request.getfixturevalue(smrt_cell_name_fixture)
    expected_run_data: PacBioRunData = request.getfixturevalue(run_data_fixture)
    run_name: str = "/".join([run_name, smrt_cell_name])

    # WHEN Generating run data
    run_data: PacBioRunData = pac_bio_run_data_generator.get_run_data(
        run_name=run_name, sequencing_dir=pac_bio_runs_dir.as_posix()
    )

    # THEN the correct run data are returned
    assert run_data == expected_run_data


@pytest.mark.parametrize("wrong_run_name", ["rimproper_name", "d_improper_name "])
def test_get_run_data_improper_name(
    pac_bio_run_data_generator: PacBioRunDataGenerator,
    pac_bio_runs_dir: Path,
    wrong_run_name: str,
):
    # GIVEN a PacBioRunDataGenerator and a wrong run name

    # WHEN Generating run data with the wrong run name

    # THEN an PostProcessingRunDataGeneratorError is raised
    with pytest.raises(PostProcessingRunDataGeneratorError):
        pac_bio_run_data_generator.get_run_data(
            run_name=wrong_run_name, sequencing_dir=pac_bio_runs_dir.as_posix()
        )
