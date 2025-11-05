from pathlib import Path
from unittest.mock import create_autospec

import pytest
from housekeeper.store.models import File

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.constants import DataDelivery, Workflow
from cg.constants.priority import Priority, SlurmQos
from cg.models.orders.sample_base import SexEnum, StatusEnum
from cg.store.models import (
    Application,
    BedVersion,
    Case,
    CaseSample,
    Customer,
    Order,
    Organism,
    Sample,
)
from cg.store.store import Store
from tests.store_helpers import StoreHelpers
from tests.typed_mock import TypedMock, create_typed_mock


@pytest.fixture
def microsalt_store(base_store: Store, helpers: StoreHelpers) -> Store:
    organism: Organism = base_store.get_all_organisms()[0]
    microsalt_case: Case = helpers.add_case(
        customer_id="cust000",
        data_analysis=Workflow.MICROSALT,
        data_delivery=DataDelivery.ANALYSIS_FILES,
        internal_id="microparakeet",
        name="microsalt-name",
        store=base_store,
        ticket="123456",
    )
    application: Application = base_store.get_application_by_tag("MWRNXTR003")
    customer: Customer = base_store.get_customers()[0]

    microsalt_sample: Sample = base_store.add_sample(
        application_version=application.versions[0],
        customer=customer,
        name="microsalt-sample",
        organism=organism,
        priority=Priority.standard,
        sex=SexEnum.unknown,
    )

    base_store.relate_sample(
        case=microsalt_case, sample=microsalt_sample, status=StatusEnum.unknown
    )
    order: Order = base_store.add_order(customer=customer, ticket_id=1)
    microsalt_case.orders.append(order)
    base_store.add_item_to_store(microsalt_case)
    base_store.add_item_to_store(microsalt_sample)
    base_store.commit_to_store()

    return base_store


@pytest.fixture
def mock_store_for_nextflow_config_file_creation(
    nextflow_case_id: str,
) -> Store:
    """Fixture to provide a mock store for the Nextflow config file creator."""
    case: Case = create_autospec(Case, slurm_priority=SlurmQos.NORMAL)
    store: Store = create_autospec(Store)
    store.get_case_by_internal_id.return_value = case
    return store


@pytest.fixture
def mock_housekeeper_for_nf_sample_sheet(fastq_path_1: Path, fastq_path_2: Path) -> HousekeeperAPI:
    """Fixture to provide a mock housekeeper API for the Nextflow sample sheet creator."""
    fastq_file1: File = create_autospec(File, full_path=fastq_path_1.as_posix())
    fastq_file2: File = create_autospec(File, full_path=fastq_path_2.as_posix())
    housekeeper_mock: HousekeeperAPI = create_autospec(HousekeeperAPI)
    housekeeper_mock.files.return_value = [fastq_file1, fastq_file2]
    return housekeeper_mock


@pytest.fixture
def mock_store_for_nallo_file_creators() -> Store:
    mock_store: TypedMock = create_typed_mock(Store)
    mock_store.as_mock.get_case_workflow.return_value = Workflow.NALLO
    mock_store.as_mock.get_case_priority.return_value = SlurmQos.NORMAL
    return mock_store.as_type


@pytest.fixture
def mock_store_for_raredisease_file_creators(
    nextflow_case_id: str, nextflow_sample_id: str
) -> Store:
    """Fixture to provide a mock store for the params file creator."""
    sample: Sample = create_autospec(Sample)
    sample.internal_id = nextflow_sample_id
    sample.application_version.application.analysis_type = "wgs"
    sample.sex = SexEnum.male
    case: Case = create_autospec(Case)
    case.internal_id = nextflow_case_id
    link: CaseSample = create_autospec(
        CaseSample, get_maternal_sample_id="", get_paternal_sample_id=""
    )
    link.status = StatusEnum.affected
    link.sample = sample
    link.case = case
    case.links = [link]
    case.data_analysis = Workflow.RAREDISEASE
    store: Store = create_autospec(Store)
    store.get_case_by_internal_id.return_value = case
    store.get_case_priority.return_value = SlurmQos.NORMAL
    store.get_case_workflow.return_value = Workflow.RAREDISEASE
    store.get_samples_by_case_id.return_value = [sample]
    store.get_sample_by_internal_id.return_value = sample
    bed_version: BedVersion = create_autospec(BedVersion)
    bed_version.filename = "bed_version_file.bed"
    store.get_bed_version_by_short_name.return_value = bed_version
    return store


@pytest.fixture
def mock_store_for_rnafusion_file_creators(nextflow_sample_id: str) -> Store:
    """Fixture mocking the necessary parts of StatusDB for the RNAFusion sample sheet creator."""
    mock_sample: Sample = create_autospec(Sample)
    mock_sample.internal_id = nextflow_sample_id

    mock_case: Case = create_autospec(Case, samples=[mock_sample])
    mock_case.data_analysis = Workflow.RNAFUSION

    mock_store: Store = create_autospec(Store)
    mock_store.get_case_by_internal_id.return_value = mock_case
    mock_store.get_case_workflow.return_value = Workflow.RNAFUSION
    mock_store.get_case_priority.return_value = SlurmQos.NORMAL
    return mock_store


@pytest.fixture
def mock_store_for_taxprofiler_file_creators(nextflow_sample_id: str) -> Store:
    """Fixture to provide a mock store for the Taxprofiler sample sheet creator."""
    mock_sample: Sample = create_autospec(Sample)
    mock_sample.internal_id = nextflow_sample_id
    mock_sample.name = nextflow_sample_id

    mock_case: Case = create_autospec(Case, samples=[mock_sample])

    mock_store: Store = create_autospec(Store)
    mock_store.get_case_by_internal_id.return_value = mock_case
    mock_store.get_case_workflow.return_value = Workflow.TAXPROFILER
    mock_store.get_case_priority.return_value = SlurmQos.NORMAL
    return mock_store


@pytest.fixture
def mock_store_for_nextflow_gene_panel_file_creator() -> Store:
    """Fixture to provide a mock store for the gene panel file creator."""
    case: Case = create_autospec(Case)
    case.customer.internal_id = "cust000"
    store: Store = create_autospec(Store)
    store.get_case_by_internal_id.return_value = case
    return store
