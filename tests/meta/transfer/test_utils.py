from pathlib import Path

from cg.utils.files import get_files_matching_pattern


def test_get_all_fastq_from_folder(external_data_directory: Path):
    """Test the finding of fastq.gz files in customer directories."""
    # GIVEN a folder containing two folders with both fastq and md5 files
    for folder in external_data_directory.iterdir():
        # WHEN the list of file paths is created
        sample_folder: Path = external_data_directory.joinpath(folder)
        file_paths: list[Path] = [
            sample_folder.joinpath(path)
            for path in get_files_matching_pattern(directory=sample_folder, pattern="*.fastq.gz")
        ]
        # THEN only fast.gz files are returned
        assert all(tmp.suffixes == [".fastq", ".gz"] for tmp in file_paths)
