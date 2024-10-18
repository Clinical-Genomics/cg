from pathlib import Path

from cg.constants import FileExtensions
from cg.services.illumina.backup.utils import (
    get_latest_archived_encryption_key_path,
    get_latest_archived_sequencing_run_path,
)


def test_get_latest_encryption_key_path(dsmc_q_archive_output: list[str], flow_cell_name: str):
    """Tests returning an encryption key path from DSMC output."""
    # GIVEN an DSMC output and a flow cell id
    key_path: Path = get_latest_archived_encryption_key_path(dsmc_output=dsmc_q_archive_output)

    # THEN this method should return a path object
    assert isinstance(key_path, Path)

    # THEN the latest key file name should be returned
    expected: str = (
        f"161115_ST-E00214_0118_B{flow_cell_name}{FileExtensions.KEY}{FileExtensions.GPG}"
    )
    assert key_path.name == expected


def test_get_latest_archived_run_path(dsmc_q_archive_output: list[str], flow_cell_name: str):
    """Tests returning an Illumina run path from DSMC output."""
    # GIVEN an DSMC output and a flow cell id
    runs_path: Path = get_latest_archived_sequencing_run_path(dsmc_output=dsmc_q_archive_output)

    # THEN this method should return a path object
    assert isinstance(runs_path, Path)

    # THEN the latest Illumina run file name should be returned
    expected: str = (
        f"161115_ST-E00214_0118_B{flow_cell_name}{FileExtensions.TAR}{FileExtensions.GZIP}{FileExtensions.GPG}"
    )
    assert runs_path.name == expected
