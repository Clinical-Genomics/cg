from pathlib import Path
from unittest.mock import Mock, create_autospec

import pytest
from housekeeper.store.models import File
from pyfakefs.fake_filesystem import FakeFilesystem
from pytest_mock import MockerFixture
from sqlalchemy.orm import Query

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.meta.upload.gisaid.gisaid import GisaidAPI
from cg.meta.upload.gisaid.models import GisaidSample
from cg.models.cg_config import CGConfig, EmailBaseSettings, GisaidConfig, MutantConfig
from cg.store.models import Sample
from cg.store.store import Store


@pytest.fixture
def housekeeper_api() -> HousekeeperAPI:
    return create_autospec(HousekeeperAPI)


@pytest.fixture
def status_db() -> Store:
    return create_autospec(Store)


@pytest.fixture
def cg_config(housekeeper_api: HousekeeperAPI, status_db: Store) -> CGConfig:
    return create_autospec(
        CGConfig,
        email_base_settings=EmailBaseSettings(
            sender_email="sender@scilifelab.se", smtp_server="smtp_server"
        ),
        housekeeper_api=housekeeper_api,
        gisaid=GisaidConfig(
            submitter="submitter",
            upload_password="upload_password",
            upload_cid="upload_cid",
            log_dir="log_dir",
            logwatch_email="logwatch@scilifelab.se",
        ),
        mutant=MutantConfig(binary_path="binary_path", conda_env="conda_env", root="root"),
        status_db=status_db,
    )


# TODO add pyfakefs to dependencies
def mock_completion_file(contents: str, fs) -> File:
    path = "/fake/completion_file.csv"
    fs.create_file(path, contents=contents)
    return create_autospec(File, full_path=path)


@pytest.fixture
def gisaid_log(fs, gisaid_log_contents: str) -> File:
    path = "/fake/gisad-log.log"
    fs.create_file(path, contents=gisaid_log_contents)
    return create_autospec(File, full_path=path)


@pytest.fixture
def expected_completion_dataframe() -> dict[str, dict[int, str]]:
    return {
        "GISAID_accession": {
            0: " EPI_ISL_75698657",
            1: " EPI_ISL_75698657",
            2: " EPI_ISL_75698658",
            3: " EPI_ISL_75698659",
            4: "",
            5: " EPI_ISL_75698661",
        },
        "provnummer": {
            0: "85CS900121",
            1: "85CS900121",
            2: "85CS900136",
            3: "85CS900117",
            4: "85CS900135",
            5: "85CS900145",
        },
        "urvalskriterium": {
            0: "Allmän övervakning",
            1: "Stickprov",
            2: "Allmän övervakning",
            3: "Allmän övervakning",
            4: "Allmän övervakning",
            5: "Allmän övervakning",
        },
    }


@pytest.fixture
def expected_updated_completion_file():
    return """provnummer,urvalskriterium,GISAID_accession
85CS900121,Allmän övervakning, EPI_ISL_20431427
85CS900121,Stickprov, EPI_ISL_20431427
85CS900136,Allmän övervakning, EPI_ISL_20431428
85CS900117,Allmän övervakning, EPI_ISL_20431429
85CS900135,Allmän övervakning, EPI_ISL_20431430
85CS900145,Allmän övervakning, EPI_ISL_20431431
"""


# def test_get_completion_dataframe(
#     cg_config: CGConfig,
#     completion_file_original_contents: str,
#     expected_completion_dataframe: dict[str, dict[int, str]],
#     fs,
# ):
#     completion_file = mock_completion_file(completion_file_original_contents, fs=fs)
#     gisaid_api = GisaidAPI(config=cg_config)

#     data_frame: DataFrame = gisaid_api.get_completion_dataframe(completion_file=completion_file)

#     assert data_frame.to_dict() == expected_completion_dataframe


def test_get_completion_dict(
    cg_config: CGConfig,
    completion_file_original_contents: str,
    expected_completion_dataframe: dict[str, dict[int, str]],
    fs: FakeFilesystem,
):
    completion_file = mock_completion_file(completion_file_original_contents, fs=fs)
    gisaid_api = GisaidAPI(config=cg_config)

    dict = gisaid_api.get_completion_dict(completion_file=completion_file)

    assert dict == expected_completion_dataframe


def test_get_gisaid_sample_list(
    cg_config: CGConfig,
    completion_file_original_contents: str,
    fs: FakeFilesystem,
    housekeeper_api: HousekeeperAPI,
    status_db: Store,
):
    completion_file = mock_completion_file(completion_file_original_contents, fs=fs)
    housekeeper_api.get_file_from_latest_version = Mock(return_value=completion_file)

    status_db.get_sample_by_name = lambda name: Sample(name=name)
    gisaid_api = GisaidAPI(config=cg_config)

    sample_list: list[Sample] = gisaid_api.get_gisaid_sample_list("case_id")
    assert [sample.name for sample in sample_list] == [
        "85CS900121",
        "85CS900136",
        "85CS900117",
        "85CS900135",
        "85CS900145",
    ]


def test_update_completion_file(
    cg_config: CGConfig,
    completion_file_original_contents: str,
    expected_updated_completion_file: str,
    fs: FakeFilesystem,
    gisaid_log: File,
    housekeeper_api: HousekeeperAPI,
):
    completion_file: File = mock_completion_file(completion_file_original_contents, fs=fs)
    housekeeper_api.get_file_from_latest_version = Mock(return_value=completion_file)

    get_files_query = create_autospec(Query)
    get_files_query.first = Mock(return_value=gisaid_log)
    housekeeper_api.get_files = Mock(return_value=get_files_query)

    gisaid_api = GisaidAPI(config=cg_config)

    gisaid_api.update_completion_file("case_id")

    assert Path(completion_file.full_path).read_text() == expected_updated_completion_file


def test_update_completion_file_sample_not_in_gisaid_log(
    cg_config: CGConfig,
    completion_file_accession_not_in_log: str,
    fs: FakeFilesystem,
    gisaid_log: File,
    housekeeper_api: HousekeeperAPI,
):
    completion_file: File = mock_completion_file(
        contents=completion_file_accession_not_in_log, fs=fs
    )
    housekeeper_api.get_file_from_latest_version = Mock(return_value=completion_file)

    get_files_query = create_autospec(Query)
    get_files_query.first = Mock(return_value=gisaid_log)
    housekeeper_api.get_files = Mock(return_value=get_files_query)

    gisaid_api = GisaidAPI(config=cg_config)

    with pytest.raises(KeyError):
        gisaid_api.update_completion_file("case_id")


def test_create_gisaid_csv(
    cg_config: CGConfig, housekeeper_api: HousekeeperAPI, fs: FakeFilesystem
):
    housekeeper_api.get_file_from_latest_version = Mock(return_value=None)
    fs.create_dir("root/case_id/results")
    samples: list[GisaidSample] = [
        GisaidSample(
            case_id="case_id",
            cg_lims_id="cg_lims_id",
            submitter="submitter",
            region="region",
            region_code="region_code",
            fn="fn",
            covv_collection_date="2026-08-04",
            covv_subm_sample_id="covv_subm_sample_id",
        )
    ]

    gisaid_api = GisaidAPI(config=cg_config)
    gisaid_api.create_gisaid_csv(gisaid_samples=samples, case_id="case_id")

    assert (
        Path("root/case_id/results/case_id.csv").read_text()
        == "submitter,fn,covv_virus_name,covv_type,covv_passage,covv_collection_date,covv_location,"
        "covv_host,covv_gender,covv_patient_age,covv_patient_status,covv_seq_technology,"
        "covv_orig_lab,covv_orig_lab_addr,covv_subm_sample_id,covv_subm_lab,covv_subm_lab_addr,"
        "covv_authors,covv_specimen,covv_outbreak,covv_add_host_info,covv_add_location,"
        "covv_provider_sample_id,covv_last_vaccinated,covv_treatment,covv_assembly_method,"
        "covv_coverage\nsubmitter,fn,hCoV-19/Sweden/region_code_SE100_covv_subm_sample_id/2026,"
        "betacoronavirus,Original,2026-08-04,Europe/Sweden/region,Human,unknown,unknown,unknown,"
        "Illumina NovaSeq,,,region_code_SE100_covv_subm_sample_id,Karolinska University Hospital,"
        '"171 76 Stockholm, Sweden","Jan Albert ,Tobias Allander ,Sandra Broddesson ,'
        "Robert Dyrdak ,Martin Ekman ,Lynda Eneh ,Shambhu Ganeshappa Aralaguppe ,"
        "Natalija Gerasimcik ,Karina Hentrich ,Annika Tiveljung Lindell ,Valtteri Wirta ,"
        'Zhibing Yun",,,,,,,,,\n'
    )


def test_upload_all_samples_already_uploaded(
    cg_config: CGConfig,
    completion_file_original_contents_all_uploaded: str,
    fs: FakeFilesystem,
    housekeeper_api: HousekeeperAPI,
    mocker: MockerFixture,
):
    completion_file: File = mock_completion_file(
        completion_file_original_contents_all_uploaded, fs=fs
    )
    # GIVEN a completion file where all the samples have been uploaded
    housekeeper_api.get_file_from_latest_version = Mock(return_value=completion_file)

    gisaid_api = GisaidAPI(config=cg_config)

    create_spy: Mock = mocker.spy(gisaid_api, "create_gisaid_files_in_housekeeper")
    upload_spy: Mock = mocker.spy(gisaid_api, "upload_results_to_gisaid")
    update_spy: Mock = mocker.spy(gisaid_api, "update_completion_file")

    gisaid_api.upload("case_id")

    create_spy.assert_not_called()
    upload_spy.assert_not_called()
    update_spy.assert_not_called()


def test_upload_all_samples_not_already_uploaded(
    cg_config: CGConfig,
    completion_file_original_contents_not_all_uploaded: str,
    fs: FakeFilesystem,
    housekeeper_api: HousekeeperAPI,
    mocker: MockerFixture,
):
    completion_file: File = mock_completion_file(
        contents=completion_file_original_contents_not_all_uploaded, fs=fs
    )
    housekeeper_api.get_file_from_latest_version = Mock(return_value=completion_file)

    gisaid_api = GisaidAPI(config=cg_config)

    create_mock: Mock = mocker.patch.object(gisaid_api, "create_gisaid_files_in_housekeeper")
    upload_mock: Mock = mocker.patch.object(gisaid_api, "upload_results_to_gisaid")
    update_mock: Mock = mocker.patch.object(gisaid_api, "update_completion_file")

    gisaid_api.upload("case_id")

    create_mock.assert_called_once_with(case_id="case_id")
    upload_mock.assert_called_once_with(case_id="case_id")
    update_mock.assert_called_once_with(case_id="case_id")


def test_upload_all_no_sars_samples(
    cg_config: CGConfig,
    completion_file_no_sars: str,
    fs: FakeFilesystem,
    housekeeper_api: HousekeeperAPI,
    mocker: MockerFixture,
):
    completion_file: File = mock_completion_file(contents=completion_file_no_sars, fs=fs)
    housekeeper_api.get_file_from_latest_version = Mock(return_value=completion_file)

    gisaid_api = GisaidAPI(config=cg_config)

    create_spy: Mock = mocker.spy(gisaid_api, "create_gisaid_files_in_housekeeper")
    upload_spy: Mock = mocker.spy(gisaid_api, "upload_results_to_gisaid")
    update_spy: Mock = mocker.spy(gisaid_api, "update_completion_file")

    gisaid_api.upload("case_id")

    create_spy.assert_not_called()
    upload_spy.assert_not_called()
    update_spy.assert_not_called()
