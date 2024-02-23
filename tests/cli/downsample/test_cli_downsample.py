"""Tests for the downsample command."""

from pathlib import Path

from click.testing import CliRunner, Result

from cg.cli.downsample import store_downsampled_samples
from cg.models.cg_config import CGConfig


def test_store_downsampled_fastq_files(
    downsample_context: CGConfig,
    downsample_sample_internal_id_1: str,
    downsample_sample_internal_id_2: str,
    cli_runner: CliRunner,
    downsample_dir: Path,
    tmp_path_factory,
):
    """Test to store the downsampled fastq files in housekeeper."""
    # GIVEN directories with downsampled sample
    for sample_id in [
        f"{downsample_sample_internal_id_1}_5M",
        f"{downsample_sample_internal_id_2}_5M",
    ]:
        Path(downsample_dir, f"{sample_id}").mkdir()
        Path(downsample_dir, f"{sample_id}", f"{sample_id}.fastq.gz").touch()
    # WHEN calling the cli command to store the fastq files
    result: Result = cli_runner.invoke(
        store_downsampled_samples,
        args=[f"{downsample_sample_internal_id_1}_5M", f"{downsample_sample_internal_id_2}_5M"],
        obj=downsample_context,
    )

    # THEN the command should run successfully
    assert result.exit_code == 0

    # THEN both samples should be stored in housekeeper
    for sample_id in [
        f"{downsample_sample_internal_id_1}_5M",
        f"{downsample_sample_internal_id_2}_5M",
    ]:
        assert downsample_context.housekeeper_api.get_latest_bundle_version(sample_id)
        assert downsample_context.housekeeper_api.get_file_from_latest_version(
            bundle_name=sample_id, tags=["fastq"]
        )
