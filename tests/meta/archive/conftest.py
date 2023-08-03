from datetime import datetime, timedelta
from pathlib import Path
from typing import List
from unittest import mock

import pytest

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.constants.archiving import ArchiveLocationsInUse
from cg.constants.constants import FileFormat
from cg.constants.subject import Gender
from cg.io.controller import WriteStream
from cg.meta.archive.archive import SpringArchiveAPI
from cg.meta.archive.ddn_dataflow import ROOT_TO_TRIM, DDNDataFlowApi, TransferData, TransferPayload
from cg.models.cg_config import DDNDataFlowConfig
from cg.store import Store
from cg.store.models import Customer, Sample
from requests import Response
from tests.store_helpers import StoreHelpers


@pytest.fixture(name="ddn_dataflow_config")
def fixture_ddn_dataflow_config(
    local_storage_repository: str, remote_storage_repository: str
) -> DDNDataFlowConfig:
    """Returns a mock DDN Dataflow config."""
    return DDNDataFlowConfig(
        database_name="test_db",
        user="test_user",
        password="DummyPassword",
        url=Path("some", "api", "url.com").as_posix(),
        local_storage=local_storage_repository,
        archive_repository=remote_storage_repository,
    )


@pytest.fixture(name="ddn_dataflow_api")
def fixture_ddn_dataflow_api(ddn_dataflow_config: DDNDataFlowConfig) -> DDNDataFlowApi:
    """Returns a DDNApi without tokens being set."""
    mock_ddn_auth_success_response = Response()
    mock_ddn_auth_success_response.status_code = 200
    mock_ddn_auth_success_response._content = WriteStream.write_stream_from_content(
        file_format=FileFormat.JSON,
        content={
            "access": "test_auth_token",
            "refresh": "test_refresh_token",
            "expire": (datetime.now() + timedelta(minutes=20)).timestamp(),
        },
    ).encode()
    with mock.patch(
        "cg.meta.archive.ddn_dataflow.APIRequest.api_request_from_content",
        return_value=mock_ddn_auth_success_response,
    ):
        return DDNDataFlowApi(ddn_dataflow_config)


@pytest.fixture(name="transfer_data")
def fixture_transfer_data(local_directory: Path, remote_path: Path) -> TransferData:
    """Return a TransferData object."""
    return TransferData(source=local_directory.as_posix(), destination=remote_path.as_posix())


@pytest.fixture(name="transfer_payload")
def fixture_transfer_payload(transfer_data: TransferData) -> TransferPayload:
    """Return a TransferPayload object containing two identical TransferData object.."""
    return TransferPayload(files_to_transfer=[transfer_data, transfer_data.copy(deep=True)])


@pytest.fixture(name="remote_path")
def fixture_remote_path() -> Path:
    """Returns a mock path."""
    return Path("/some", "place")


@pytest.fixture(name="local_directory")
def fixture_local_directory() -> Path:
    """Returns a mock path with /home as its root."""
    return Path(ROOT_TO_TRIM, "other", "place")


@pytest.fixture(name="trimmed_local_directory")
def fixture_trimmed_local_directory(local_directory: Path) -> Path:
    """Returns the trimmed local directory."""
    return Path(f"/{local_directory.relative_to(ROOT_TO_TRIM)}")


@pytest.fixture(name="local_storage_repository")
def fixture_local_storage_repository() -> str:
    """Returns a local storage repository."""
    return "local@storage:"


@pytest.fixture(name="remote_storage_repository")
def fixture_remote_storage_repository() -> str:
    """Returns a remote storage repository."""
    return "archive@repisitory:"


@pytest.fixture(name="full_remote_path")
def fixture_full_remote_path(remote_storage_repository: str, remote_path: Path) -> str:
    """Returns the merged remote repository and path."""
    return remote_storage_repository + remote_path.as_posix()


@pytest.fixture(name="full_local_path")
def fixture_full_local_path(local_storage_repository: str, trimmed_local_directory: Path) -> str:
    """Returns the merged local repository and trimmed path."""
    return local_storage_repository + trimmed_local_directory.as_posix()


@pytest.fixture(name="archive_store")
def fixture_archive_store(
    base_store: Store,
    helpers: StoreHelpers,
    sample_id,
    father_sample_id,
    mother_sample_id,
    sample_name,
) -> Store:
    """Returns a store with samples for both a DDN customer as well as a non-DDN customer."""
    customer_ddn: Customer = base_store.add_customer(
        internal_id="CustWithDDN",
        invoice_address="Baker Street 221B",
        invoice_reference="Sherlock Holmes",
        name="Sherlock Holmes",
        is_clinical=True,
        data_archive_location=ArchiveLocationsInUse.KAROLINSKA_BUCKET,
    )
    customer_without_ddn: Customer = base_store.add_customer(
        internal_id="CustWithoutDDN",
        invoice_address="Wallaby Way 42",
        invoice_reference="P Sherman",
        name="P Sherman",
        is_clinical=False,
        data_archive_location="PDC",
    )

    new_samples: List[Sample] = [
        base_store.add_sample(
            name=sample_name,
            sex=Gender.MALE,
            internal_id=sample_id,
        ),
        base_store.add_sample(
            name="sample_2_with_ddn_customer",
            sex=Gender.MALE,
            internal_id=mother_sample_id,
        ),
        base_store.add_sample(
            name="sample_without_ddn_customer",
            sex=Gender.MALE,
            internal_id=father_sample_id,
        ),
    ]
    new_samples[0].customer = customer_ddn
    new_samples[1].customer = customer_ddn
    new_samples[2].customer = customer_without_ddn
    external_app = base_store.get_application_by_tag("WGXCUSC000").versions[0]
    wgs_app = base_store.get_application_by_tag("WGSPCFC030").versions[0]
    for sample in new_samples:
        sample.application_version = external_app if "external" in sample.name else wgs_app
    base_store.session.add(customer_ddn)
    base_store.session.add(customer_without_ddn)
    base_store.session.add_all(new_samples)
    base_store.session.commit()
    return base_store


@pytest.fixture(name="spring_archive_api")
def fixture_spring_archive_api(
    populated_housekeeper_api: HousekeeperAPI,
    archive_store: Store,
    father_sample_id: str,
    helpers,
) -> SpringArchiveAPI:
    """Returns an ArchiveAPI with a populated housekeeper store and a DDNDataFlowApi.
    Also adds /home/ as a prefix for each SPRING file for the DDNDataFlowApi to accept them."""
    for spring_file in populated_housekeeper_api.files(tags=[SequencingFileTag.SPRING]):
        spring_file.path = f"/home/{spring_file.path}"
    populated_housekeeper_api.commit()
    return SpringArchiveAPI(
        housekeeper_api=populated_housekeeper_api,
        status_db=archive_store,
    )
