from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from cg.constants import Workflow


def test_create_raredisease_config_with_none_flag(
    raredisease_configurator: NextflowConfigurator,
    raredisease_case_config: NextflowCaseConfig,
    raredisease_case_id: str,
    raredisease_params_file_path: str,
    raredisease_work_dir_path: str,
):
    """Test creating the case config with a flag set to None."""
    # GIVEN a configurator and a case id
    gene_panel_creator: GenePanelFileCreator = (
        raredisease_configurator.pipeline_extension.gene_panel_file_creator
    )
    managed_variants_creator: ManagedVariantsFileCreator = (
        raredisease_configurator.pipeline_extension.managed_variants_file_creator
    )

    # GIVEN that scout returns panels and variants
    with (
        mock.patch.object(gene_panel_creator, "scout_api") as mock_gene_panel_scout_api,
        mock.patch.object(managed_variants_creator, "scout_api") as mock_managed_variants_scout_api,
    ):
        mock_gene_panel_scout_api.export_panels.return_value = []
        mock_managed_variants_scout_api.export_managed_variants.return_value = []

        # WHEN creating a case config specifying revision being None
        case_config: NextflowCaseConfig = raredisease_configurator.configure(
            case_id=raredisease_case_id, revision=None
        )

    # THEN the expected case config is returned without revision being changed
    assert case_config == raredisease_case_config


@pytest.mark.parametrize(
    "workflow",
    [Workflow.RAREDISEASE, Workflow.RNAFUSION],
)
def test_create_nextflow_configurator(
    workflow: Workflow,
    nextflow_case_id: str,
    nextflow_root: str,
    configurator_scenario: dict,
    mocker: MockerFixture,
):
    """Test creating the case config for all Nextflow pipelines."""

    # GIVEN a Nextflow configurator and an expected case config
    configurator, expected_case_config = configurator_scenario[workflow]

    # GIVEN that all expected files are mocked to exist
    mocker.patch.object(Path, "exists", return_value=True)

    # WHEN getting the case config
    case_config = configurator.get_config(case_id=nextflow_case_id)

    # THEN we should get back a case config
    assert case_config == expected_case_config


@pytest.mark.parametrize(
    "workflow",
    [Workflow.RAREDISEASE, Workflow.RNAFUSION],
)
def test_create_nextflow_configurator_flags(
    workflow: Workflow,
    nextflow_case_id: str,
    nextflow_root: str,
    configurator_scenario: dict,
    mocker: MockerFixture,
):
    """Test that using flags when configuring a case overrides the case config default values."""

    # GIVEN a Nextflow configurator and an expected case config
    configurator, _ = configurator_scenario[workflow]

    # GIVEN that all expected files are mocked to exist
    mocker.patch.object(Path, "exists", return_value=True)

    # WHEN getting the case config
    case_config = configurator.get_config(case_id=nextflow_case_id, revision="overridden")

    # THEN we should get back a case config with updated value
    assert case_config.revision == "overridden"
