from pathlib import Path

from cg.services.decompression_service.decompressor import Decompressor


def test_decompressor(zipped_folder: Path, destination_folder: Path, file_in_zip: Path):
    # GIVEN a decompressor, a source path and a destination path
    decompressor = Decompressor()
    assert zipped_folder.exists()

    # WHEN decompressing a file
    decompressed_path = decompressor.decompress(
        source_path=zipped_folder, destination_path=destination_folder
    )

    # THEN assert that the decompressed path exists
    assert decompressed_path.exists()
    assert decompressed_path.is_dir()

    # THEN assert the expected files are in the decompressed path
    assert file_in_zip.name in [file.name for file in decompressed_path.iterdir()]
