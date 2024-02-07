from pathlib import Path

from cg.meta.transfer.utils import get_all_fastq_from_folder


def test_get_all_fastq_from_folder(external_data_directory: Path):
    """Test the finding of fastq.gz files in customer directories."""
    # GIVEN a folder containing two folders with both fastq and md5 files
    for folder in external_data_directory.iterdir():
        # WHEN the list of file paths is created
        files = get_all_fastq_from_folder(sample_folder=external_data_directory.joinpath(folder))
        # THEN only fast.gz files are returned
        assert all(tmp.suffixes == [".fastq", ".gz"] for tmp in files)
