from pathlib import Path

import mock
import pytest

from cg.services.analysis_starter.configurator.abstract_model import CaseConfig
from cg.services.analysis_starter.configurator.file_creators.gene_panel import GenePanelFileCreator
from cg.services.analysis_starter.configurator.file_creators.managed_variants import (
    ManagedVariantsFileCreator,
)
from cg.services.analysis_starter.configurator.implementations.nextflow import NextflowConfigurator
from cg.services.analysis_starter.configurator.models.nextflow import NextflowCaseConfig


def test_create_raredisease_config(
    raredisease_configurator: NextflowConfigurator,
    raredisease_case_config: NextflowCaseConfig,
    raredisease_case_id: str,
    raredisease_params_file_path: str,
    raredisease_work_dir_path: str,
):
    """Test creating the case config for all pipelines."""
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

        # WHEN creating a case config
        case_config: CaseConfig = raredisease_configurator.create_config(raredisease_case_id)

    # THEN the expected case config is returned
    assert case_config == raredisease_case_config


@pytest.mark.parametrize(
    "configurator_fixture, case_id_fixture, case_path_fixture",
    [("raredisease_configurator", "raredisease_case_id", "raredisease_case_path")],
    ids=["raredisease"],
)
def test_create_nextflow_config_file_exists(
    configurator_fixture: str,
    case_id_fixture: str,
    case_path_fixture: str,
    request: pytest.FixtureRequest,
):
    """Test that a Nextflow config file is created for all Nextflow pipelines."""
    # GIVEN a configurator, a case id and a case path
    configurator: NextflowConfigurator = request.getfixturevalue(configurator_fixture)
    case_id: str = request.getfixturevalue(case_id_fixture)
    case_path: Path = request.getfixturevalue(case_path_fixture)

    # GIVEN that a case directory exists
    configurator._create_case_directory(case_id=case_id)

    # WHEN creating nextflow config
    configurator.config_file_creator.create(case_id=case_id, case_path=case_path)

    # THEN the nextflow config is created
    case_path: Path = configurator._get_case_path(case_id=case_id)
    assert configurator.config_file_creator.get_file_path(
        case_id=case_id, case_path=case_path
    ).exists()
