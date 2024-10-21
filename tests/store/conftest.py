"""Fixtures for store tests."""

import datetime as dt
import enum
from datetime import datetime
from typing import Generator

import pytest

from cg.constants import Workflow
from cg.constants.devices import DeviceType
from cg.constants.priority import PriorityTerms
from cg.constants.subject import PhenotypeStatus, Sex
from cg.services.illumina.data_transfer.models import IlluminaFlowCellDTO
from cg.services.orders.store_order_services.store_pool_order import StorePoolOrderService
from cg.store.models import (
    Analysis,
    Application,
    Case,
    CaseSample,
    Customer,
    IlluminaFlowCell,
    Organism,
    Sample,
)
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


class StoreConstants(enum.Enum):
    INTERNAL_ID_SAMPLE_WITH_ATTRIBUTES: str = "sample_with_attributes"
    NAME_SAMPLE_WITH_ATTRIBUTES: str = "sample_with_attributes"
    APPLICATION_VERSION_ID_SAMPLE_WITH_ATTRIBUTES: int = 2
    CUSTOMER_ID_SAMPLE_WITH_ATTRIBUTES: str = "1"
    SUBJECT_ID_SAMPLE_WITH_ATTRIBUTES: str = "test_subject_id"
    ORGANISM_ID_SAMPLE_WITH_ATTRIBUTES: int = 1
    LOQUSDB_ID_SAMPLE_WITH_ATTRIBUTES: str = "loqusdb_id"
    READS_SAMPLE_WITH_ATTRIBUTES: int = 100
    DOWN_SAMPLED_TO_SAMPLE_WITH_ATTRIBUTES: int = 1
    AGE_AT_SAMPLING_SAMPLE_WITH_ATTRIBUTES: float = 45
    COMMENT_SAMPLE_WITH_ATTRIBUTES: str = "comment"
    CONTROL_SAMPLE_WITH_ATTRIBUTES: str = "negative"
    CAPTURE_KIT_SAMPLE_WITH_ATTRIBUTES: str = "capture_kit"
    PRIORITY_SAMPLE_WITH_ATTRIBUTES: str = "research"
    ORDER_SAMPLE_WITH_ATTRIBUTES: str = "order"
    REFERENCE_GENOME_SAMPLE_WITH_ATTRIBUTES: str = "NC_222"
    ORIGINAL_TICKET_SAMPLE_WITH_ATTRIBUTES: str = "ticket"
    FROM_SAMPLE_SAMPLE_WITH_ATTRIBUTES: str = "sample_1"
    SEX_SAMPLE_WITH_ATTRIBUTES: str = "male"
    ENTRY_ID_SAMPLE_WITH_ATTRIBUTES: int = 1
    INVOICE_ID_SAMPLE_WITH_ATTRIBUTES: int = 1
    INTERNAL_ID_SAMPLE_WITHOUT_ATTRIBUTES: str = "sample_without_attributes"
    NAME_SAMPLE_WITHOUT_ATTRIBUTES: str = "sample_without_attributes"
    ENTRY_ID_SAMPLE_WITHOUT_ATTRIBUTES: int = 2

    INVOICE_ID_POOL_WITH_ATTRIBUTES: int = 1
    NAME_POOL_WITH_ATTRIBUTES: str = "pool_with_attributes"
    NAME_POOL_WITHOUT_ATTRIBUTES: str = "pool_without_attributes"
    ORDER_POOL_WITH_ATTRIBUTES: str = "order001"

    TAG_APPLICATION_WITH_ATTRIBUTES: str = "test_tag"
    PREP_CATEGORY_APPLICATION_WITH_ATTRIBUTES: str = "wgs"
    PREP_CATEGORY_APPLICATION_WITHOUT_ATTRIBUTES: str = "wes"
    TAG_APPLICATION_WITHOUT_ATTRIBUTES: str = "test_tag_2"

    INVOICE_ID_INVOICE_WITH_ATTRIBUTES: int = 1
    INVOICE_ID_INVOICE_WITHOUT_ATTRIBUTES: int = 2

    @staticmethod
    def generate_year_interval(n_entries: int, old_timestamp: dt.datetime) -> list[int]:
        """Create a list of approximately uniformly distributed year numbers from 1 to present."""
        start: int = old_timestamp.year
        stop: int = dt.date.today().year
        step: float = (stop - start) / (n_entries - 1)
        output = [start]

        for i in range(1, n_entries):
            output.append(output[0] + round(i * step))
        return output


@pytest.fixture(name="microbial_submitted_order")
def microbial_submitted_order() -> dict:
    """Build an example order as it looks after submission to."""

    def _get_item(name: str, internal_id: str, well_position: str, organism: str) -> dict:
        """Return a item."""
        ref_genomes = {
            "C. Jejuni": "NC_111",
            "M. upium": "NC_222",
            "C. difficile": "NC_333",
        }
        return dict(
            name=name,
            internal_id=internal_id,
            reads="1000",
            container="96 well plate",
            container_name="hej",
            rml_plate_name=None,
            well_position=well_position,
            well_position_rml=None,
            sex=None,
            panels=None,
            require_qc_ok=True,
            application="MWRNXTR003",
            source=None,
            status=None,
            customer="cust015",
            family=None,
            priority="standard",
            capture_kit=None,
            comment="comment",
            index=None,
            reagent_label=None,
            tumour=False,
            custom_index=None,
            elution_buffer="Nuclease-free water",
            organism=organism,
            reference_genome=ref_genomes[organism],
            extraction_method="MagNaPure 96 (contact Clinical Genomics before " "submission)",
            analysis=Workflow.RAW_DATA,
            concentration_sample="1",
            mother=None,
            father=None,
        )

    return {
        "customer": "cust000",
        "name": "test order",
        "internal_id": "lims_reference",
        "comment": "test comment",
        "ticket_number": "123456",
        "items": [
            _get_item("Jag", "ms1", "D:5", "C. Jejuni"),
            _get_item("testar", "ms2", "H:5", "M. upium"),
            _get_item("list", "ms3", "A:6", "C. difficile"),
        ],
        "project_type": "microbial",
    }


@pytest.fixture(name="microbial_store")
def microbial_store(
    base_store: Store, microbial_submitted_order: dict
) -> Generator[Store, None, None]:
    """Set up a microbial store instance."""
    customer: Customer = base_store.get_customer_by_internal_id(
        customer_internal_id=microbial_submitted_order["customer"]
    )

    for sample_data in microbial_submitted_order["items"]:
        application_version = base_store.get_application_by_tag(
            sample_data["application"]
        ).versions[0]
        organism: Organism = Organism(
            internal_id=sample_data["organism"], name=sample_data["organism"]
        )
        base_store.session.add(organism)
        sample = base_store.add_sample(
            name=sample_data["name"],
            sex=Sex.UNKNOWN,
            comment=sample_data["comment"],
            priority=sample_data["priority"],
            reads=sample_data["reads"],
            reference_genome=sample_data["reference_genome"],
        )
        sample.application_version = application_version
        sample.customer = customer
        sample.organism = organism
        base_store.session.add(sample)

    base_store.session.commit()
    yield base_store


@pytest.fixture(name="case")
def case_obj(analysis_store: Store) -> Case:
    """Return a case models object."""
    return analysis_store.get_cases()[0]


@pytest.fixture(name="sample")
def sample_obj(analysis_store) -> Sample:
    """Return a sample models object."""
    return analysis_store._get_query(table=Sample).first()


@pytest.fixture(name="sequencer_name")
def sequencer_name() -> str:
    """Return sequencer name."""
    return "A00689"


@pytest.fixture(name="invalid_application_id")
def invalid_application_id() -> int:
    """Return an invalid application id."""
    return -1


@pytest.fixture(name="invalid_application_tag")
def invalid_application_tag() -> str:
    """Return an invalid application tag."""
    return "invalid-tag"


@pytest.fixture(name="store_with_a_sample_that_has_many_attributes_and_one_without")
def store_with_a_sample_that_has_many_attributes_and_one_without(
    store: Store,
    helpers: StoreHelpers,
    timestamp_now=dt.datetime.now(),
) -> Store:
    """Return a store with a sample that has many attributes and one without."""
    helpers.add_sample(
        store=store,
        control=StoreConstants.CONTROL_SAMPLE_WITH_ATTRIBUTES.value,
        customer_id=StoreConstants.CUSTOMER_ID_SAMPLE_WITH_ATTRIBUTES.value,
        is_external=True,
        is_tumour=True,
        internal_id=StoreConstants.INTERNAL_ID_SAMPLE_WITH_ATTRIBUTES.value,
        reads=StoreConstants.READS_SAMPLE_WITH_ATTRIBUTES.value,
        name=StoreConstants.NAME_SAMPLE_WITH_ATTRIBUTES.value,
        original_ticket=StoreConstants.ORIGINAL_TICKET_SAMPLE_WITH_ATTRIBUTES.value,
        ordered_at=timestamp_now,
        created_at=timestamp_now,
        delivered_at=timestamp_now,
        received_at=timestamp_now,
        last_sequenced_at=timestamp_now,
        prepared_at=timestamp_now,
        application_version_id=StoreConstants.APPLICATION_VERSION_ID_SAMPLE_WITH_ATTRIBUTES.value,
        subject_id=StoreConstants.SUBJECT_ID_SAMPLE_WITH_ATTRIBUTES.value,
        invoice_id=StoreConstants.INVOICE_ID_SAMPLE_WITH_ATTRIBUTES.value,
        organism_id=StoreConstants.ORGANISM_ID_SAMPLE_WITH_ATTRIBUTES.value,
        loqusdb_id=StoreConstants.LOQUSDB_ID_SAMPLE_WITH_ATTRIBUTES.value,
        downsampled_to=StoreConstants.DOWN_SAMPLED_TO_SAMPLE_WITH_ATTRIBUTES.value,
        no_invoice=False,
        age_at_sampling=StoreConstants.AGE_AT_SAMPLING_SAMPLE_WITH_ATTRIBUTES.value,
        capture_kit=StoreConstants.CAPTURE_KIT_SAMPLE_WITH_ATTRIBUTES.value,
        comment=StoreConstants.COMMENT_SAMPLE_WITH_ATTRIBUTES.value,
        from_sample=StoreConstants.FROM_SAMPLE_SAMPLE_WITH_ATTRIBUTES.value,
        order=StoreConstants.ORDER_SAMPLE_WITH_ATTRIBUTES.value,
        priority=StoreConstants.PRIORITY_SAMPLE_WITH_ATTRIBUTES.value,
        reference_genome=StoreConstants.REFERENCE_GENOME_SAMPLE_WITH_ATTRIBUTES.value,
        sex=StoreConstants.SEX_SAMPLE_WITH_ATTRIBUTES.value,
    )

    helpers.add_sample(
        store=store,
        is_external=False,
        is_tumour=False,
        internal_id=StoreConstants.INTERNAL_ID_SAMPLE_WITHOUT_ATTRIBUTES.value,
        name=StoreConstants.NAME_SAMPLE_WITHOUT_ATTRIBUTES.value,
        delivered_at=None,
        received_at=None,
        last_sequenced_at=None,
        prepared_at=None,
        subject_id=None,
        invoice_id=None,
        downsampled_to=None,
        no_invoice=True,
    )

    return store


@pytest.fixture(name="store_with_a_pool_with_and_without_attributes")
def store_with_a_pool_with_and_without_attributes(
    store: Store,
    helpers: StoreHelpers,
    timestamp_now=dt.datetime.now(),
) -> Store:
    """Return a store with a pool with and without attributes."""
    helpers.ensure_pool(
        store=store,
        delivered_at=timestamp_now,
        received_at=timestamp_now,
        invoice_id=StoreConstants.INVOICE_ID_POOL_WITH_ATTRIBUTES.value,
        no_invoice=False,
        name=StoreConstants.NAME_POOL_WITH_ATTRIBUTES.value,
        order=StoreConstants.ORDER_POOL_WITH_ATTRIBUTES.value,
    )

    helpers.ensure_pool(
        store=store,
        delivered_at=None,
        received_at=None,
        invoice_id=None,
        no_invoice=True,
        name=StoreConstants.NAME_POOL_WITHOUT_ATTRIBUTES.value,
    )

    return store


@pytest.fixture
def store_with_an_application_with_and_without_attributes(
    store: Store,
    helpers: StoreHelpers,
) -> Store:
    """Return a store with an application with and without attributes."""
    helpers.ensure_application(
        store=store,
        tag=StoreConstants.TAG_APPLICATION_WITH_ATTRIBUTES.value,
        prep_category=StoreConstants.PREP_CATEGORY_APPLICATION_WITH_ATTRIBUTES.value,
        is_external=True,
        is_archived=True,
    )

    helpers.ensure_application(
        store=store,
        tag=StoreConstants.TAG_APPLICATION_WITHOUT_ATTRIBUTES.value,
        prep_category=StoreConstants.PREP_CATEGORY_APPLICATION_WITHOUT_ATTRIBUTES.value,
        is_external=False,
        is_archived=False,
    )

    return store


@pytest.fixture
def store_with_application_limitations(
    store_with_an_application_with_and_without_attributes: Store, helpers: StoreHelpers
) -> Store:
    """Return a store with different application limitations."""
    helpers.ensure_application_limitation(
        store=store_with_an_application_with_and_without_attributes,
        application=store_with_an_application_with_and_without_attributes.get_application_by_tag(
            StoreConstants.TAG_APPLICATION_WITH_ATTRIBUTES.value
        ),
        workflow=Workflow.MIP_DNA,
    )
    for workflow in [Workflow.MIP_DNA, Workflow.BALSAMIC]:
        helpers.ensure_application_limitation(
            store=store_with_an_application_with_and_without_attributes,
            application=store_with_an_application_with_and_without_attributes.get_application_by_tag(
                StoreConstants.TAG_APPLICATION_WITHOUT_ATTRIBUTES.value
            ),
            workflow=workflow,
        )
    return store_with_an_application_with_and_without_attributes


@pytest.fixture(name="applications_store")
def applications_store(store: Store, helpers: StoreHelpers) -> Store:
    """Return a store populated with applications from excel file"""
    app_tags: list[str] = ["PGOTTTR020", "PGOTTTR030", "PGOTTTR040"]
    for app_tag in app_tags:
        helpers.ensure_application(store=store, tag=app_tag)
    return store


@pytest.fixture(name="store_with_different_application_versions")
def store_with_different_application_versions(
    applications_store: Store,
    helpers: StoreHelpers,
    old_timestamp: dt.datetime,
) -> Store:
    """Returns a store with application versions with different applications, dates and versions."""
    applications: list[Application] = applications_store.get_applications()
    years: list[int] = StoreConstants.generate_year_interval(
        n_entries=len(applications),
        old_timestamp=old_timestamp,
    )
    versions: list[int] = list(range(1, len(applications) + 1))

    for application, year, version in zip(applications, years, versions):
        helpers.ensure_application_version(
            store=applications_store,
            application_tag=application.tag,
            valid_from=dt.datetime(year, 1, 1, 1, 1, 1),
            version=version,
        )
    return applications_store


@pytest.fixture(name="store_with_an_invoice_with_and_without_attributes")
def store_with_an_invoice_with_and_without_attributes(
    store: Store,
    helpers: StoreHelpers,
    timestamp_now=dt.datetime.now(),
) -> Store:
    """Return a store with an invoice with and without attributes."""
    helpers.ensure_invoice(
        store=store,
        invoice_id=StoreConstants.INVOICE_ID_INVOICE_WITH_ATTRIBUTES.value,
        invoiced_at=timestamp_now,
    )

    helpers.ensure_invoice(
        store=store,
        invoice_id=StoreConstants.INVOICE_ID_INVOICE_WITHOUT_ATTRIBUTES.value,
        invoiced_at=None,
    )
    return store


@pytest.fixture
def store_with_older_and_newer_analyses(
    base_store: Store,
    helpers: StoreHelpers,
    case: Case,
    timestamp_now: dt.datetime,
    timestamp_yesterday: dt.datetime,
    old_timestamp: dt.datetime,
) -> Generator[Store, None, None]:
    """Return a store with older and newer analyses."""
    analysis = base_store._get_query(table=Analysis).first()
    analysis.uploaded_at = timestamp_now
    analysis.cleaned_at = timestamp_now
    analysis.started_at = timestamp_now
    analysis.completed_at = timestamp_now
    base_store.session.add(analysis)
    base_store.session.commit()
    times = [timestamp_now, timestamp_yesterday, old_timestamp]
    for time in times:
        helpers.add_analysis(
            store=base_store,
            case=case,
            started_at=time,
            completed_at=time,
            uploaded_at=time,
            cleaned_at=time,
            workflow=Workflow.BALSAMIC,
        )

    yield base_store


@pytest.fixture(name="store_with_analyses_for_cases")
def store_with_analyses_for_cases(
    analysis_store: Store,
    helpers: StoreHelpers,
    timestamp_now: dt.datetime,
    timestamp_yesterday: dt.datetime,
) -> Store:
    """Return a store with two analyses for two cases."""
    case_one = analysis_store.get_case_by_internal_id("yellowhog")
    case_two = helpers.add_case(analysis_store, internal_id="test_case_1")

    cases = [case_one, case_two]
    for case in cases:
        oldest_analysis = helpers.add_analysis(
            analysis_store,
            case=case,
            started_at=timestamp_yesterday,
            uploaded_at=timestamp_yesterday,
            delivery_reported_at=None,
        )
        helpers.add_analysis(
            analysis_store,
            case=case,
            started_at=timestamp_now,
            uploaded_at=timestamp_now,
            delivery_reported_at=None,
        )
        sample = helpers.add_sample(analysis_store, delivered_at=timestamp_now)
        link: CaseSample = analysis_store.relate_sample(
            case=oldest_analysis.case, sample=sample, status=PhenotypeStatus.UNKNOWN
        )
        analysis_store.session.add(link)
    return analysis_store


@pytest.fixture
def rml_pool_store(
    case_id: str,
    customer_id: str,
    helpers,
    sample_id: str,
    store: Store,
    ticket_id: str,
    timestamp_now: datetime,
):
    new_customer = store.add_customer(
        internal_id=customer_id,
        name="Test customer",
        scout_access=True,
        invoice_address="skolgatan 15",
        invoice_reference="abc",
    )
    store.session.add(new_customer)

    application = store.add_application(
        tag="RMLP05R800",
        prep_category="rml",
        description="Ready-made",
        percent_kth=80,
        percent_reads_guaranteed=75,
        sequencing_depth=0,
        target_reads=800,
    )
    store.session.add(application)

    app_version = store.add_application_version(
        application=application,
        version=1,
        valid_from=timestamp_now,
        prices={
            PriorityTerms.STANDARD: 12,
            PriorityTerms.PRIORITY: 222,
            PriorityTerms.EXPRESS: 123,
            PriorityTerms.RESEARCH: 12,
        },
    )
    store.session.add(app_version)

    new_pool = store.add_pool(
        customer=new_customer,
        name="Test",
        order="Test",
        ordered=dt.datetime.now(),
        application_version=app_version,
    )
    store.session.add(new_pool)
    new_case = helpers.add_case(
        store=store,
        internal_id=case_id,
        name=StorePoolOrderService.create_case_name(ticket=ticket_id, pool_name="Test"),
    )
    store.session.add(new_case)

    new_sample = helpers.add_sample(
        store=store,
        application_tag=application.tag,
        application_type=application.prep_category,
        customer_id=new_customer.id,
        internal_id=sample_id,
    )
    new_sample.application_version = app_version
    store.session.add(new_sample)
    store.session.commit()

    helpers.add_relationship(
        store=store,
        sample=new_sample,
        case=new_case,
    )

    yield store


@pytest.fixture
def store_with_analyses_for_cases_not_uploaded_fluffy(
    analysis_store: Store,
    helpers: StoreHelpers,
    timestamp_now: datetime,
    timestamp_yesterday: datetime,
) -> Store:
    """Return a store with two analyses for two cases and workflow."""
    case_one = analysis_store.get_case_by_internal_id("yellowhog")
    case_two = helpers.add_case(analysis_store, internal_id="test_case_1")

    cases = [case_one, case_two]
    for case in cases:
        oldest_analysis = helpers.add_analysis(
            analysis_store,
            case=case,
            started_at=timestamp_yesterday,
            uploaded_at=timestamp_yesterday,
            delivery_reported_at=None,
            workflow=Workflow.FLUFFY,
        )
        helpers.add_analysis(
            analysis_store,
            case=case,
            started_at=timestamp_now,
            uploaded_at=None,
            delivery_reported_at=None,
            workflow=Workflow.FLUFFY,
        )
        sample = helpers.add_sample(analysis_store, delivered_at=timestamp_now)
        link: CaseSample = analysis_store.relate_sample(
            case=oldest_analysis.case, sample=sample, status=PhenotypeStatus.UNKNOWN
        )
        analysis_store.session.add(link)
    return analysis_store


@pytest.fixture
def store_with_samples_for_multiple_customers(
    store: Store, helpers: StoreHelpers, timestamp_now: datetime
) -> Generator[Store, None, None]:
    """Return a store with two samples for three different customers."""
    for number in range(3):
        helpers.add_sample(
            store=store,
            customer_id="".join(["cust00", str(number)]),
            internal_id="_".join(["test_sample", str(number)]),
            no_invoice=False,
            delivered_at=timestamp_now,
        )
    yield store


@pytest.fixture
def illumina_flow_cell_internal_id() -> str:
    return "FC123456"


@pytest.fixture
def illumina_flow_cell_model_s1() -> str:
    return "S1"


@pytest.fixture
def illumina_flow_cell_dto(
    illumina_flow_cell_internal_id: str, illumina_flow_cell_model_s1: str
) -> IlluminaFlowCellDTO:
    return IlluminaFlowCellDTO(
        internal_id=illumina_flow_cell_internal_id,
        type=DeviceType.ILLUMINA,
        model=illumina_flow_cell_model_s1,
    )


@pytest.fixture
def illumina_flow_cell(
    illumina_flow_cell_internal_id: str, illumina_flow_cell_model_s1: str
) -> IlluminaFlowCell:
    return IlluminaFlowCell(
        internal_id=illumina_flow_cell_internal_id,
        type=DeviceType.ILLUMINA,
        model=illumina_flow_cell_model_s1,
    )
