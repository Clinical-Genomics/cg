from pathlib import Path
from unittest.mock import Mock, create_autospec

import pytest
from mock import ANY
from pytest_mock import MockerFixture

from cg.apps.lims.api import LimsAPI
from cg.constants.constants import BedVersionGenomeVersion
from cg.constants.priority import Priority
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.models.cg_config import GCNVCallerFiles, VerifybamidSvdFiles, VerifybamidSvdFilesSet
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file import (
    raredisease_params_file_creator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.raredisease_params_file_creator import (
    RarediseaseParamsFileCreator,
)
from cg.store.models import BedVersion, Case, Sample
from cg.store.store import Store
from tests.matchers import DictContaining, DictNotContaining
from tests.typed_mock import TypedMock, create_typed_mock


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
def gcnvcaller_files() -> dict[str, GCNVCallerFiles]:
    return {
        "twistexomecomprehensive_10.2_hg38_design.bed": GCNVCallerFiles(
            gcnvcaller_model=Path("tyra", "bananks"),
            ploidy_model=Path("tom", "bananks"),
            readcount_intervals=Path("richard", "banankins"),
        )
    }


@pytest.fixture
def wgs_sample() -> Sample:
    sample = create_autospec(
        Sample,
        from_sample=None,
        internal_id="ACC",
        prep_category=SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING,
    )
    sample.name = "sample_name"
    return sample


@pytest.mark.parametrize(
    "expected_bed_short_name, lims_capture_kit",
    [
        (Path("/some/full/path/bed_version.bed"), "target_bed_shortname_123"),
        (Path("/some/full/path/default.bed"), None),
    ],
    ids=["Capture kit is in LIMS", "Capture kit not in LIMS"],
)
def test_create_on_lims_capture_kit_availability(
    lims_capture_kit: str | None,
    expected_bed_short_name: str,
    gcnvcaller_files: dict[str, GCNVCallerFiles],
    verifybamid_files_set: VerifybamidSvdFilesSet,
    mocker: MockerFixture,
):
    # GIVEN a file path
    file_path = Path("some_path", "file_name.yaml")

    # GIVEN case id
    case_id = "case_id"

    # GIVEN a store containing a case with a linked sample. Also contains a bed version.
    super_sample = create_autospec(
        Sample,
        from_sample=None,
        internal_id="ACC",
        prep_category=SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING,
    )
    super_sample.name = "sample_name"
    case = create_autospec(Case, internal_id=case_id, samples=[super_sample])
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
        default_target_bed="default.bed",
        gcnvcaller_files=gcnvcaller_files,
        verifybamid_files_set=verifybamid_files_set,
        store=store_mock,
        references_directory=Path("/some/full/path/"),
        lims=lims,
        params="Path_to_file.yaml",
    )

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
            "skip_tools": "germlinecnvcaller",
            "target_bed": expected_bed_short_name,
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


def test_create_wgs(
    gcnvcaller_files: dict[str, GCNVCallerFiles],
    verifybamid_files_set: VerifybamidSvdFilesSet,
    mocker: MockerFixture,
):
    # GIVEN a file path
    file_path = Path("some_path", "file_name.yaml")

    # GIVEN case id
    case_id = "case_id"

    # GIVEN a store containing a case with a linked sample. Also contains a bed version.
    super_sample = create_autospec(
        Sample,
        from_sample=None,
        internal_id="ACC",
        prep_category=SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING,
    )
    super_sample.name = "sample_name"
    case = create_autospec(Case, internal_id=case_id, samples=[super_sample])
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
        default_target_bed="default.bed",
        gcnvcaller_files=gcnvcaller_files,
        verifybamid_files_set=verifybamid_files_set,
        store=store_mock,
        references_directory=Path("/some/full/path/"),
        lims=lims,
        params="Path_to_file.yaml",
    )

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
            "skip_tools": "germlinecnvcaller",
            "sample_id_map": Path("some_path/case_id_customer_internal_mapping.csv"),
            "target_bed": ANY,
            "vcfanno_extra_resources": "some_path/managed_variants.vcf",
            "vep_filters_scout_fmt": "some_path/gene_panels.bed",
            "verifybamid_svd_bed": Path("some/sleeping_quarters.bed"),
            "verifybamid_svd_mu": Path("some/cow.mu"),
            "verifybamid_svd_ud": Path("some/department_of_external_affairs.UD"),
        },
    )
    # THEN auxiliary file is written and with the correct content
    write_csv_mock.assert_called_once_with(
        content=[["customer_id", "internal_id"], ["sample_name", "ACC"]],
        file_path=Path("some_path", f"{case_id}_customer_internal_mapping.csv"),
    )


def test_create_wes_gcnvcaller_included(
    gcnvcaller_files: dict[str, GCNVCallerFiles],
    verifybamid_files_set: VerifybamidSvdFilesSet,
    mocker: MockerFixture,
):
    # GIVEN a file path
    file_path = Path("some_path", "file_name.yaml")

    # GIVEN case id
    case_id = "case_id"

    # GIVEN a store containing a case with a linked sample. Also contains a bed version.
    super_sample = create_autospec(
        Sample,
        from_sample=None,
        internal_id="ACC",
        prep_category=SeqLibraryPrepCategory.WHOLE_EXOME_SEQUENCING,
    )
    super_sample.name = "sample_name"
    case = create_autospec(Case, internal_id=case_id, samples=[super_sample])
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

    # GIVEN a params file creator
    file_creator = RarediseaseParamsFileCreator(
        default_target_bed="default.bed",
        gcnvcaller_files=gcnvcaller_files,
        verifybamid_files_set=verifybamid_files_set,
        references_directory=Path("some_path"),
        store=store_mock,
        lims=lims,
        params="Path_to_file.yaml",
    )

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
            "target_bed": ANY,
            "vcfanno_extra_resources": "some_path/managed_variants.vcf",
            "vep_filters_scout_fmt": "some_path/gene_panels.bed",
            "verifybamid_svd_bed": Path("some/sleeping_quarters.exome.bed"),
            "verifybamid_svd_mu": Path("some/cow.exome.mu"),
            "verifybamid_svd_ud": Path("some/department_of_external_affairs.exome.UD"),
        },
    )

    # THEN auxiliary file is written and with the correct content
    write_csv_mock.assert_called_once_with(
        content=[["customer_id", "internal_id"], ["sample_name", "ACC"]],
        file_path=Path("some_path", f"{case_id}_customer_internal_mapping.csv"),
    )


def test_create_wes_gcnvcaller_bed_version_does_not_match(
    gcnvcaller_files: dict[str, GCNVCallerFiles],
    verifybamid_files_set: VerifybamidSvdFilesSet,
    mocker: MockerFixture,
):
    # GIVEN a file path
    file_path = Path("some_path", "file_name.yaml")

    # GIVEN case id
    case_id = "case_id"

    # GIVEN a store containing a case with a linked sample. Also contains a bed version.
    super_sample = create_autospec(
        Sample,
        from_sample=None,
        internal_id="ACC",
        prep_category=SeqLibraryPrepCategory.WHOLE_EXOME_SEQUENCING,
    )
    super_sample.name = "sample_name"
    case = create_autospec(Case, internal_id=case_id, samples=[super_sample])
    store_mock: Store = create_autospec(Store)
    store_mock.get_samples_by_case_id = Mock(return_value=[super_sample])
    store_mock.get_case_by_internal_id_strict = Mock(return_value=case)
    store_mock.get_bed_version_by_short_name_and_genome_version_strict = Mock(
        return_value=create_autospec(BedVersion, filename="non-matching_bed_version.bed")
    )

    # GIVEN that Lims returns a bed shortname
    lims = create_autospec(LimsAPI)
    lims.capture_kit = Mock(return_value="target_bed_shortname_123")

    # GIVEN a params file creator
    file_creator = RarediseaseParamsFileCreator(
        default_target_bed="default.bed",
        gcnvcaller_files=gcnvcaller_files,
        verifybamid_files_set=verifybamid_files_set,
        references_directory=Path("/any/path"),
        store=store_mock,
        lims=lims,
        params="Path_to_file.yaml",
    )

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
            "skip_tools": "germlinecnvcaller",
            "target_bed": ANY,
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
    "priority, expected_dict_contents",
    [
        (Priority.express, DictContaining({"manta_config": "/manta/config/path.ini"})),
        (Priority.standard, DictNotContaining({"manta_config": ANY})),
    ],
    ids=["Express case", "Standard case"],
)
def test_create_manta_config_depends_on_priority(
    priority: Priority,
    expected_dict_contents: DictContaining | DictNotContaining,
    gcnvcaller_files: dict[str, GCNVCallerFiles],
    verifybamid_files_set: VerifybamidSvdFilesSet,
    wgs_sample: Sample,
    mocker: MockerFixture,
) -> None:
    # GIVEN a case with the given priority
    case = create_autospec(Case, samples=[wgs_sample], priority=priority)
    store: TypedMock[Store] = create_typed_mock(Store)
    store.as_mock.get_samples_by_case_id = Mock(return_value=[wgs_sample])
    store.as_mock.get_case_by_internal_id_strict = Mock(return_value=case)

    # GIVEN that no capture kit is found in LIMS
    lims: TypedMock[LimsAPI] = create_typed_mock(LimsAPI)
    lims.as_mock.capture_kit = Mock(return_value=None)

    # GIVEN a params file creator
    file_creator = RarediseaseParamsFileCreator(
        default_target_bed="default.bed",
        gcnvcaller_files=gcnvcaller_files,
        verifybamid_files_set=verifybamid_files_set,
        references_directory=Path("/any/path"),
        store=store.as_type,
        lims=lims.as_type,
        params="Path_to_file.yaml",
    )

    # GIVEN IO is mocked
    write_yaml_mock = mocker.patch.object(
        raredisease_params_file_creator, "write_yaml_nextflow_style"
    )
    mocker.patch.object(raredisease_params_file_creator, "write_csv")
    mocker.patch.object(
        raredisease_params_file_creator, "read_yaml", return_value={"workflow": "parameter"}
    )

    # WHEN creating the params file
    file_creator.create(
        case_id="case_id",
        file_path=Path("some_path", "file_name.yaml"),
        sample_sheet_path=Path("root", "samplesheet.csv"),
    )

    # THEN the manta config is only included for express cases
    write_yaml_mock.assert_called_once_with(file_path=ANY, content=expected_dict_contents)
