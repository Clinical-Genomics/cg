from pathlib import Path
from unittest import mock

import pytest

from cg.services.analysis_starter.configurator.abstract_model import CaseConfig
from cg.services.analysis_starter.configurator.abstract_service import Configurator
from cg.services.analysis_starter.configurator.implementations.raredisease import (
    RarediseaseConfigurator,
)


@pytest.mark.parametrize(
    "configurator_fixture, case_config_fixture, case_id_fixture",
    [("raredisease_configurator", "raredisease_case_config", "raredisease_case_id")],
    ids=["raredisease"],
)
def test_create_config(
    configurator_fixture: str,
    case_config_fixture: str,
    case_id_fixture: str,
    dummy_params_file_path: str,
    dummy_work_dir_path: str,
    request: pytest.FixtureRequest,
):
    """Test creating a case config."""
    # GIVEN a configurator and a case id
    configurator: Configurator = request.getfixturevalue(configurator_fixture)
    case_id: str = request.getfixturevalue(case_id_fixture)

    # WHEN creating a case config
    with (
        mock.patch.object(
            configurator, "_get_params_file_path", return_value=Path(dummy_params_file_path)
        ),
        mock.patch.object(configurator, "_get_work_dir", return_value=Path(dummy_work_dir_path)),
    ):
        case_config: CaseConfig = configurator.create_config(case_id=case_id)

    # THEN the expected case config is returned
    expected_case_config: CaseConfig = request.getfixturevalue(case_config_fixture)
    assert case_config == expected_case_config


def test_get_nextflow_config_content(
    raredisease_case_id: str,
    raredisease_configurator: RarediseaseConfigurator,
    expected_raredisease_config_content: str,
):
    """Test getting nextflow config content."""
    # GIVEN a configurator

    # WHEN getting nextflow config content
    nextflow_config_content: str = raredisease_configurator._get_nextflow_config_content(
        case_id=raredisease_case_id
    )

    # THEN the expected content is returned
    assert nextflow_config_content.rstrip() == expected_raredisease_config_content.rstrip()
