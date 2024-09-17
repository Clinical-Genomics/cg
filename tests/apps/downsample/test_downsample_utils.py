from pathlib import Path

from cg.apps.downsample.downsample import DownsampleAPI
from cg.apps.downsample.utils import store_downsampled_sample_bundle
from cg.constants import SequencingFileTag
from cg.models.downsample.downsample_data import DownsampleData


def test_add_fastq_files_to_housekeeper(
    downsample_api: DownsampleAPI, downsample_data: DownsampleData, tmp_path, downsample_dir: Path
):
    """Test to add downsampled fastq files to housekeeper."""

    # GIVEN a downsample api and downsampled fastq files
    downsampled_sample_dir = Path(
        downsample_dir, f"{downsample_data.downsampled_sample.internal_id}"
    )
    downsampled_sample_dir.mkdir()
    Path(
        downsampled_sample_dir,
        f"{downsample_data.downsampled_sample.internal_id}.fastq.gz",
    ).touch()
    assert downsample_data.fastq_file_output_directory.exists()
    # WHEN adding fastq files to housekeeper
    store_downsampled_sample_bundle(
        housekeeper_api=downsample_data.housekeeper_api,
        sample_id=downsample_data.downsampled_sample.internal_id,
        fastq_file_output_directory=str(downsampled_sample_dir),
    )

    # THEN fastq files are added to the downsampled bundle
    assert downsample_api.housekeeper_api.get_latest_bundle_version(
        downsample_data.downsampled_sample.internal_id
    )

    assert downsample_api.housekeeper_api.get_files(
        downsample_data.downsampled_sample.internal_id, tags=[SequencingFileTag.FASTQ]
    )
