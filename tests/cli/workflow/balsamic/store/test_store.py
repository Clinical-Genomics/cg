"""Tests for cg.cli.store.balsamic"""

from cg.cli.workflow.balsamic.store import analysis

EXIT_SUCCESS = 0


def test_store_analysis_with_file_parameter(
    cli_runner, balsamic_store_context, balsamic_case, deliverables_file
):
    """Test store with analysis file"""

    # GIVEN a meta file for a balsamic analysis

    # WHEN calling store with meta file
    result = cli_runner.invoke(
        analysis,
        [balsamic_case.internal_id, "--deliverables-file", deliverables_file],
        obj=balsamic_store_context,
        catch_exceptions=False,
    )

    # THEN we should not get a message that the analysis has been stored
    assert result.exit_code == EXIT_SUCCESS
    assert "included files in Housekeeper" in result.output


def test_already_stored_analysis(
    cli_runner, balsamic_store_context, balsamic_case, deliverables_file
):
    """Test store analysis command twice"""

    # GIVEN the analysis has already been stored
    cli_runner.invoke(
        analysis,
        [balsamic_case.internal_id, "--deliverables-file", deliverables_file],
        obj=balsamic_store_context,
    )

    # WHEN calling store again for same case
    result = cli_runner.invoke(
        analysis,
        [balsamic_case.internal_id, "--deliverables-file", deliverables_file],
        obj=balsamic_store_context,
    )

    # THEN we should get a message that the analysis has previously been stored
    assert result.exit_code != EXIT_SUCCESS
    assert "analysis version already added" in result.output


def test_store_analysis_generates_file_from_directory(
    cli_runner, balsamic_store_context, balsamic_case, deliverables_file_directory, mocker
):
    """Test store with analysis with meta data with one directory"""

    # GIVEN a meta file for a balsamic analysis containing directory that should be included
    mocked_is_dir = mocker.patch("os.path.isdir")
    mocked_is_dir.return_value = True
    mocker.patch("shutil.make_archive")

    # WHEN calling store with meta file
    result = cli_runner.invoke(
        analysis,
        [balsamic_case.internal_id, "--deliverables-file", deliverables_file_directory],
        obj=balsamic_store_context,
    )

    # THEN we there should be a file representing the directory in the included bundle
    assert result.exit_code == EXIT_SUCCESS
    assert "tgz" in balsamic_store_context["hk_api"].bundle_data["files"][0]["path"]


def test_store_analysis_includes_file_once(
    cli_runner, balsamic_store_context, balsamic_case, deliverables_file_tags
):
    """Test store with analysis with meta data with same file for multiple tags"""

    # GIVEN a meta file for a balsamic analysis containing one file with two tags

    # WHEN calling store with meta file
    result = cli_runner.invoke(
        analysis,
        [balsamic_case.internal_id, "--deliverables-file", deliverables_file_tags],
        obj=balsamic_store_context,
    )

    # THEN we there should be one file with two tags in the included bundle
    assert result.exit_code == EXIT_SUCCESS
    assert len(balsamic_store_context["hk_api"].bundle_data["files"]) == 1
    assert set(balsamic_store_context["hk_api"].bundle_data["files"][0]["tags"]) == set(
        ["vcf", "vep"]
    )
