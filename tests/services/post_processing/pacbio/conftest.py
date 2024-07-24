"""Fixtures for the PacBio post processing services."""

from pathlib import Path

import pytest

from cg.services.post_processing.pacbio.run_data_generator.run_data import PacBioRunData


@pytest.fixture
def expected_pac_bio_run_data(
    pac_bio_test_run_name: str, pac_bio_fixtures_dir: Path
) -> PacBioRunData:
    return PacBioRunData(
        full_path=Path(pac_bio_fixtures_dir, pac_bio_test_run_name),
        sequencing_run_name=pac_bio_test_run_name,
        well_name="A01",
        plate="1",
    )
