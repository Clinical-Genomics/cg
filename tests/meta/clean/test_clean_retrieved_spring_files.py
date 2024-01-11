import logging

from housekeeper.store.models import File

from cg.meta.clean.clean_retrieved_spring_files import CleanRetrievedSpringFilesAPI


def test_get_files_to_remove(
    populated_clean_retrieved_spring_files_api_dry_run: CleanRetrievedSpringFilesAPI,
    path_to_old_retrieved_spring_file: str,
    path_to_old_retrieved_spring_file_in_housekeeper: str,
):
    """Tests that only old retrieved files are cleaned with clean_retrieved_spring_files. With the provided populated
    api, this should not return a newly retrieved spring file, a fastq file nor an archived spring file which
    has not been retrieved."""

    # GIVEN a CleanRetrievedSpringFilesAPI with a populated Housekeeper database

    # WHEN getting files to remove when cleaning retrieved spring files
    files_to_remove: list[
        File
    ] = populated_clean_retrieved_spring_files_api_dry_run._get_files_to_remove(age_limit=7)

    # THEN only the file with an old enough 'retrieved_at' should be returned
    assert [file.path for file in files_to_remove] == [
        path_to_old_retrieved_spring_file_in_housekeeper
    ]


def test_clean_retrieved_spring_files_dry_run(
    populated_clean_retrieved_spring_files_api_dry_run: CleanRetrievedSpringFilesAPI,
    path_to_old_retrieved_spring_file: str,
    path_to_old_retrieved_spring_file_in_housekeeper: str,
    caplog,
):
    """Tests that only the Spring file with an old enough 'retrieved_at' would be removed when cleaning retrieved
    Spring files."""

    caplog.set_level(logging.INFO)

    # GIVEN a CleanRetrievedSpringFilesAPI with a populated Housekeeper database

    # WHEN running 'clean_retrieved_spring_files'
    populated_clean_retrieved_spring_files_api_dry_run.clean_retrieved_spring_files(age_limit=7)

    # THEN only the file with an old enough 'retrieved_at' should have been removed
    assert (
        f"Dry run - would have unlinked {path_to_old_retrieved_spring_file_in_housekeeper}"
        in caplog.text
    )
