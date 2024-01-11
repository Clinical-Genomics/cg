import logging
from pathlib import Path

from housekeeper.store.models import File

from cg.meta.clean.clean_retrieved_spring_files import CleanRetrievedSpringFilesAPI


def test_get_files_to_remove(
    populated_clean_retrieved_spring_files_api: CleanRetrievedSpringFilesAPI,
    path_to_old_retrieved_spring_file: str,
    path_to_old_retrieved_spring_file_in_housekeeper: str,
):
    """Tests that only old retrieved files are cleaned with clean_retrieved_spring_files. With the provided populated
    api, this should not return a newly retrieved spring file, a fastq file nor an archived spring file which
    has not been retrieved."""

    # GIVEN a CleanRetrievedSpringFilesAPI with a populated Housekeeper database

    # WHEN getting files to remove when cleaning retrieved spring files
    files_to_remove: list[File] = populated_clean_retrieved_spring_files_api._get_files_to_remove(
        age_limit=7
    )

    # THEN only the file with an old enough 'retrieved_at' should be returned
    assert [file.path for file in files_to_remove] == [
        path_to_old_retrieved_spring_file_in_housekeeper
    ]


def test_clean_retrieved_spring_files_dry_run(
    populated_clean_retrieved_spring_files_api: CleanRetrievedSpringFilesAPI,
    path_to_old_retrieved_spring_file: str,
    retrieved_test_bundle_name: str,
    caplog,
):
    """Tests that only the Spring file with an old enough 'retrieved_at' would be removed when cleaning retrieved
    Spring files."""

    caplog.set_level(logging.INFO)

    # GIVEN a CleanRetrievedSpringFilesAPI with a populated Housekeeper database
    # GIVEN that an old retrieved file exists
    for file in populated_clean_retrieved_spring_files_api.housekeeper_api.get_files(
        bundle=retrieved_test_bundle_name
    ):
        if path_to_old_retrieved_spring_file in file.path:
            file_path: str = file.path
            Path(file_path).touch()

    # WHEN running 'clean_retrieved_spring_files'
    populated_clean_retrieved_spring_files_api.clean_retrieved_spring_files(age_limit=7)

    # THEN the file with an old enough 'retrieved_at' should have been removed
    assert not Path(file_path).exists()
