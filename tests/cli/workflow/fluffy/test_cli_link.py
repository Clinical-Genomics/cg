from pathlib import Path

from cg.cli.workflow.fluffy.base import link
from cg.constants import EXIT_SUCCESS, EXIT_FAIL
from cg.meta.workflow.fluffy import FluffyAnalysisAPI


def test_link_dry(
    cli_runner,
    fluffy_case_id_existing,
    fluffy_context,
    caplog,
):
    caplog.set_level("INFO")
    result = cli_runner.invoke(link, [fluffy_case_id_existing, "--dry-run"], obj=fluffy_context)
    assert result.exit_code == EXIT_SUCCESS
    assert "Linking" in caplog.text


def test_link(
    cli_runner,
    fluffy_case_id_existing,
    fluffy_sample_lims_id,
    fluffy_context,
    fastq_file_fixture_path,
    caplog,
):
    fluffy_analysis_api: FluffyAnalysisAPI = fluffy_context["fluffy_analysis_api"]
    Path(fluffy_analysis_api.root_dir, fluffy_case_id_existing).mkdir(exist_ok=True, parents=True)
    caplog.set_level("INFO")
    result = cli_runner.invoke(link, [fluffy_case_id_existing], obj=fluffy_context)
    assert "Linking" in caplog.text
    assert result.exit_code == EXIT_SUCCESS
    assert Path(
        fluffy_analysis_api.get_fastq_path(
            case_id=fluffy_case_id_existing, sample_id=fluffy_sample_lims_id
        )
    ).exists()


def test_link_dir_exists(
    cli_runner,
    fluffy_case_id_existing,
    fluffy_sample_lims_id,
    fluffy_context,
    fastq_file_fixture_path,
    caplog,
):
    fluffy_analysis_api: FluffyAnalysisAPI = fluffy_context["fluffy_analysis_api"]
    Path(fluffy_analysis_api.get_workdir_path(fluffy_case_id_existing)).mkdir(
        exist_ok=True, parents=True
    )
    caplog.set_level("INFO")
    result = cli_runner.invoke(link, [fluffy_case_id_existing], obj=fluffy_context)
    assert "Linking" in caplog.text
    assert result.exit_code == EXIT_SUCCESS
    assert Path(
        fluffy_analysis_api.get_fastq_path(
            case_id=fluffy_case_id_existing, sample_id=fluffy_sample_lims_id
        )
    ).exists()
    assert "directory exists" in caplog.text
