from pathlib import Path
from unittest.mock import MagicMock, Mock, create_autospec

import pytest
from pytest_mock import MockerFixture
from sqlalchemy import Case

from cg.apps.lims.api import LimsAPI
from cg.constants import Workflow
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.services.analysis_starter.configurator.file_creators.nextflow import config_file
from cg.services.analysis_starter.configurator.file_creators.nextflow.config_file import (
    NextflowConfigFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file import raredisease
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.raredisease import (
    RarediseaseParamsFileCreator,
)
from cg.store.models import BedVersion, Sample
from cg.store.store import Store


def test_raredisease_params_file_creator(mocker: MockerFixture):
    # GIVEN a file path
    file_path = Path("some_path", "file_name.yaml")

    # GIVEN a store containing a case with a linked sample. Also contains a bed version.
    super_sample = create_autospec(
        Sample,
        from_sample=None,
        internal_id="ACC",
        prep_category=SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING,
    )
    super_sample.name = "sample_name"
    case = create_autospec(Case, samples=[super_sample])
    store_mock: Store = create_autospec(Store)
    store_mock.get_samples_by_case_id = Mock(return_value=[super_sample])
    store_mock.get_case_by_internal_id_strict = Mock(return_value=case)
    store_mock.get_bed_version_by_short_name_strict = lambda short_name: (
        create_autospec(BedVersion, filename="bed_version.bed")
        if short_name == "target_bed_shortname_123"
        else create_autospec(BedVersion)
    )

    # GIVEN that Lims returns a bed shortname
    lims = create_autospec(LimsAPI)
    lims.get_capture_kit_strict = Mock(return_value="target_bed_shortname_123")

    # GIVEN a params file creator
    file_creator = RarediseaseParamsFileCreator(
        store=store_mock, lims=lims, params="Path_to_file.yaml"
    )

    # GIVEN case id
    case_id = "case_id"

    # GIVEN sample sheet path
    sample_sheet_path = Path("root", "samplesheet.csv")

    # GIVEN IO is mocked
    write_yaml_mock = mocker.patch.object(raredisease, "write_yaml_nextflow_style")
    write_csv_mock = mocker.patch.object(raredisease, "write_csv")
    mocker.patch.object(raredisease, "read_yaml", return_value={"Key": "Value"})

    # WHEN creating the params file
    file_creator.create(
        case_id=case_id,
        file_path=file_path,
        sample_sheet_path=sample_sheet_path,
    )

    # THEN the file should have been written with the expected content
    write_yaml_mock.assert_called_once_with(
        file_path=file_path,
        content={
            "Key": "Value",
            "analysis_type": "wgs",
            "input": Path("root/samplesheet.csv"),
            "outdir": Path("some_path"),
            "sample_id_map": Path("some_path/case_id_customer_internal_mapping.csv"),
            "save_mapped_as_cram": True,
            "target_bed_file": "bed_version.bed",
            "vcfanno_extra_resources": "some_path/managed_variants.vcf",
            "vep_filters_scout_fmt": "some_path/gene_panels.bed",
        },
    )
    # THEN auxiliary file is written and with the correct content
    write_csv_mock.assert_called_once_with(
        content=[["customer_id", "internal_id"], ["sample_name", "ACC"]],
        file_path=Path("some_path", f"{case_id}_customer_internal_mapping.csv"),
    )


@pytest.mark.parametrize("workflow", [Workflow.RNAFUSION, Workflow.TAXPROFILER])
def test_nextflow_params_file_creator(
    workflow: Workflow,
    params_file_scenario: dict,
    nextflow_sample_sheet_path: Path,
    nextflow_case_id: str,
):
    """Test that the Nextflow params file is written correctly."""
    file_path = Path("/root", "case_id", "file_name.yaml")
    # GIVEN a params file creator, an expected output and a mocked file writer
    file_creator, expected_content, write_yaml_mock = params_file_scenario[workflow]

    # WHEN creating the params file
    file_creator.create(
        case_id=nextflow_case_id,
        file_path=file_path,
        sample_sheet_path=nextflow_sample_sheet_path,
    )

    # THEN the file should have been written with the expected content
    write_yaml_mock.assert_called_once_with(file_path=file_path, content=expected_content)


def test_nextflow_config_file_content(
    nextflow_config_file_creator: NextflowConfigFileCreator,
    nextflow_case_id: str,
    nextflow_case_path: Path,
    expected_nextflow_config_content: str,
    mocker: MockerFixture,
):
    """Test that a Nextflow config file content is created correctly for all pipelines."""
    # GIVEN a Nextflow config content creator and a case id

    # GIVEN a writer mock
    write_mock: MagicMock = mocker.patch.object(config_file, "write_txt", return_value=None)

    # WHEN creating a Nextflow config file
    file_path = Path(nextflow_case_path, f"{nextflow_case_id}_nextflow_config.json")
    nextflow_config_file_creator.create(case_id=nextflow_case_id, file_path=file_path)

    # THEN the content of the file is the expected
    write_mock.assert_called_once_with(
        file_path=file_path, content=expected_nextflow_config_content
    )
