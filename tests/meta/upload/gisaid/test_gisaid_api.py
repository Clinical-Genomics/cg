from unittest.mock import create_autospec

import pytest
from housekeeper.store.models import File
from pandas import DataFrame

from cg.meta.upload.gisaid.gisaid import GisaidAPI
from cg.models.cg_config import CGConfig, EmailBaseSettings, GisaidConfig, MutantConfig


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


def test_get_completion_dataframe(expected_completion_dataframe: dict[str, dict[int, str]]):
    cg_config: CGConfig = create_autospec(
        CGConfig,
        email_base_settings=EmailBaseSettings(
            sender_email="sender@scilifelab.se", smtp_server="smtp_server"
        ),
        gisaid=GisaidConfig(
            submitter="submitter",
            upload_password="upload_password",
            upload_cid="upload_cid",
            log_dir="log_dir",
            logwatch_email="logwatch@scilifelab.se",
        ),
        mutant=MutantConfig(binary_path="binary_path", conda_env="conda_env", root="root"),
    )
    gisaid_api = GisaidAPI(config=cg_config)
    file = create_autospec(File)
    file.full_path = "tests/meta/upload/gisaid/fixtures/completion_file.csv"

    data_frame: DataFrame = gisaid_api.get_completion_dataframe(completion_file=file)

    assert data_frame.to_dict() == expected_completion_dataframe


def test_get_completion_dict(expected_completion_dataframe: dict[str, dict[int, str]]):
    cg_config: CGConfig = create_autospec(
        CGConfig,
        email_base_settings=EmailBaseSettings(
            sender_email="sender@scilifelab.se", smtp_server="smtp_server"
        ),
        gisaid=GisaidConfig(
            submitter="submitter",
            upload_password="upload_password",
            upload_cid="upload_cid",
            log_dir="log_dir",
            logwatch_email="logwatch@scilifelab.se",
        ),
        mutant=MutantConfig(binary_path="binary_path", conda_env="conda_env", root="root"),
    )
    gisaid_api = GisaidAPI(config=cg_config)
    file = create_autospec(File)
    file.full_path = "tests/meta/upload/gisaid/fixtures/completion_file.csv"

    dict = gisaid_api.get_completion_dict(completion_file=file)

    assert dict == expected_completion_dataframe
