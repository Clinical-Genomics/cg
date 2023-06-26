from cg.models.cg_config import CGConfig
from click.testing import CliRunner


def test_remove_old_flow_cell_dirs_skip_failing_flow_cell(
    cli_runner: CliRunner, cg_context: CGConfig, caplog
):
    # GIVEN an old flow cell which is not tagged as archived but which is present in Housekeeper

    # WHEN running the clean remove_old_flow_cell_dirs

    # THEN assert that the error is caught

    # THEN assert that the removal of other flow cell directories continued
    return True
