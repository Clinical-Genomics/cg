from pathlib import Path
from unittest.mock import Mock, create_autospec

import pytest
from housekeeper.store.models import File
from pandas import DataFrame
from sqlalchemy.orm import Query

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.meta.upload.gisaid.gisaid import GisaidAPI
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
@pytest.fixture
def completion_file(completion_file_original_contents, fs) -> File:
    path = "/fake/completion_file.csv"
    fs.create_file(path, contents=completion_file_original_contents)
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
            1: " EPI_ISL_75698658",
            2: " EPI_ISL_75698659",
            3: " EPI_ISL_75698660",
            4: " EPI_ISL_75698661",
        },
        "provnummer": {
            0: "85CS900121",
            1: "85CS900136",
            2: "85CS900117",
            3: "85CS900135",
            4: "85CS900145",
        },
        "urvalskriterium": {
            0: "Allmän övervakning",
            1: "Allmän övervakning",
            2: "Allmän övervakning",
            3: "Allmän övervakning",
            4: "Allmän övervakning",
        },
    }


@pytest.fixture
def expected_updated_completion_file():
    return """provnummer,urvalskriterium,GISAID_accession
85CS900121,Allmän övervakning, EPI_ISL_20431427
85CS900136,Allmän övervakning, EPI_ISL_20431428
85CS900117,Allmän övervakning, EPI_ISL_20431429
85CS900135,Allmän övervakning, EPI_ISL_20431430
85CS900145,Allmän övervakning, EPI_ISL_20431431
"""


def test_get_completion_dataframe(
    cg_config: CGConfig,
    completion_file: File,
    expected_completion_dataframe: dict[str, dict[int, str]],
):
    gisaid_api = GisaidAPI(config=cg_config)

    data_frame: DataFrame = gisaid_api.get_completion_dataframe(completion_file=completion_file)

    assert data_frame.to_dict() == expected_completion_dataframe


def test_get_completion_dict(
    cg_config: CGConfig,
    completion_file: File,
    expected_completion_dataframe: dict[str, dict[int, str]],
):
    gisaid_api = GisaidAPI(config=cg_config)

    dict = gisaid_api.get_completion_dict(completion_file=completion_file)

    assert dict == expected_completion_dataframe


def test_get_gisaid_sample_list(
    cg_config: CGConfig, completion_file: File, housekeeper_api: HousekeeperAPI, status_db: Store
):
    housekeeper_api.get_file_from_latest_version = Mock(return_value=completion_file)
    status_db.get_sample_by_name = lambda name: Sample(name=name)
    gisaid_api = GisaidAPI(config=cg_config)

    sample_list: list[Sample] = gisaid_api.get_gisaid_sample_list("case_id")
    assert ["85CS900121", "85CS900136", "85CS900117", "85CS900135", "85CS900145"] == [
        sample.name for sample in sample_list
    ]


def test_update_completion_file(
    cg_config: CGConfig,
    completion_file: File,
    expected_updated_completion_file: str,
    gisaid_log: File,
    housekeeper_api: HousekeeperAPI,
):
    housekeeper_api.get_file_from_latest_version = Mock(return_value=completion_file)

    get_files_query = create_autospec(Query)
    get_files_query.first = Mock(return_value=gisaid_log)
    housekeeper_api.get_files = Mock(return_value=get_files_query)

    gisaid_api = GisaidAPI(config=cg_config)

    gisaid_api.update_completion_file("case_id")

    assert Path(completion_file.full_path).read_text() == expected_updated_completion_file
