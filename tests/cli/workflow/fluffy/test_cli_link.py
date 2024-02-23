import shutil
from pathlib import Path

from click.testing import CliRunner

from cg.cli.workflow.commands import link
from cg.constants import EXIT_SUCCESS
from cg.meta.workflow.fluffy import FluffyAnalysisAPI
from cg.models.cg_config import CGConfig


def test_cli_link_no_case(
    cli_runner: CliRunner,
    fluffy_case_id_non_existing,
    fluffy_sample_lims_id,
    fluffy_context: CGConfig,
    caplog,
):
    caplog.set_level("ERROR")
    fluffy_analysis_api: FluffyAnalysisAPI = fluffy_context.meta_apis["analysis_api"]

    # GIVEN a case_id that does not exist in database

    # WHEN running command in dry-run
    result = cli_runner.invoke(link, [fluffy_case_id_non_existing], obj=fluffy_context)

    # THEN command does not terminate successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN log informs that case id does not exist
    assert fluffy_case_id_non_existing in caplog.text

    # THEN file directories were not created
    assert not Path(
        fluffy_analysis_api.get_fastq_path(
            case_id=fluffy_case_id_non_existing, sample_id=fluffy_sample_lims_id
        )
    ).exists()


def test_cli_link(
    cli_runner: CliRunner,
    fluffy_case_id_existing,
    fluffy_sample_lims_id,
    fluffy_context: CGConfig,
    fluffy_fastq_file_path,
    caplog,
):
    caplog.set_level("INFO")
    fluffy_analysis_api: FluffyAnalysisAPI = fluffy_context.meta_apis["analysis_api"]
    # GIVEN that a fastq path does not exist
    fastq_path: Path = Path(
        fluffy_analysis_api.get_fastq_path(
            case_id=fluffy_case_id_existing, sample_id=fluffy_sample_lims_id
        )
    )
    assert not fastq_path.exists()

    # GIVEN a case_id that does exist in database

    # WHEN running command
    result = cli_runner.invoke(link, [fluffy_case_id_existing], obj=fluffy_context)

    # THEN log informs about what paths it links from and to
    assert "Linking" in caplog.text

    # THEN command terminates successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN file directories were created
    assert fastq_path.exists()

    # Clean-uo
    shutil.rmtree(fastq_path)


def test_cli_link_dir_exists(
    cli_runner: CliRunner,
    fluffy_case_id_existing,
    fluffy_sample_lims_id,
    fluffy_context: CGConfig,
    fluffy_fastq_file_path,
    caplog,
):
    caplog.set_level("INFO")
    fluffy_analysis_api: FluffyAnalysisAPI = fluffy_context.meta_apis["analysis_api"]

    # GIVEN a case_id that does exist in database

    # GIVEN folder with fastq files already present in working directory
    Path(fluffy_analysis_api.get_workdir_path(fluffy_case_id_existing)).mkdir(
        exist_ok=True, parents=True
    )

    # WHEN running command
    result = cli_runner.invoke(link, [fluffy_case_id_existing], obj=fluffy_context)

    # THEN log informs about what paths it links from and to
    assert "Linking" in caplog.text

    # THEN command terminates successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN file directories were created
    assert Path(
        fluffy_analysis_api.get_fastq_path(
            case_id=fluffy_case_id_existing, sample_id=fluffy_sample_lims_id
        )
    ).exists()

    # THEN log informs that directory exists and will be re-created
    assert "directory exists" in caplog.text
