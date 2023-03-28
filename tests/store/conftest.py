"""Fixtures for store tests."""
import datetime as dt
import enum
from pathlib import Path
from typing import Generator, List
import pytest

from cg.constants import Pipeline
from cg.constants.subject import Gender
from cg.store import Store
from cg.store.models import Analysis, Application, Family, Sample, Customer
from tests.store_helpers import StoreHelpers
from tests.store.api.conftest import fixture_applications_store
from tests.conftest import fixture_old_timestamp


class StoreConftestFixture(enum.Enum):
    INTERNAL_ID_SAMPLE_WITH_ATTRIBUTES: str = "sample_with_attributes"
    NAME_SAMPLE_WITH_ATTRIBUTES: str = "sample_with_attributes"
    SUBJECT_ID_SAMPLE_WITH_ATTRIBUTES: str = "test_subject_id"
    DOWN_SAMPLED_TO_SAMPLE_WITH_ATTRIBUTES: int = 1
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
    def generate_year_interval(n_entries, old_timestamp: dt.datetime) -> List[int]:
        """Create a list of approximately uniformly distributed year numbers from 1 to present."""
        start: int = old_timestamp.year
        stop: int = dt.date.today().year
        step: float = (stop - start) / (n_entries - 1)
        output = [start]

        for i in range(1, n_entries):
            output.append(output[0] + round(i * step))
        return output


@pytest.fixture(name="application_versions_file")
def fixture_application_versions_file(fixtures_dir: Path) -> str:
    """Return application version import file."""
    return Path(fixtures_dir, "store", "api", "application_versions.xlsx").as_posix()


@pytest.fixture(name="applications_file")
def fixture_applications_file(fixtures_dir: Path) -> str:
    """Return application import file."""
    return Path(fixtures_dir, "store", "api", "applications.xlsx").as_posix()


@pytest.fixture(name="microbial_submitted_order")
def fixture_microbial_submitted_order() -> dict:
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
            require_qcok=True,
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
            analysis=str(Pipeline.FASTQ),
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
def fixture_microbial_store(
    base_store: Store, microbial_submitted_order: dict
) -> Generator[Store, None, None]:
    """Set up a microbial store instance."""
    customer: Customer = base_store.get_customer_by_customer_id(
        customer_id=microbial_submitted_order["customer"]
    )

    for sample_data in microbial_submitted_order["items"]:
        application_version = base_store.get_application_by_tag(
            sample_data["application"]
        ).versions[0]
        organism = base_store.Organism(
            internal_id=sample_data["organism"], name=sample_data["organism"]
        )
        base_store.add(organism)
        sample = base_store.add_sample(
            name=sample_data["name"],
            sex=Gender.UNKNOWN,
            comment=sample_data["comment"],
            priority=sample_data["priority"],
            reads=sample_data["reads"],
            reference_genome=sample_data["reference_genome"],
        )
        sample.application_version = application_version
        sample.customer = customer
        sample.organism = organism
        base_store.add(sample)

    base_store.commit()
    yield base_store


@pytest.fixture(name="analysis_obj")
def fixture_analysis_obj(analysis_store: Store) -> Analysis:
    """Return an analysis object from a populated store."""
    return analysis_store._get_query(table=Analysis)[0]


@pytest.fixture(name="case_obj")
def fixture_case_obj(analysis_store: Store) -> Family:
    """Return a case models object."""
    return analysis_store.families()[0]


@pytest.fixture(name="sample_obj")
def fixture_sample_obj(analysis_store) -> Sample:
    """Return a sample models object."""
    return analysis_store.get_samples()[0]


@pytest.fixture(name="sequencer_name")
def fixture_sequencer_name() -> str:
    """Return sequencer name."""
    return "A00689"


@pytest.fixture(name="invalid_application_id")
def fixture_invalid_application_id() -> int:
    """Return an invalid application id."""
    return -1


@pytest.fixture(name="invalid_application_version_version")
def fixture_invalid_application_version_version() -> int:
    """Return an invalid version of an Application Version."""
    return -1


@pytest.fixture(name="store_with_a_sample_that_has_many_attributes_and_one_without")
def fixture_store_with_a_sample_that_has_many_attributes_and_one_without(
    store: Store,
    helpers: StoreHelpers,
    timestamp_now=dt.datetime.now(),
) -> Store:
    """Return a store with a sample that has many attributes and one without."""
    helpers.add_sample(
        store,
        internal_id=StoreConftestFixture.INTERNAL_ID_SAMPLE_WITH_ATTRIBUTES.value,
        name=StoreConftestFixture.NAME_SAMPLE_WITH_ATTRIBUTES.value,
        is_external=True,
        is_tumour=True,
        delivered_at=timestamp_now,
        received_at=timestamp_now,
        sequenced_at=timestamp_now,
        prepared_at=timestamp_now,
        subject_id=StoreConftestFixture.SUBJECT_ID_SAMPLE_WITH_ATTRIBUTES.value,
        invoice_id=StoreConftestFixture.INVOICE_ID_SAMPLE_WITH_ATTRIBUTES.value,
        downsampled_to=StoreConftestFixture.DOWN_SAMPLED_TO_SAMPLE_WITH_ATTRIBUTES.value,
        no_invoice=False,
    )

    helpers.add_sample(
        store,
        internal_id=StoreConftestFixture.INTERNAL_ID_SAMPLE_WITHOUT_ATTRIBUTES.value,
        name=StoreConftestFixture.NAME_SAMPLE_WITHOUT_ATTRIBUTES.value,
        is_external=False,
        is_tumour=False,
        delivered_at=None,
        received_at=None,
        sequenced_at=None,
        prepared_at=None,
        subject_id=None,
        invoice_id=None,
        downsampled_to=None,
        no_invoice=True,
    )

    return store


@pytest.fixture(name="store_with_a_pool_with_and_without_attributes")
def fixture_store_with_a_pool_with_and_without_attributes(
    store: Store,
    helpers: StoreHelpers,
    timestamp_now=dt.datetime.now(),
) -> Store:
    """Return a store with a pool with and without attributes."""
    helpers.ensure_pool(
        store=store,
        delivered_at=timestamp_now,
        received_at=timestamp_now,
        invoice_id=StoreConftestFixture.INVOICE_ID_POOL_WITH_ATTRIBUTES.value,
        no_invoice=False,
        name=StoreConftestFixture.NAME_POOL_WITH_ATTRIBUTES.value,
        order=StoreConftestFixture.ORDER_POOL_WITH_ATTRIBUTES.value,
    )

    helpers.ensure_pool(
        store=store,
        delivered_at=None,
        received_at=None,
        invoice_id=None,
        no_invoice=True,
        name=StoreConftestFixture.NAME_POOL_WITHOUT_ATTRIBUTES.value,
    )

    return store


@pytest.fixture(name="store_with_an_application_with_and_without_attributes")
def fixture_store_with_an_application_with_and_without_attributes(
    store: Store,
    helpers: StoreHelpers,
    timestamp_now=dt.datetime.now(),
) -> Store:
    """Return a store with an application with and without attributes."""
    helpers.ensure_application(
        store=store,
        tag=StoreConftestFixture.TAG_APPLICATION_WITH_ATTRIBUTES.value,
        prep_category=StoreConftestFixture.PREP_CATEGORY_APPLICATION_WITH_ATTRIBUTES.value,
        is_external=True,
        is_archived=True,
    )

    helpers.ensure_application(
        store=store,
        tag=StoreConftestFixture.TAG_APPLICATION_WITHOUT_ATTRIBUTES.value,
        prep_category=StoreConftestFixture.PREP_CATEGORY_APPLICATION_WITHOUT_ATTRIBUTES.value,
        is_external=False,
        is_archived=False,
    )

    return store


@pytest.fixture(name="store_with_different_application_versions")
def fixture_store_with_different_application_versions(
    applications_store: Store,
    helpers: StoreHelpers,
    old_timestamp: dt.datetime,
) -> Store:
    """Returns a store with application versions with different applications, dates and versions."""
    applications: List[Application] = applications_store.get_applications()
    years: List[int] = StoreConftestFixture.generate_year_interval(
        n_entries=len(applications),
        old_timestamp=old_timestamp,
    )
    versions: List[int] = list(range(1, len(applications) + 1))

    for application, year, version in zip(applications, years, versions):
        helpers.ensure_application_version(
            store=applications_store,
            application_tag=application.tag,
            valid_from=dt.datetime(year, 1, 1, 1, 1, 1),
            version=version,
        )
    return applications_store


@pytest.fixture(name="store_with_an_invoice_with_and_without_attributes")
def fixture_store_with_an_invoice_with_and_without_attributes(
    store: Store,
    helpers: StoreHelpers,
    timestamp_now=dt.datetime.now(),
) -> Store:
    """Return a store with an invoice with and without attributes."""
    helpers.ensure_invoice(
        store=store,
        invoice_id=StoreConftestFixture.INVOICE_ID_INVOICE_WITH_ATTRIBUTES.value,
        invoiced_at=timestamp_now,
    )

    helpers.ensure_invoice(
        store=store,
        invoice_id=StoreConftestFixture.INVOICE_ID_INVOICE_WITHOUT_ATTRIBUTES.value,
        invoiced_at=None,
    )
    return store


@pytest.fixture(name="store_with_case_and_analysis")
def fixture_store_with_case_and_analysis(
    store: Store, helpers: StoreHelpers, analysis_type: str = "wgs"
) -> Store:
    """Return a store with a case and analysis."""
    # GIVEN a store with a case and analysis
    case = helpers.add_case(store=store, name="test_case", internal_id="test_case_internal_id")
    helpers.add_analysis(store=store, case=case)
    yield store


@pytest.fixture(name="store_with_older_and_newer_analyses")
def fixture_store_with_older_and_newer_analyses(
    base_store: Store,
    helpers: StoreHelpers,
    case_obj: Family,
    timestamp_now: dt.datetime,
    timestamp_yesterday: dt.datetime,
    old_timestamp: dt.datetime,
) -> Store:
    """Return a store with  older and newer analyses."""
    analysis = base_store.Analysis.query.first()
    analysis.uploaded_at = timestamp_now
    analysis.uploaded_to_vogue_at = timestamp_now
    analysis.cleaned_at = timestamp_now
    analysis.started_at = timestamp_now
    analysis.completed_at = timestamp_now
    base_store.add_commit(analysis)
    times = [timestamp_now, timestamp_yesterday, old_timestamp]
    for time in times:
        helpers.add_analysis(
            store=base_store,
            case=case_obj,
            pipeline=Pipeline.BALSAMIC,
            started_at=time,
            completed_at=time,
            uploaded_at=time,
            uploaded_to_vogue_at=time,
            cleaned_at=time,
        )

    yield base_store
