import logging
from pathlib import Path

from housekeeper.store.models import File

from cg.meta.clean.clean_retrieved_spring_files import CleanRetrievedSpringFilesAPI


def test_get_files_to_remove(
    populated_clean_retrieved_spring_files_api: CleanRetrievedSpringFilesAPI,
    path_to_old_retrieved_spring_file: str,
):
    """Tests that only old retrieved files are cleaned with clean_retrieved_spring_files. With the provided populated
    api, this should not return a newly retrieved spring file, a fastq file nor an archived spring file which
    has not been retrieved."""

    # GIVEN a clean retrieved Spring files API with a populated Housekeeper database

    # WHEN getting files to remove when cleaning retrieved spring files
    files_to_remove: list[File] = populated_clean_retrieved_spring_files_api._get_files_to_remove()

    # THEN only the file with an old enough 'retrieved_at' should be returned
    assert [file.path for file in files_to_remove] == [
        Path(path_to_old_retrieved_spring_file).absolute().as_posix()
    ]


def test_clean_retrieved_spring_files(
    populated_clean_retrieved_spring_files_api: CleanRetrievedSpringFilesAPI,
    path_to_old_retrieved_spring_file: str,
    caplog,
):
    """Tests that only the Spring file with an old enough 'retrieved_at' would be removed when cleaning retrieved
    Spring files."""

    caplog.set_level(logging.INFO)
    # GIVEN a clean retrieved Spring files API with a populated Housekeeper database

    # WHEN running 'clean_retrieved_spring_files'
    populated_clean_retrieved_spring_files_api.clean_retrieved_spring_files(dry_run=True)

    # THEN only the file with an old enough 'retrieved_at' should have been removed
    assert (
        f"Dry run - would have unlinked {Path(path_to_old_retrieved_spring_file).absolute().as_posix()}"
        in caplog.text
    )
