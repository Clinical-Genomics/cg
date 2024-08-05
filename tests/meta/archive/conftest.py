import http
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from unittest import mock

import pytest
from click.testing import CliRunner
from housekeeper.store.models import Bundle, File
from requests import Response

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.constants.archiving import ArchiveLocations
from cg.constants.constants import DataDelivery, FileFormat, Workflow
from cg.constants.subject import Sex
from cg.io.controller import WriteStream
from cg.meta.archive.archive import SpringArchiveAPI
from cg.meta.archive.ddn.constants import ROOT_TO_TRIM
from cg.meta.archive.ddn.ddn_data_flow_client import DDNDataFlowClient
from cg.meta.archive.ddn.models import AuthToken, MiriaObject, TransferPayload
from cg.meta.archive.models import FileAndSample
from cg.models.cg_config import CGConfig, DataFlowConfig
from cg.store.models import Case, Customer, Order, Sample
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


@pytest.fixture(name="ddn_dataflow_config")
def ddn_dataflow_config(
    local_storage_repository: str, remote_storage_repository: str
) -> DataFlowConfig:
    """Returns a mock DDN Dataflow config."""
    return DataFlowConfig(
        database_name="test_db",
        user="test_user",
        password="DummyPassword",
        url=Path("some", "api", "url.com").as_posix(),
        local_storage=local_storage_repository,
        archive_repository=remote_storage_repository,
    )


@pytest.fixture
def ok_miria_response(ok_response: Response):
    ok_response._content = b'{"jobId": "123"}'
    return ok_response


@pytest.fixture
def ok_miria_job_status_response(ok_response: Response):
    ok_response._content = b'{"id": "123", "status": "Completed"}'
    return ok_response


@pytest.fixture
def archive_request_json(
    remote_storage_repository: str, local_storage_repository: str, trimmed_local_path: str
) -> dict:
    return {
        "osType": "Unix/MacOS",
        "createFolder": True,
        "pathInfo": [
            {
                "destination": f"{remote_storage_repository}ADM1",
                "source": local_storage_repository + trimmed_local_path,
            }
        ],
        "metadataList": [],
        "settings": [],
    }


@pytest.fixture
def retrieve_request_json(
    remote_storage_repository: str, local_storage_repository: str, trimmed_local_path: str
) -> dict[str, Any]:
    """Returns the body for a retrieval http post towards the DDN Miria API."""
    return {
        "osType": "Unix/MacOS",
        "createFolder": False,
        "pathInfo": [
            {
                "destination": local_storage_repository
                + Path(trimmed_local_path).parent.as_posix(),
                "source": f"{remote_storage_repository}ADM1",
            }
        ],
        "metadataList": [],
        "settings": [],
    }


@pytest.fixture
def header_with_test_auth_token() -> dict:
    return {
        "Content-Type": "application/json",
        "accept": "application/json",
        "Authorization": "Bearer test_auth_token",
    }


@pytest.fixture
def miria_auth_token_response(ok_response: Response):
    ok_response._content = b'{"access": "test_auth_token", "expire":15, "test_refresh_token":""}'
    return ok_response


@pytest.fixture
def test_auth_token() -> AuthToken:
    return AuthToken(
        access="test_auth_token",
        expire=int((datetime.now() + timedelta(minutes=20)).timestamp()),
        refresh="test_refresh_token",
    )


@pytest.fixture
def archival_job_id() -> int:
    return 123


@pytest.fixture
def retrieval_job_id() -> int:
    return 124


@pytest.fixture
def ddn_dataflow_client(ddn_dataflow_config: DataFlowConfig) -> DDNDataFlowClient:
    """Returns a DDNApi without tokens being set."""
    mock_ddn_auth_success_response = Response()
    mock_ddn_auth_success_response.status_code = 200
    mock_ddn_auth_success_response._content = WriteStream.write_stream_from_content(
        file_format=FileFormat.JSON,
        content={
            "access": "test_auth_token",
            "refresh": "test_refresh_token",
            "expire": int((datetime.now() + timedelta(minutes=20)).timestamp()),
        },
    ).encode()
    with mock.patch(
        "cg.meta.archive.ddn.ddn_data_flow_client.APIRequest.api_request_from_content",
        return_value=mock_ddn_auth_success_response,
    ):
        return DDNDataFlowClient(ddn_dataflow_config)


@pytest.fixture
def miria_file_archive(local_directory: Path, remote_path: Path) -> MiriaObject:
    """Return a MiriaObject for archiving."""
    return MiriaObject(source=local_directory.as_posix(), destination=remote_path.as_posix())


@pytest.fixture
def file_and_sample(spring_archive_api: SpringArchiveAPI, sample_id: str):
    return FileAndSample(
        file=spring_archive_api.housekeeper_api.get_files(bundle=sample_id).first(),
        sample=spring_archive_api.status_db.get_sample_by_internal_id(sample_id),
    )


@pytest.fixture
def trimmed_local_path(spring_archive_api: SpringArchiveAPI, sample_id: str):
    file: File = spring_archive_api.housekeeper_api.get_files(bundle=sample_id).first()
    return file.path[5:]


@pytest.fixture
def miria_file_retrieve(local_directory: Path, remote_path: Path) -> MiriaObject:
    """Return a MiriaObject for retrieval."""
    return MiriaObject(source=remote_path.as_posix(), destination=local_directory.as_posix())


@pytest.fixture
def transfer_payload(miria_file_archive: MiriaObject) -> TransferPayload:
    """Return a TransferPayload object containing two identical MiriaObject object."""
    return TransferPayload(
        files_to_transfer=[miria_file_archive, miria_file_archive.model_copy(deep=True)]
    )


@pytest.fixture
def remote_path() -> Path:
    """Returns a mock path."""
    return Path("/some", "place")


@pytest.fixture
def local_directory() -> Path:
    """Returns a mock path with /home as its root."""
    return Path(ROOT_TO_TRIM, "other", "place")


@pytest.fixture
def trimmed_local_directory(local_directory: Path) -> Path:
    """Returns the trimmed local directory."""
    return Path(f"/{local_directory.relative_to(ROOT_TO_TRIM)}")


@pytest.fixture
def local_storage_repository() -> str:
    """Returns a local storage repository."""
    return "local@storage:"


@pytest.fixture
def remote_storage_repository() -> str:
    """Returns a remote storage repository."""
    return "archive@repository:"


@pytest.fixture
def full_remote_path(remote_storage_repository: str, remote_path: Path) -> str:
    """Returns the merged remote repository and path."""
    return remote_storage_repository + remote_path.as_posix()


@pytest.fixture
def archive_store(
    base_store: Store,
    helpers: StoreHelpers,
    sample_id,
    father_sample_id,
    mother_sample_id,
    sample_name,
) -> Store:
    """Returns a store with samples for both a DDN customer and a non-DDN customer."""
    customer_ddn: Customer = base_store.add_customer(
        internal_id="CustWithDDN",
        invoice_address="Baker Street 221B",
        invoice_reference="Sherlock Holmes",
        name="Sherlock Holmes",
        is_clinical=True,
        data_archive_location=ArchiveLocations.KAROLINSKA_BUCKET,
    )
    customer_without_ddn: Customer = base_store.add_customer(
        internal_id="CustWithoutDDN",
        invoice_address="Wallaby Way 42",
        invoice_reference="P Sherman",
        name="P Sherman",
        is_clinical=False,
        data_archive_location="PDC",
    )

    new_samples: list[Sample] = [
        base_store.add_sample(
            name=sample_name,
            sex=Sex.MALE,
            internal_id=sample_id,
            original_ticket=str(1),
        ),
        base_store.add_sample(
            name="sample_2_with_ddn_customer",
            sex=Sex.MALE,
            internal_id=mother_sample_id,
            original_ticket=str(2),
        ),
        base_store.add_sample(
            name="sample_without_ddn_customer",
            sex=Sex.MALE,
            internal_id=father_sample_id,
            original_ticket=str(3),
        ),
    ]
    new_samples[0].customer = customer_ddn
    new_samples[0].last_sequenced_at = datetime.now()
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
    case: Case = base_store.add_case(
        data_analysis=Workflow.MIP_DNA,
        data_delivery=DataDelivery.NO_DELIVERY,
        name="dummy_name",
        ticket="123",
        customer_id=customer_ddn.id,
    )
    base_store.relate_sample(case=case, sample=new_samples[0], status="unknown")
    order = Order(
        customer_id=customer_ddn.id,
        ticket_id=new_samples[0].original_ticket,
        workflow=case.data_analysis,
    )
    base_store.session.add(order)
    base_store.session.add(case)
    base_store.session.commit()
    base_store.link_case_to_order(order.id, case.id)
    return base_store


@pytest.fixture
def sample_with_spring_file() -> str:
    return "ADM1"


@pytest.fixture
def spring_archive_api(
    populated_housekeeper_api: HousekeeperAPI,
    archive_store: Store,
    ddn_dataflow_config: DataFlowConfig,
    father_sample_id: str,
    sample_id: str,
    helpers,
) -> SpringArchiveAPI:
    """Returns an ArchiveAPI with a populated housekeeper store and a DDNDataFlowClient.
    Also adds /home/ as a prefix for each SPRING file for the DDNDataFlowClient to accept them."""
    populated_housekeeper_api.add_tags_if_non_existent(
        tag_names=[ArchiveLocations.KAROLINSKA_BUCKET]
    )
    for spring_file in populated_housekeeper_api.files(tags=[SequencingFileTag.SPRING]):
        spring_file.path = f"/home/{spring_file.path}"
        if spring_file.version.bundle.name == sample_id:
            spring_file.tags.append(
                populated_housekeeper_api.get_tag(name=ArchiveLocations.KAROLINSKA_BUCKET)
            )

    populated_housekeeper_api.commit()
    return SpringArchiveAPI(
        housekeeper_api=populated_housekeeper_api,
        status_db=archive_store,
        data_flow_config=ddn_dataflow_config,
    )


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a CliRunner"""
    return CliRunner()


@pytest.fixture
def base_context(
    base_store: Store, housekeeper_api: HousekeeperAPI, cg_config_object: CGConfig
) -> CGConfig:
    """context to use in CLI."""
    cg_config_object.status_db_ = base_store
    cg_config_object.housekeeper_api_ = housekeeper_api
    return cg_config_object


@pytest.fixture
def archive_context(
    base_context: CGConfig,
    real_housekeeper_api: HousekeeperAPI,
    path_to_spring_file_to_archive: str,
    path_to_spring_file_with_ongoing_archival: str,
    archival_job_id: int,
    helpers: StoreHelpers,
    ddn_dataflow_config: DataFlowConfig,
) -> CGConfig:
    base_context.housekeeper_api_ = real_housekeeper_api
    base_context.data_flow = ddn_dataflow_config

    customer = helpers.ensure_customer(
        store=base_context.status_db, customer_id="miria_customer", customer_name="Miriam"
    )
    customer.data_archive_location = ArchiveLocations.KAROLINSKA_BUCKET

    base_context.status_db.add_sample(
        name="sample_with_spring_files",
        sex=Sex.MALE,
        internal_id="sample_with_spring_files",
        **{"customer": "MiriaCustomer"},
    )
    helpers.add_sample(
        store=base_context.status_db, customer_id="miria_customer", internal_id="miria_sample"
    )
    bundle: Bundle = real_housekeeper_api.create_new_bundle_and_version(name="miria_sample")
    real_housekeeper_api.add_file(
        path=path_to_spring_file_to_archive,
        version_obj=bundle.versions[0],
        tags=[SequencingFileTag.SPRING, ArchiveLocations.KAROLINSKA_BUCKET],
    )
    file: File = real_housekeeper_api.add_file(
        path=path_to_spring_file_with_ongoing_archival,
        version_obj=bundle.versions[0],
        tags=[SequencingFileTag.SPRING, ArchiveLocations.KAROLINSKA_BUCKET],
    )
    file.id = 1234
    real_housekeeper_api.add_archives(files=[file], archive_task_id=archival_job_id)

    return base_context


@pytest.fixture
def path_to_spring_file_to_archive() -> str:
    return "/home/path/to/spring/file.spring"


@pytest.fixture
def path_to_spring_file_with_ongoing_archival() -> str:
    return "/home/path/to/ongoing/spring/file.spring"


@pytest.fixture
def failed_response() -> Response:
    response = Response()
    response.status_code = http.HTTPStatus.FORBIDDEN
    return response


@pytest.fixture
def failed_delete_file_response(failed_response: Response) -> Response:
    failed_response._content = b'{"detail":"Given token not valid for any token type","code":"token_not_valid","messages":[{"tokenClass":"AccessToken","tokenType":"access","message":"Token is invalid or expired"}]}'
    return failed_response


@pytest.fixture
def ok_delete_file_response(ok_response: Response) -> Response:
    ok_response._content = b'{"message":"Object has been deleted"}'
    return ok_response
