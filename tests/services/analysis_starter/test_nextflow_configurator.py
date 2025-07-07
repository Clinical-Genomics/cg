from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from cg.apps.scout.scoutapi import ScoutAPI
from cg.services.analysis_starter.configurator.implementations.nextflow import NextflowConfigurator
from cg.services.analysis_starter.configurator.models.nextflow import NextflowCaseConfig


def test_create_raredisease_config(
    raredisease_configurator: NextflowConfigurator,
    raredisease_case_config: NextflowCaseConfig,
    raredisease_case_id: str,
    mocker: MockerFixture,
):
    """Test creating the case config for all pipelines."""

    # GIVEN that scout returns panels and variants
    mocker.patch.object(ScoutAPI, "export_panels", return_value=[])
    mocker.patch.object(ScoutAPI, "export_managed_variants", return_value=[])

    # WHEN creating a case config
    case_config: NextflowCaseConfig = raredisease_configurator.configure(
        case_id=raredisease_case_id
    )

    # THEN the expected case config is returned
    assert case_config == raredisease_case_config


def test_create_raredisease_config_with_flag(
    raredisease_configurator: NextflowConfigurator,
    raredisease_case_config: NextflowCaseConfig,
    raredisease_case_id: str,
    mocker: MockerFixture,
):
    """Test creating the case config for all pipelines."""

    # GIVEN that scout returns panels and variants
    mocker.patch.object(ScoutAPI, "export_panels", return_value=[])
    mocker.patch.object(ScoutAPI, "export_managed_variants", return_value=[])

    # WHEN creating a case config specifying additional options
    case_config: NextflowCaseConfig = raredisease_configurator.configure(
        case_id=raredisease_case_id, revision="0.0.0"
    )

    # THEN the expected case config is returned
    assert case_config == raredisease_case_config.model_copy(update={"revision": "0.0.0"})


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


def test_create_rnafusion_configurator(
    nextflow_case_id: str,
    nextflow_root: str,
    rnafusion_configurator: NextflowConfigurator,
    mocker: MockerFixture,
    rnafusion_case_config: NextflowCaseConfig,
):

    # GIVEN that IO operations are mocked
    mocker.patch.object(Path, "exists", return_value=True)

    # GIVEN that the case path is mocked
    rnafusion_configurator.root_dir = nextflow_root

    # WHEN getting the case config
    case_config = rnafusion_configurator.get_config(case_id=nextflow_case_id)

    # THEN we should get back a case config
    assert case_config == rnafusion_case_config


def test_create_rnafusion_configurator_flags(
    nextflow_case_id: str,
    nextflow_root: str,
    rnafusion_configurator: NextflowConfigurator,
    mocker: MockerFixture,
    rnafusion_case_config: NextflowCaseConfig,
):

    # GIVEN that IO operations are mocked
    mocker.patch.object(Path, "exists", return_value=True)

    # GIVEN that the case path is mocked
    rnafusion_configurator.root_dir = nextflow_root

    # WHEN getting the case config
    case_config = rnafusion_configurator.get_config(case_id=nextflow_case_id, revision="overridden")

    # THEN we should get back a case config with updated value
    assert case_config.revision == "overridden"
