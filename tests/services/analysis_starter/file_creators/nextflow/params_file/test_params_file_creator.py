from pathlib import Path
from unittest.mock import Mock, create_autospec

import pytest
from pytest_mock import MockerFixture

from cg.apps.lims.api import LimsAPI
from cg.constants.constants import Workflow
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file import (
    tomte_params_file_creator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.abstract import (
    ParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.tomte_params_file_creator import (
    TomteParamsFileCreator,
)
from cg.store.store import Store


def test_tomte_params_file_creator(mocker: MockerFixture):
    # GIVEN statusDB and connection to the LIMS API
    status_db: Store = create_autospec(Store)
    status_db.get_sample_ids_by_case_id = Mock(return_value=["sample_1", "sample_2"])
    lims_api: LimsAPI = create_autospec(LimsAPI)

    # GIVEN all sample have the same source, the best kind.
    lims_api.get_source = Mock(return_value="the_best_kind_of_source")

    # GIVEN a Tomte params file creator.
    file_creator = TomteParamsFileCreator(
        "/path/to/params_file", lims_api=lims_api, status_db=status_db
    )

    # GIVEN a workflow parameters file
    mocker.patch.object(tomte_params_file_creator, "read_yaml", return_value={"cat": "grep"})

    # GIVEN yaml can be written
    write_yaml_mock: Mock = mocker.patch.object(
        tomte_params_file_creator, "write_yaml_nextflow_style"
    )

    # WHEN calling create
    file_creator.create(
        case_id="santa_case",
        file_path=Path("down", "the", "chimney"),
        sample_sheet_path=Path("wish", "list"),
    )

    # THEN the params file was created with expected content
    write_yaml_mock.assert_called_once_with(
        content={
            "cat": "grep",
            "gene_panel_clinical_filter": Path("down", "the", "gene_panels.bed"),
            "genome": "GRCh38",
            "input": Path("wish", "list"),
            "outdir": Path("down", "the"),
            "tissue": "the_best_kind_of_source",
        },
        file_path=Path("down", "the", "chimney"),
    )


@pytest.mark.parametrize(
    "workflow",
    [
        Workflow.NALLO,
        Workflow.RNAFUSION,
        Workflow.TAXPROFILER,
        Workflow.TRANA_16S,
        Workflow.TRANA_ITS,
    ],
)
def test_nextflow_params_file_creator(
    workflow: Workflow,
    params_file_scenario: dict,
    nextflow_sample_sheet_path: Path,
    case_id: str,
    mocker: MockerFixture,
):
    """Test that the Nextflow params file is written correctly."""
    # GIVEN a file path where the params file should be written
    file_path = Path("/root", "case_id", "file_name.yaml")

    # GIVEN a params file creator class, an expected output and the module with the file creator
    file_creator_class, expected_content, module = params_file_scenario[workflow]
    file_creator: ParamsFileCreator = file_creator_class(params="workflow_parameters.yaml")

    # GIVEN a YAML reader that returns the content of a pipeline params file and a file writer
    read_yaml_mock: Mock = mocker.patch.object(
        module, "read_yaml", return_value={"workflow_param1": "some_value"}
    )
    write_yaml_mock: Mock = mocker.patch.object(module, "write_yaml_nextflow_style")

    # WHEN creating the params file
    file_creator.create(
        case_id=case_id,
        file_path=file_path,
        sample_sheet_path=nextflow_sample_sheet_path,
    )

    # THEN the workflow parameters was read from the correct file
    read_yaml_mock.assert_called_once_with(Path("workflow_parameters.yaml"))

    # THEN the file should have been written with the expected content
    write_yaml_mock.assert_called_once_with(file_path=file_path, content=expected_content)
