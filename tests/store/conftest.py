"""Fixtures for store tests."""
import datetime
import enum
from pathlib import Path
from typing import Generator
import pytest

from cg.constants import Pipeline
from cg.constants.subject import Gender
from cg.store import Store
from cg.store.models import Analysis, Family, Sample
from tests.store_helpers import StoreHelpers


class StoreConftestFixture(enum.Enum):
    INTERNAL_ID_SAMPLE_WITH_ATTRIBUTES: str = "sample_with_attributes"
    NAME_SAMPLE_WITH_ATTRIBUTES: str = "sample_with_attributes"
    SUBJECT_ID_SAMPLE_WITH_ATTRIBUTES: str = "test_subject_id"
    DOWN_SAMPLED_TO_SAMPLE_WITH_ATTRIBUTES: str = 1
    ENTRY_ID_SAMPLE_WITH_ATTRIBUTES: str = 1
    INVOICE_ID_SAMPLE_WITH_ATTRIBUTES: str = 1
    INTERNAL_ID_SAMPLE_WITHOUT_ATTRIBUTES: str = "sample_without_attributes"
    NAME_SAMPLE_WITHOUT_ATTRIBUTES: str = "sample_without_attributes"
    ENTRY_ID_SAMPLE_WITHOUT_ATTRIBUTES: str = 2


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
    customer = base_store.customer(microbial_submitted_order["customer"])

    for sample_data in microbial_submitted_order["items"]:
        application_version = base_store.application(sample_data["application"]).versions[0]
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
    return analysis_store.analyses()[0]


@pytest.fixture(name="case_obj")
def fixture_case_obj(analysis_store: Store) -> Family:
    """Return a case models object."""
    return analysis_store.families()[0]


@pytest.fixture(name="sample_obj")
def fixture_sample_obj(analysis_store) -> Sample:
    """Return a sample models object."""
    return analysis_store.get_all_samples()[0]


@pytest.fixture(name="sequencer_name")
def fixture_sequencer_name() -> str:
    """Return sequencer name."""
    return "A00689"


@pytest.fixture(name="store_with_a_sample_that_has_many_attributes_and_one_without")
def fixture_store_with_a_sample_that_has_many_attributes_and_one_without(
    store: Store,
    helpers: StoreHelpers,
    timestamp_now=datetime.datetime.now(),
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
