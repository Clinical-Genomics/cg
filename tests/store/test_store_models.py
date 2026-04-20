import pytest

from cg.constants.constants import ControlOptions
from cg.constants.priority import Priority
from cg.constants.sequencing import ReadType, SeqLibraryPrepCategory
from cg.store.models import (
    Application,
    ApplicationVersion,
    Case,
    CaseSample,
    Customer,
    IlluminaSampleSequencingMetrics,
    PacbioSampleSequencingMetrics,
    Sample,
)
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


def test_application_version_has_application(store: Store, helpers: StoreHelpers):
    """Test that an Application version has the application that was instantiated to."""
    # GIVEN an application
    application: Application = helpers.ensure_application(store=store, tag="dummy_tag")

    # WHEN initialising an application version with the application
    application_version = ApplicationVersion(application=application)

    # THEN the application version has an application attribute
    assert application_version.application
    # THEN the application version's application is the application used for instantiation
    assert application_version.application == application


def test_microbial_sample_to_dict(microbial_store: Store, helpers):
    # GIVEN a store with a Microbial sample
    sample_obj = helpers.add_microbial_sample(microbial_store)
    microbial_store.session.add(sample_obj)
    microbial_store.session.commit()
    assert sample_obj

    # WHEN running to dict on that sample
    a_dict = sample_obj.to_dict(links=True)

    # THEN you should get a dictionary with
    assert a_dict["id"]
    assert a_dict["internal_id"]
    assert a_dict["name"]
    assert a_dict["application_version_id"]
    assert a_dict["created_at"]
    assert a_dict["priority"]
    assert a_dict["reads"]
    assert a_dict["comment"]
    assert a_dict["application"]
    assert a_dict["application_version"]


def test_no_collaborators(base_store):
    # GIVEN a customer without collaborations
    new_customer_id = "cust004"
    customer = base_store.add_customer(
        new_customer_id,
        "No-colab",
        scout_access=True,
        invoice_address="Test street",
        invoice_reference="ABCDEF",
    )
    # WHEN calling the collaborators property
    collaborators = customer.collaborators
    # THEN only the customer should be returned
    assert len(collaborators) == 1
    assert collaborators.pop().internal_id == new_customer_id


def test_collaborators(base_store, customer_id):
    # GIVEN a customer with one collaboration
    customer: Customer = base_store.get_customer_by_internal_id(customer_internal_id=customer_id)
    assert all(
        customer_obj.internal_id
        in [
            "cust001",
            "cust002",
            "cust003",
            customer_id,
        ]
        for customer_obj in customer.collaborations[0].customers
    )

    # WHEN calling the collaborators property
    # THEN the customer and the collaborators should be returned
    collaborators = customer.collaborators
    assert len(collaborators) == 4
    assert all(
        collaborator.internal_id
        in [
            "cust001",
            "cust002",
            "cust003",
            customer_id,
        ]
        for collaborator in collaborators
    )


def test_multiple_collaborations(base_store, customer_id):
    # Given a customer in two collaborations
    collaboration = base_store.add_collaboration("small_collaboration", "small collaboration")
    new_customer_id = "cust004"
    new_customer = base_store.add_customer(
        new_customer_id,
        "No-colab",
        scout_access=True,
        invoice_address="Test street",
        invoice_reference="ABCDEF",
    )
    prod_customer: Customer = base_store.get_customer_by_internal_id(
        customer_internal_id=customer_id
    )
    collaboration.customers.extend([prod_customer, new_customer])
    base_store.session.add_all([new_customer, collaboration])
    base_store.session.commit()
    base_store.session.refresh(collaboration)
    # WHEN calling the collaborators property
    collaborators = prod_customer.collaborators
    # THEN all customers in both collaborations should be returned
    assert len(collaborators) == 5
    assert all(
        collaborator.internal_id in ["cust001", new_customer_id, "cust002", "cust003", customer_id]
        for collaborator in collaborators
    )


def test_case_samples_all_control(analysis_store: Store, case_id: str) -> None:
    """Tests that are_all_samples_control returns True if all samples in a case are controls."""

    # GIVEN a case with all samples being positive controls
    case: Case = analysis_store.get_case_by_internal_id(case_id)
    for sample in case.samples:
        sample.control = ControlOptions.POSITIVE

    # WHEN checking if all samples are controls

    # THEN the result should be True
    assert case.are_all_samples_control()


def test_sample_is_external():
    # GIVEN a sample associated with an external application
    sample = Sample(
        application_version=ApplicationVersion(application=Application(is_external=True))
    )

    # THEN the sample is external
    assert sample.is_external


def test_sample_is_not_external():
    # GIVEN a sample associated with an application that is not external
    sample = Sample(
        application_version=ApplicationVersion(application=Application(is_external=False))
    )
    # THEN the sample is not external
    assert not sample.is_external


def test_hifi_yield_pacbio_sample():
    # GIVEN a PacBio sample with pacbio sequencing runs
    sample = Sample(
        _sample_run_metrics=[
            PacbioSampleSequencingMetrics(hifi_yield=10),
            PacbioSampleSequencingMetrics(hifi_yield=90),
        ]
    )
    # WHEN getting the accumulated HiFi yield
    hifi_yield: int | None = sample.hifi_yield

    # THEN the value is the sum of all the sample metric yields
    assert hifi_yield == 100


def test_hifi_yield_illumina_sample():
    # GIVEN a Illumina sample with Illumina sequencing runs
    sample = Sample(
        _sample_run_metrics=[
            IlluminaSampleSequencingMetrics(),
            IlluminaSampleSequencingMetrics(),
        ]
    )

    # WHEN getting the accumulated HiFi yield
    hifi_yield: int | None = sample.hifi_yield

    # THEN the value should be None
    assert hifi_yield is None


def test_hifi_yield_no_sample_sequencing_metrics():
    # GIVEN sample without sequencing metrics
    sample = Sample()

    # WHEN getting the accumulated HiFi yield
    hifi_yield: int | None = sample.hifi_yield

    # THEN the value should be None
    assert hifi_yield is None


def test_application_expected_hifi_yield():
    # GIVEN an application with target_hifi_yield and percent_hifi_yield_guaranteed
    application = Application(
        target_hifi_yield=200,
        percent_hifi_yield_guaranteed=75,
    )

    # WHEN getting the expected HiFi yield
    expected_hifi_yield: float | None = application.expected_hifi_yield

    # THEN the value should be calculated correctly
    assert expected_hifi_yield == 150


@pytest.mark.parametrize(
    "prep_category, read_type, expected_analysis_type",
    [
        (SeqLibraryPrepCategory.COVID.value, ReadType.SHORT_READ.value, "cov"),
        (SeqLibraryPrepCategory.MICROBIAL.value, ReadType.SHORT_READ.value, "mic"),
        (SeqLibraryPrepCategory.READY_MADE_LIBRARY.value, ReadType.SHORT_READ.value, "rml"),
        (SeqLibraryPrepCategory.TARGETED_GENOME_SEQUENCING.value, ReadType.SHORT_READ.value, "tgs"),
        (SeqLibraryPrepCategory.WHOLE_EXOME_SEQUENCING.value, ReadType.SHORT_READ.value, "wes"),
        (SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING.value, ReadType.SHORT_READ.value, "wgs"),
        (
            SeqLibraryPrepCategory.WHOLE_TRANSCRIPTOME_SEQUENCING.value,
            ReadType.SHORT_READ.value,
            "wts",
        ),
    ],
)
def test_application_analysis_type_short_read(
    prep_category: str, read_type: str, expected_analysis_type: str
):
    # GIVEN an application
    application = Application(
        prep_category=prep_category,
        read_type=read_type,
    )

    # WHEN getting the analysis type
    # THEN it returns the expected analysis type
    assert application.analysis_type == expected_analysis_type


@pytest.mark.parametrize(
    "prep_category, read_type, expected_analysis_type",
    [
        (SeqLibraryPrepCategory.COVID.value, ReadType.LONG_READ.value, "cov-lr"),
        (SeqLibraryPrepCategory.MICROBIAL.value, ReadType.LONG_READ.value, "mic-lr"),
        (SeqLibraryPrepCategory.READY_MADE_LIBRARY.value, ReadType.LONG_READ.value, "rml-lr"),
        (
            SeqLibraryPrepCategory.TARGETED_GENOME_SEQUENCING.value,
            ReadType.LONG_READ.value,
            "tgs-lr",
        ),
        (SeqLibraryPrepCategory.WHOLE_EXOME_SEQUENCING.value, ReadType.LONG_READ.value, "wes-lr"),
        (SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING.value, ReadType.LONG_READ.value, "wgs-lr"),
        (
            SeqLibraryPrepCategory.WHOLE_TRANSCRIPTOME_SEQUENCING.value,
            ReadType.LONG_READ.value,
            "wts-lr",
        ),
    ],
)
def test_application_analysis_type_long_read(
    prep_category: str, read_type: str, expected_analysis_type: str
):
    # GIVEN an application
    application = Application(
        prep_category=prep_category,
        read_type=read_type,
    )

    # WHEN getting the analysis type
    # THEN it returns the expected analysis type
    assert application.analysis_type == expected_analysis_type


@pytest.mark.parametrize(
    "prep_category, read_type, expected_analysis_type",
    [
        (SeqLibraryPrepCategory.COVID.value, ReadType.OPTICAL_MAPPING.value, "cov-om"),
        (SeqLibraryPrepCategory.MICROBIAL.value, ReadType.OPTICAL_MAPPING.value, "mic-om"),
        (SeqLibraryPrepCategory.READY_MADE_LIBRARY.value, ReadType.OPTICAL_MAPPING.value, "rml-om"),
        (
            SeqLibraryPrepCategory.TARGETED_GENOME_SEQUENCING.value,
            ReadType.OPTICAL_MAPPING.value,
            "tgs-om",
        ),
        (
            SeqLibraryPrepCategory.WHOLE_EXOME_SEQUENCING.value,
            ReadType.OPTICAL_MAPPING.value,
            "wes-om",
        ),
        (
            SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING.value,
            ReadType.OPTICAL_MAPPING.value,
            "wgs-om",
        ),
        (
            SeqLibraryPrepCategory.WHOLE_TRANSCRIPTOME_SEQUENCING.value,
            ReadType.OPTICAL_MAPPING.value,
            "wts-om",
        ),
    ],
)
def test_application_analysis_type_optical_mapping(
    prep_category: str, read_type: str, expected_analysis_type: str
):
    # GIVEN an application
    application = Application(
        prep_category=prep_category,
        read_type=read_type,
    )

    # WHEN getting the analysis type
    # THEN it returns the expected analysis type
    assert application.analysis_type == expected_analysis_type


def test_application_expected_hifi_yield_no_target_hifi_yield():
    # GIVEN an application without target_hifi_yield
    application = Application(
        target_hifi_yield=None,
        percent_hifi_yield_guaranteed=None,
    )

    # WHEN getting the expected HiFi yield
    expected_hifi_yield: float | None = application.expected_hifi_yield

    # THEN the value should be None
    assert expected_hifi_yield is None


def test_sample_to_dict_pacbio_success():
    # GIVEN a PacBio sample with application, customer, sequencing_metrics, priority and a case
    application = Application(tag="PACBIOTAG")
    application_version = ApplicationVersion(application=application)
    customer = Customer(internal_id="cust000")
    case_sample = CaseSample(case_id=666)
    metrics = PacbioSampleSequencingMetrics(hifi_yield=13)
    sample = Sample(
        application_version=application_version,
        customer=customer,
        priority=Priority.standard,
        _sample_run_metrics=[metrics],
        links=[case_sample],
    )

    # WHEN serialising the sample
    dict_sample = sample.to_dict()

    # THEN the serialised sample has the expected entries
    assert dict_sample["priority"] == "standard"
    assert dict_sample["customer"]["internal_id"] == "cust000"
    assert dict_sample["application"]["tag"] == "PACBIOTAG"
    assert dict_sample["application_version"]
    assert dict_sample["hifi_yield"] == 13
    assert not dict_sample["uses_reads"]


def test_sample_to_dict_illumina_success():
    # GIVEN a Illumina sample with application, customer, sequencing_metrics, priority and a case
    application = Application(tag="ILLUMINATAG")
    application_version = ApplicationVersion(application=application)
    customer = Customer(internal_id="cust000")
    case_sample = CaseSample(case_id=666)
    metrics = IlluminaSampleSequencingMetrics()
    sample = Sample(
        application_version=application_version,
        customer=customer,
        priority=Priority.standard,
        _sample_run_metrics=[metrics],
        links=[case_sample],
        reads=13,
    )

    # WHEN serialising the sample
    dict_sample = sample.to_dict()

    # THEN the serialised sample has the expected entries
    assert dict_sample["priority"] == "standard"
    assert dict_sample["customer"]["internal_id"] == "cust000"
    assert dict_sample["application"]["tag"] == "ILLUMINATAG"
    assert dict_sample["application_version"]
    assert dict_sample["hifi_yield"] is None
    assert dict_sample["reads"] == 13
    assert dict_sample["uses_reads"]
