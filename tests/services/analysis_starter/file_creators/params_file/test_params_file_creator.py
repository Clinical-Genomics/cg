from pathlib import Path
from unittest.mock import Mock, create_autospec

import pytest
from mock import ANY
from pytest_mock import MockerFixture

from cg.apps.lims.api import LimsAPI
from cg.constants.constants import BedVersionGenomeVersion, Workflow
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.models.cg_config import GCNVCallerFiles, VerifybamidSvdFiles, VerifybamidSvdFilesSet
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file import (
    raredisease_params_file_creator,
    tomte_params_file_creator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.abstract import (
    ParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.raredisease_params_file_creator import (
    RarediseaseParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.tomte_params_file_creator import (
    TomteParamsFileCreator,
)
from cg.store.models import BedVersion, Case, Sample
from cg.store.store import Store


@pytest.fixture
def verifybamid_files_set() -> VerifybamidSvdFilesSet:
    wes_resources = VerifybamidSvdFiles(
        bed=Path("some/sleeping_quarters.exome.bed"),
        mu=Path("some/cow.exome.mu"),
        ud=Path("some/department_of_external_affairs.exome.UD"),
    )
    wgs_resources = VerifybamidSvdFiles(
        bed=Path("some/sleeping_quarters.bed"),
        mu=Path("some/cow.mu"),
        ud=Path("some/department_of_external_affairs.UD"),
    )
    return VerifybamidSvdFilesSet(wes=wes_resources, wgs=wgs_resources)


@pytest.fixture
def gcnvcaller_files() -> GCNVCallerFiles:
    return GCNVCallerFiles(
        gcnvcaller_model=Path("tyra", "bananks"),
        ploidy_model=Path("tom", "bananks"),
        readcount_intervals=Path("richard", "banankins"),
    )


@pytest.mark.parametrize(
    "expected_bed_short_name, lims_capture_kit",
    [("bed_version.bed", "target_bed_shortname_123"), ("", None)],
    ids=["Capture kit is in LIMS", "Capture kit not in LIMS"],
)
def test_raredisease_params_file_creator_on_lims_capture_kit_availability(
    lims_capture_kit: str | None,
    expected_bed_short_name: str,
    verifybamid_files_set: VerifybamidSvdFilesSet,
    mocker: MockerFixture,
):
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
    store_mock.get_bed_version_by_short_name_and_genome_version_strict = (
        lambda short_name, genome_version: (
            create_autospec(BedVersion, filename="bed_version.bed")
            if short_name == "target_bed_shortname_123"
            and genome_version == BedVersionGenomeVersion.HG38
            else create_autospec(BedVersion)
        )
    )

    # GIVEN that Lims returns a bed shortname
    lims = create_autospec(LimsAPI)
    lims.capture_kit = Mock(return_value=lims_capture_kit)

    # GIVEN a params file creator
    file_creator = RarediseaseParamsFileCreator(
        verifybamid_files_set=verifybamid_files_set,
        store=store_mock,
        lims=lims,
        params="Path_to_file.yaml",
    )

    # GIVEN case id
    case_id = "case_id"

    # GIVEN sample sheet path
    sample_sheet_path = Path("root", "samplesheet.csv")

    # GIVEN IO is mocked
    write_yaml_mock = mocker.patch.object(
        raredisease_params_file_creator, "write_yaml_nextflow_style"
    )
    write_csv_mock = mocker.patch.object(raredisease_params_file_creator, "write_csv")
    mocker.patch.object(raredisease_params_file_creator, "read_yaml", return_value={"Key": "Value"})

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
            "target_bed_file": expected_bed_short_name,
            "vcfanno_extra_resources": "some_path/managed_variants.vcf",
            "vep_filters_scout_fmt": "some_path/gene_panels.bed",
            "verifybamid_svd_bed": ANY,
            "verifybamid_svd_mu": ANY,
            "verifybamid_svd_ud": ANY,
        },
    )
    # THEN auxiliary file is written and with the correct content
    write_csv_mock.assert_called_once_with(
        content=[["customer_id", "internal_id"], ["sample_name", "ACC"]],
        file_path=Path("some_path", f"{case_id}_customer_internal_mapping.csv"),
    )


@pytest.mark.parametrize(
    "prep_category, expected_bed, expected_mu, expected_ud",
    [
        (
            SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING,
            Path("some/sleeping_quarters.bed"),
            Path("some/cow.mu"),
            Path("some/department_of_external_affairs.UD"),
        ),
        (
            SeqLibraryPrepCategory.WHOLE_EXOME_SEQUENCING,
            Path("some/sleeping_quarters.exome.bed"),
            Path("some/cow.exome.mu"),
            Path("some/department_of_external_affairs.exome.UD"),
        ),
    ],
)
def test_raredisease_params_file_creator_different_prep_categories(
    expected_bed: Path,
    expected_mu: Path,
    expected_ud: Path,
    prep_category: SeqLibraryPrepCategory,
    verifybamid_files_set: VerifybamidSvdFilesSet,
    mocker: MockerFixture,
):
    # GIVEN a file path
    file_path = Path("some_path", "file_name.yaml")

    # GIVEN a store containing a case with a linked sample. Also contains a bed version.
    super_sample = create_autospec(
        Sample,
        from_sample=None,
        internal_id="ACC",
        prep_category=prep_category,
    )
    super_sample.name = "sample_name"
    case = create_autospec(Case, samples=[super_sample])
    store_mock: Store = create_autospec(Store)
    store_mock.get_samples_by_case_id = Mock(return_value=[super_sample])
    store_mock.get_case_by_internal_id_strict = Mock(return_value=case)
    store_mock.get_bed_version_by_short_name_and_genome_version_strict = Mock(
        return_value=create_autospec(BedVersion, filename="bed_version.bed")
    )

    # GIVEN that Lims returns a bed shortname
    lims = create_autospec(LimsAPI)
    lims.capture_kit = Mock(return_value="target_bed_shortname_123")

    # GIVEN a params file creator

    file_creator = RarediseaseParamsFileCreator(
        verifybamid_files_set=verifybamid_files_set,
        store=store_mock,
        lims=lims,
        params="Path_to_file.yaml",
    )

    # GIVEN case id
    case_id = "case_id"

    # GIVEN sample sheet path
    sample_sheet_path = Path("root", "samplesheet.csv")

    # GIVEN IO is mocked
    write_yaml_mock = mocker.patch.object(
        raredisease_params_file_creator, "write_yaml_nextflow_style"
    )
    write_csv_mock = mocker.patch.object(raredisease_params_file_creator, "write_csv")
    mocker.patch.object(raredisease_params_file_creator, "read_yaml", return_value={"Key": "Value"})

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
            "analysis_type": prep_category,
            "input": Path("root/samplesheet.csv"),
            "outdir": Path("some_path"),
            "sample_id_map": Path("some_path/case_id_customer_internal_mapping.csv"),
            "save_mapped_as_cram": True,
            "target_bed_file": ANY,
            "vcfanno_extra_resources": "some_path/managed_variants.vcf",
            "vep_filters_scout_fmt": "some_path/gene_panels.bed",
            "verifybamid_svd_bed": expected_bed,
            "verifybamid_svd_mu": expected_mu,
            "verifybamid_svd_ud": expected_ud,
        },
    )
    # THEN auxiliary file is written and with the correct content
    write_csv_mock.assert_called_once_with(
        content=[["customer_id", "internal_id"], ["sample_name", "ACC"]],
        file_path=Path("some_path", f"{case_id}_customer_internal_mapping.csv"),
    )


def test_raredisease_params_file_creator_wes_gcnvcaller_included(
    verifybamid_files_set: VerifybamidSvdFilesSet,
    mocker: MockerFixture,
):
    # GIVEN a file path
    file_path = Path("some_path", "file_name.yaml")

    # GIVEN a store containing a case with a linked sample. Also contains a bed version.
    super_sample = create_autospec(
        Sample,
        from_sample=None,
        internal_id="ACC",
        prep_category=SeqLibraryPrepCategory.WHOLE_EXOME_SEQUENCING,
    )
    super_sample.name = "sample_name"
    case = create_autospec(Case, samples=[super_sample])
    store_mock: Store = create_autospec(Store)
    store_mock.get_samples_by_case_id = Mock(return_value=[super_sample])
    store_mock.get_case_by_internal_id_strict = Mock(return_value=case)
    store_mock.get_bed_version_by_short_name_and_genome_version_strict = Mock(
        return_value=create_autospec(
            BedVersion, filename="twistexomecomprehensive_10.2_hg38_design.bed"
        )
    )

    # GIVEN that Lims returns a bed shortname
    lims = create_autospec(LimsAPI)
    lims.capture_kit = Mock(return_value="target_bed_shortname_123")

    gcnvcaller_files = GCNVCallerFiles(
        gcnvcaller_model=Path("tyra", "bananks"),
        ploidy_model=Path("tom", "bananks"),
        readcount_intervals=Path("richard", "banankins"),
    )

    # GIVEN a params file creator
    file_creator = RarediseaseParamsFileCreator(
        gcnvcaller_files={"twistexomecomprehensive_10.2_hg38_design.bed": gcnvcaller_files},
        verifybamid_files_set=verifybamid_files_set,
        store=store_mock,
        lims=lims,
        params="Path_to_file.yaml",
    )

    # GIVEN case id
    case_id = "case_id"

    # GIVEN sample sheet path
    sample_sheet_path = Path("root", "samplesheet.csv")

    # GIVEN IO is mocked
    write_yaml_mock = mocker.patch.object(
        raredisease_params_file_creator, "write_yaml_nextflow_style"
    )
    write_csv_mock = mocker.patch.object(raredisease_params_file_creator, "write_csv")
    mocker.patch.object(raredisease_params_file_creator, "read_yaml", return_value={"Key": "Value"})

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
            "analysis_type": SeqLibraryPrepCategory.WHOLE_EXOME_SEQUENCING,
            "gcnvcaller_model": Path("tyra", "bananks"),
            "input": Path("root/samplesheet.csv"),
            "outdir": Path("some_path"),
            "ploidy_model": Path("tom/bananks"),
            "readcount_intervals": Path("richard/banankins"),
            "sample_id_map": Path("some_path/case_id_customer_internal_mapping.csv"),
            "save_mapped_as_cram": True,
            "skip_germlinecnvcaller": False,
            "target_bed_file": ANY,
            "vcfanno_extra_resources": "some_path/managed_variants.vcf",
            "vep_filters_scout_fmt": "some_path/gene_panels.bed",
            "verifybamid_svd_bed": ANY,
            "verifybamid_svd_mu": ANY,
            "verifybamid_svd_ud": ANY,
        },
    )
    # THEN auxiliary file is written and with the correct content
    write_csv_mock.assert_called_once_with(
        content=[["customer_id", "internal_id"], ["sample_name", "ACC"]],
        file_path=Path("some_path", f"{case_id}_customer_internal_mapping.csv"),
    )


def test_raredisease_params_file_creator_wes_gcnvcaller_bed_version_does_not_match(
    verifybamid_files_set: VerifybamidSvdFilesSet,
    mocker: MockerFixture,
):
    # GIVEN a file path
    file_path = Path("some_path", "file_name.yaml")

    # GIVEN a store containing a case with a linked sample. Also contains a bed version.
    super_sample = create_autospec(
        Sample,
        from_sample=None,
        internal_id="ACC",
        prep_category=SeqLibraryPrepCategory.WHOLE_EXOME_SEQUENCING,
    )
    super_sample.name = "sample_name"
    case = create_autospec(Case, samples=[super_sample])
    store_mock: Store = create_autospec(Store)
    store_mock.get_samples_by_case_id = Mock(return_value=[super_sample])
    store_mock.get_case_by_internal_id_strict = Mock(return_value=case)
    store_mock.get_bed_version_by_short_name_and_genome_version_strict = Mock(
        return_value=create_autospec(BedVersion, filename="non-matching_bed_version.bed")
    )

    # GIVEN that Lims returns a bed shortname
    lims = create_autospec(LimsAPI)
    lims.capture_kit = Mock(return_value="target_bed_shortname_123")

    gcnvcaller_files = GCNVCallerFiles(
        gcnvcaller_model=Path("tyra", "bananks"),
        ploidy_model=Path("tom", "bananks"),
        readcount_intervals=Path("richard", "banankins"),
    )

    # GIVEN a params file creator
    file_creator = RarediseaseParamsFileCreator(
        gcnvcaller_files={"twistexomecomprehensive_10.2_hg38_design.bed": gcnvcaller_files},
        verifybamid_files_set=verifybamid_files_set,
        store=store_mock,
        lims=lims,
        params="Path_to_file.yaml",
    )

    # GIVEN case id
    case_id = "case_id"

    # GIVEN sample sheet path
    sample_sheet_path = Path("root", "samplesheet.csv")

    # GIVEN IO is mocked
    write_yaml_mock = mocker.patch.object(
        raredisease_params_file_creator, "write_yaml_nextflow_style"
    )
    write_csv_mock = mocker.patch.object(raredisease_params_file_creator, "write_csv")
    mocker.patch.object(raredisease_params_file_creator, "read_yaml", return_value={"Key": "Value"})

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
            "analysis_type": SeqLibraryPrepCategory.WHOLE_EXOME_SEQUENCING,
            "input": Path("root/samplesheet.csv"),
            "outdir": Path("some_path"),
            "sample_id_map": Path("some_path/case_id_customer_internal_mapping.csv"),
            "save_mapped_as_cram": True,
            "skip_germlinecnvcaller": True,
            "target_bed_file": ANY,
            "vcfanno_extra_resources": "some_path/managed_variants.vcf",
            "vep_filters_scout_fmt": "some_path/gene_panels.bed",
            "verifybamid_svd_bed": ANY,
            "verifybamid_svd_mu": ANY,
            "verifybamid_svd_ud": ANY,
        },
    )
    # THEN auxiliary file is written and with the correct content
    write_csv_mock.assert_called_once_with(
        content=[["customer_id", "internal_id"], ["sample_name", "ACC"]],
        file_path=Path("some_path", f"{case_id}_customer_internal_mapping.csv"),
    )


def test_raredisease_params_file_creator_wgs(
    verifybamid_files_set: VerifybamidSvdFilesSet,
    mocker: MockerFixture,
):
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

    # GIVEN that Lims returns a bed shortname
    lims = create_autospec(LimsAPI)
    lims.capture_kit = Mock(return_value=None)

    # GIVEN a params file creator
    file_creator = RarediseaseParamsFileCreator(
        gcnvcaller_files={"twistexomecomprehensive_10.2_hg38_design.bed": gcnvcaller_files},
        verifybamid_files_set=verifybamid_files_set,
        store=store_mock,
        lims=lims,
        params="Path_to_file.yaml",
    )

    # GIVEN case id
    case_id = "case_id"

    # GIVEN sample sheet path
    sample_sheet_path = Path("root", "samplesheet.csv")

    # GIVEN IO is mocked
    write_yaml_mock = mocker.patch.object(
        raredisease_params_file_creator, "write_yaml_nextflow_style"
    )
    write_csv_mock = mocker.patch.object(raredisease_params_file_creator, "write_csv")
    mocker.patch.object(raredisease_params_file_creator, "read_yaml", return_value={"Key": "Value"})

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
            "analysis_type": SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING,
            "input": Path("root/samplesheet.csv"),
            "outdir": Path("some_path"),
            "sample_id_map": Path("some_path/case_id_customer_internal_mapping.csv"),
            "save_mapped_as_cram": True,
            "skip_germlinecnvcaller": True,
            "target_bed_file": ANY,
            "vcfanno_extra_resources": "some_path/managed_variants.vcf",
            "vep_filters_scout_fmt": "some_path/gene_panels.bed",
            "verifybamid_svd_bed": ANY,
            "verifybamid_svd_mu": ANY,
            "verifybamid_svd_ud": ANY,
        },
    )
    # THEN auxiliary file is written and with the correct content
    write_csv_mock.assert_called_once_with(
        content=[["customer_id", "internal_id"], ["sample_name", "ACC"]],
        file_path=Path("some_path", f"{case_id}_customer_internal_mapping.csv"),
    )


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


@pytest.mark.parametrize("workflow", [Workflow.NALLO, Workflow.RNAFUSION, Workflow.TAXPROFILER])
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
