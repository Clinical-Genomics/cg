import logging
from datetime import datetime

import pytest
from sqlalchemy.orm import Query

from cg.constants import SequencingRunDataAvailability
from cg.constants.constants import CaseActions, MicrosaltAppTags, Workflow
from cg.constants.subject import PhenotypeStatus
from cg.exc import CgError
from cg.server.dto.orders.orders_request import OrdersRequest
from cg.store.models import (
    Analysis,
    Application,
    ApplicationLimitations,
    ApplicationVersion,
    Bed,
    BedVersion,
    Case,
    CaseSample,
    Collaboration,
    Customer,
    IlluminaSampleSequencingMetrics,
    IlluminaSequencingRun,
    Invoice,
    Order,
    Organism,
    Pool,
    Sample,
    User,
)
from cg.store.store import Store
from tests.store.conftest import StoreConstants
from tests.store_helpers import StoreHelpers


def test_get_bed_by_entry_id(base_store: Store, entry_id: int = 1):
    """Test returning panel bed by entry id."""

    # GIVEN a store with bed records

    # WHEN getting the query for the bed
    bed: Bed = base_store.get_bed_by_entry_id(entry_id)

    # THEN return a bed with the supplied bed id
    assert bed.id == entry_id


def test_get_bed_by_bed_name(base_store: Store, bed_name: str):
    """Test returning panel bed by name."""

    # GIVEN a store with bed records

    # WHEN getting the query for the bed
    bed: Bed = base_store.get_bed_by_name(bed_name)

    # THEN return a bed with the supplied bed id
    assert bed.name == bed_name


def test_get_active_beds(base_store: Store):
    """Test returning not archived bed records from the database."""

    # GIVEN a store with beds

    # WHEN fetching beds
    beds: Query = base_store.get_active_beds()

    # THEN beds should have been returned
    assert beds

    # THEN the bed records should not be archived
    for bed in beds:
        assert bed.is_archived is False


def test_get_active_beds_when_archived(base_store: Store):
    """Test returning not archived bed records from the database when archived."""

    # GIVEN a store with beds
    beds: Query = base_store.get_active_beds()
    for bed in beds:
        bed.is_archived = True
        base_store.session.add(bed)
        base_store.session.commit()

    # WHEN fetching beds
    active_beds: Query = base_store.get_active_beds()

    # THEN return no beds
    assert not list(active_beds)


def test_get_application_by_tag(microbial_store: Store, tag: str = MicrosaltAppTags.MWRNXTR003):
    """Test function to return the application by tag."""

    # GIVEN a store with application records

    # WHEN getting the query for the flow cells
    application: Application = microbial_store.get_application_by_tag(tag=tag)

    # THEN return a application with the supplied application tag
    assert application.tag == tag


def test_get_applications_is_not_archived(
    microbial_store: Store, expected_number_of_not_archived_applications
):
    """Test function to return the application when not archived."""

    # GIVEN a store with application records

    # WHEN getting the query for the flow cells
    applications: list[Application] = microbial_store.get_applications_is_not_archived()

    # THEN return an application with the supplied application tag
    assert len(applications) == expected_number_of_not_archived_applications
    for application in applications:
        assert not application.is_archived


def test_case_in_uploaded_observations(helpers: StoreHelpers, sample_store: Store, loqusdb_id: str):
    """Test retrieval of uploaded observations."""

    # GIVEN a case with observations that has been uploaded to Loqusdb
    analysis: Analysis = helpers.add_analysis(store=sample_store, workflow=Workflow.MIP_DNA)
    analysis.case.customer.loqus_upload = True
    sample: Sample = helpers.add_sample(sample_store, loqusdb_id=loqusdb_id)
    link = sample_store.relate_sample(analysis.case, sample, PhenotypeStatus.UNKNOWN)
    sample_store.session.add(link)
    assert analysis.case.analyses
    for link in analysis.case.links:
        assert link.sample.loqusdb_id is not None

    # WHEN getting observations to upload
    uploaded_observations: Query = sample_store.observations_uploaded()

    # THEN the case should be in the returned query
    assert analysis.case in uploaded_observations


def test_case_not_in_uploaded_observations(helpers: StoreHelpers, sample_store: Store):
    """Test retrieval of uploaded observations that have not been uploaded to Loqusdb."""

    # GIVEN a case with observations that has not been uploaded to loqusdb
    analysis: Analysis = helpers.add_analysis(store=sample_store, workflow=Workflow.MIP_DNA)
    analysis.case.customer.loqus_upload = True
    sample: Sample = helpers.add_sample(sample_store)
    link = sample_store.relate_sample(analysis.case, sample, PhenotypeStatus.UNKNOWN)
    sample_store.session.add(link)
    assert analysis.case.analyses
    for link in analysis.case.links:
        assert link.sample.loqusdb_id is None

    # WHEN getting observations to upload
    uploaded_observations: Query = sample_store.observations_uploaded()

    # THEN the case should not be in the returned query
    assert analysis.case not in uploaded_observations


def test_case_in_observations_to_upload(helpers: StoreHelpers, sample_store: Store):
    """Test extraction of ready to be uploaded to Loqusdb cases."""

    # GIVEN a case with completed analysis and samples w/o loqusdb_id
    analysis: Analysis = helpers.add_analysis(store=sample_store, workflow=Workflow.MIP_DNA)
    analysis.case.customer.loqus_upload = True
    sample: Sample = helpers.add_sample(sample_store)
    link = sample_store.relate_sample(analysis.case, sample, PhenotypeStatus.UNKNOWN)
    sample_store.session.add(link)
    assert analysis.case.analyses
    for link in analysis.case.links:
        assert link.sample.loqusdb_id is None

    # WHEN getting observations to upload
    observations_to_upload: Query = sample_store.observations_to_upload()

    # THEN the case should be in the returned query
    assert analysis.case in observations_to_upload


def test_case_not_in_observations_to_upload(
    helpers: StoreHelpers, sample_store: Store, loqusdb_id: str
):
    """Test case extraction that should not be uploaded to Loqusdb."""

    # GIVEN a case with completed analysis and samples with a Loqusdb ID
    analysis: Analysis = helpers.add_analysis(store=sample_store, workflow=Workflow.MIP_DNA)
    analysis.case.customer.loqus_upload = True
    sample: Sample = helpers.add_sample(sample_store, loqusdb_id=loqusdb_id)
    link = sample_store.relate_sample(analysis.case, sample, PhenotypeStatus.UNKNOWN)
    sample_store.session.add(link)
    assert analysis.case.analyses
    for link in analysis.case.links:
        assert link.sample.loqusdb_id is not None

    # WHEN getting observations to upload
    observations_to_upload: Query = sample_store.observations_to_upload()

    # THEN the case should not be in the returned query
    assert analysis.case not in observations_to_upload


def test_analyses_to_upload_when_not_completed_at(helpers, sample_store):
    """Test analyses to upload with no completed_at date."""
    # GIVEN a store with an analysis without a completed_at date
    helpers.add_analysis(store=sample_store)

    # WHEN fetching all analyses that are ready for upload
    records: list[Analysis] = [
        analysis_obj for analysis_obj in sample_store.get_analyses_to_upload()
    ]

    # THEN no analysis object should be returned since they did not have a completed_at entry
    assert len(records) == 0


def test_analyses_to_upload_when_no_workflow(helpers, sample_store, timestamp):
    """Test analyses to upload with no workflow specified."""
    # GIVEN a store with one analysis
    helpers.add_analysis(store=sample_store, completed_at=timestamp)

    # WHEN fetching all analysis that are ready for upload without specifying workflow
    records: list[Analysis] = [
        analysis_obj for analysis_obj in sample_store.get_analyses_to_upload(workflow=None)
    ]

    # THEN one analysis object should be returned
    assert len(records) == 1


def test_analyses_to_upload_when_analysis_has_workflow(helpers, sample_store, timestamp):
    """Test analyses to upload to when existing workflow."""
    # GIVEN a store with an analysis that has been run with MIP
    helpers.add_analysis(store=sample_store, completed_at=timestamp, workflow=Workflow.MIP_DNA)

    # WHEN fetching all analyses that are ready for upload and analysed with MIP
    records: list[Analysis] = [
        analysis_obj for analysis_obj in sample_store.get_analyses_to_upload(workflow=None)
    ]

    # THEN one analysis object should be returned
    assert len(records) == 1


def test_analyses_to_upload_when_filtering_with_workflow(helpers, sample_store, timestamp):
    """Test analyses to upload to when existing workflow and using it in filtering."""
    # GIVEN a store with an analysis that is analysed with MIP
    workflow = Workflow.MIP_DNA
    helpers.add_analysis(store=sample_store, completed_at=timestamp, workflow=workflow)

    # WHEN fetching all workflows that are analysed with MIP
    records: list[Analysis] = [
        analysis_obj for analysis_obj in sample_store.get_analyses_to_upload(workflow=workflow)
    ]

    for analysis_obj in records:
        # THEN the workflow should be MIP in the analysis object
        assert analysis_obj.workflow == workflow


def test_analyses_to_upload_with_workflow_and_no_complete_at(helpers, sample_store, timestamp):
    """Test analyses to upload to when existing workflow and using it in filtering."""
    # GIVEN a store with an analysis that is analysed with MIP but does not have a completed_at
    pipeline = Workflow.MIP_DNA
    helpers.add_analysis(store=sample_store, completed_at=None, workflow=pipeline)

    # WHEN fetching all analyses that are ready for upload and analysed by MIP
    records: list[Analysis] = [
        analysis_obj for analysis_obj in sample_store.get_analyses_to_upload(workflow=pipeline)
    ]

    # THEN no analysis object should be returned since they were not completed
    assert len(records) == 0


def test_analyses_to_upload_when_filtering_with_missing_workflow(helpers, sample_store, timestamp):
    """Test analyses to upload to when missing workflow and using it in filtering."""
    # GIVEN a store with an analysis that has been analysed with "missing_pipeline"
    helpers.add_analysis(store=sample_store, completed_at=timestamp, workflow=Workflow.MIP_DNA)

    # WHEN fetching all analyses that was analysed with MIP
    records: list[Analysis] = [
        analysis_obj
        for analysis_obj in sample_store.get_analyses_to_upload(workflow=Workflow.RAW_DATA)
    ]

    # THEN no analysis object should be returned, since there were no MIP analyses
    assert len(records) == 0


def test_set_case_action(analysis_store: Store, case_id):
    """Tests if actions of cases are changed to analyze."""
    # Given a store with a case with action None
    action = analysis_store.get_case_by_internal_id(internal_id=case_id).action

    assert action is None

    # When setting the case to "analyze"
    analysis_store.set_case_action(case_internal_id=case_id, action="analyze")
    new_action = analysis_store.get_case_by_internal_id(internal_id=case_id).action

    # Then the action should be set to analyze
    assert new_action == "analyze"


def test_get_applications(microbial_store: Store, expected_number_of_applications):
    """Test function to return the applications."""

    # GIVEN a store with application records

    # WHEN getting the query for the flow cells
    applications: list[Application] = microbial_store.get_applications()

    # THEN return an application with the supplied application tag
    assert len(applications) == expected_number_of_applications


def test_get_bed_version_query(base_store: Store):
    """Test function to return the bed version query."""

    # GIVEN a store with bed versions records

    # WHEN getting the query for the bed versions
    bed_version_query: Query = base_store._get_query(table=BedVersion)

    # THEN a query should be returned
    assert isinstance(bed_version_query, Query)


def test_get_bed_version_by_file_name(base_store: Store, bed_version_file_name: str):
    """Test function to return the bed version by file name."""

    # GIVEN a store with bed versions records

    # WHEN getting the query for the bed versions
    bed_version: BedVersion = base_store.get_bed_version_by_file_name(
        bed_version_file_name=bed_version_file_name
    )

    # THEN return a bed version with the supplied bed version file_name
    assert bed_version.filename == bed_version_file_name


def test_get_bed_version_by_short_name(base_store: Store, bed_version_short_name: str):
    """Test function to return the bed version by short name."""

    # GIVEN a store with bed versions records

    # WHEN getting the query for the bed versions
    bed_version: BedVersion = base_store.get_bed_version_by_short_name(
        bed_version_short_name=bed_version_short_name
    )

    # THEN return a bed version with the supplied bed version short name
    assert bed_version.shortname == bed_version_short_name


def test_get_customer_by_internal_id(base_store: Store, customer_id: str):
    """Test function to return the customer by customer id."""

    # GIVEN a store with customer records

    # WHEN getting the query for the customer
    customer: Customer = base_store.get_customer_by_internal_id(customer_internal_id=customer_id)

    # THEN return a customer with the supplied customer internal id
    assert customer.internal_id == customer_id


def test_get_customers(base_store: Store, customer_id: str):
    """Test function to return customers."""

    # GIVEN a store with customer records

    # WHEN getting the customers
    customers: list[Customer] = base_store.get_customers()

    # THEN return customers
    assert customers

    # THEN return a customer with the database customer internal id
    assert customers[0].internal_id == customer_id


def test_get_collaboration_by_internal_id(base_store: Store, collaboration_id: str):
    """Test function to return the collaborations by internal_id."""

    # GIVEN a store with collaborations

    # WHEN getting the query for the collaborations
    collaboration: Collaboration = base_store.get_collaboration_by_internal_id(
        internal_id=collaboration_id
    )

    # THEN return a collaboration with the give collaboration internal_id
    assert collaboration.internal_id == collaboration_id


def test_get_organism_by_internal_id_returns_correct_organism(store_with_organisms: Store):
    """Test finding an organism by internal ID when the ID exists."""

    # GIVEN a store with multiple organisms
    organisms: Query = store_with_organisms._get_query(table=Organism)
    assert organisms.count() > 0

    # GIVEN a random organism from the store
    organism: Organism = organisms.first()
    assert isinstance(organism, Organism)

    # WHEN finding the organism by internal ID
    filtered_organism = store_with_organisms.get_organism_by_internal_id(organism.internal_id)

    # THEN the filtered organism should be of instance Organism
    assert isinstance(filtered_organism, Organism)

    # THEN the filtered organism should match the database organism internal id
    assert filtered_organism.internal_id == organism.internal_id


def test_get_organism_by_internal_id_returns_none_when_id_does_not_exist(
    store_with_organisms: Store,
    non_existent_id: str,
):
    """Test finding an organism by internal ID when the ID does not exist."""

    # GIVEN a store with multiple organisms
    organisms: Query = store_with_organisms._get_query(table=Organism)
    assert organisms.count() > 0

    # WHEN finding the organism by internal ID that does not exist
    filtered_organism: Organism = store_with_organisms.get_organism_by_internal_id(
        internal_id=non_existent_id
    )

    # THEN the filtered organism should be None
    assert filtered_organism is None


def test_get_organism_by_internal_id_returns_none_when_id_is_none(
    store_with_organisms: Store,
):
    """Test finding an organism by internal ID None returns None."""

    # GIVEN a store with multiple organisms
    organisms: Query = store_with_organisms._get_query(table=Organism)
    assert organisms.count() > 0

    # WHEN finding the organism by internal ID None
    filtered_organism: Organism = store_with_organisms.get_organism_by_internal_id(internal_id=None)

    # THEN the filtered organism should be None
    assert filtered_organism is None


def test_get_user_by_email_returns_correct_user(store_with_users: Store):
    """Test fetching a user by email."""

    # GIVEN a store with multiple users
    num_users: int = store_with_users._get_query(table=User).count()
    assert num_users > 0

    # Select a random user from the store
    user: User = store_with_users._get_query(table=User).first()
    assert user is not None

    # WHEN fetching the user by email
    filtered_user: User = store_with_users.get_user_by_email(email=user.email)

    # THEN a user should be returned
    assert isinstance(filtered_user, User)

    # THEN the email should match
    assert filtered_user.email == user.email


def test_get_user_by_email_returns_none_for_nonexisting_email(
    store_with_users: Store, non_existent_email: str
):
    """Test getting user by email when the email does not exist."""

    # GIVEN a non-existing email

    # WHEN retrieving the user by email
    filtered_user: User = store_with_users.get_user_by_email(email=non_existent_email)

    # THEN no user should be returned
    assert filtered_user is None


def test_get_user_when_email_is_none_returns_none(store_with_users: Store):
    """Test getting user by email when the email is None."""

    # WHEN retrieving filtering by email None
    filtered_user: User = store_with_users.get_user_by_email(email=None)

    # THEN no user should be returned
    assert filtered_user is None


def test_get_analysis_by_case_entry_id_and_started_at(
    sample_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test returning an analysis using a date."""
    # GIVEN a case with an analysis with a start date in the database
    analysis = helpers.add_analysis(store=sample_store, started_at=timestamp_now)
    assert analysis.started_at

    # WHEN getting analysis via case_id and start date
    db_analysis = sample_store.get_analysis_by_case_entry_id_and_started_at(
        case_entry_id=analysis.case.id, started_at_date=analysis.started_at
    )

    # THEN the analysis should have been retrieved
    assert db_analysis == analysis


def test_get_illumina_sequencing_runs_by_case(
    store_with_illumina_sequencing_data: Store,
    selected_novaseq_x_case_ids: str,
):
    """Test returning a sequencing run from the database by case."""

    # GIVEN a store with a sequencing run

    # WHEN fetching the a sequencing run by case
    sequencing_runs: list[IlluminaSequencingRun] = (
        store_with_illumina_sequencing_data.get_illumina_sequencing_runs_by_case(
            selected_novaseq_x_case_ids[0]
        )
    )

    # THEN a list of sequencing runs should be returned
    assert sequencing_runs


def test_get_samples_from_illumina_flow_cell_internal_id(
    novaseq_x_flow_cell_id: str, store_with_illumina_sequencing_data: Store
):
    """Test getting samples from an Illumina flow cell by internal ID"""
    # GIVEN a store with an Illumina flow cell and samples

    # WHEN fetching the samples from the flow cell
    samples: list[Sample] = store_with_illumina_sequencing_data.get_samples_by_illumina_flow_cell(
        flow_cell_id=novaseq_x_flow_cell_id
    )

    # THEN a list of samples should be returned
    assert isinstance(samples, list)
    assert isinstance(samples[0], Sample)

    # THEN the samples should be from the flow cell
    assert samples[0].run_devices[0].internal_id == novaseq_x_flow_cell_id


def test_is_all_illumina_runs_on_disk_when_no_illumina_run(
    store_with_illumina_sequencing_data: Store,
    selected_novaseq_x_case_ids: str,
):
    """Test check if all sequencing runs for samples on a case are on disk when there are no sequencing runs."""
    # GIVEN a store with a case that has no sequencing runs
    sequencing_runs: list[IlluminaSequencingRun] = (
        store_with_illumina_sequencing_data.get_illumina_sequencing_runs_by_case(
            selected_novaseq_x_case_ids[0]
        )
    )
    assert sequencing_runs
    store_with_illumina_sequencing_data.delete_illumina_flow_cell(
        sequencing_runs[0].device.internal_id
    )
    deleted_run: list[IlluminaSequencingRun] = (
        store_with_illumina_sequencing_data.get_illumina_sequencing_runs_by_case(
            selected_novaseq_x_case_ids[0]
        )
    )
    assert not deleted_run

    # WHEN fetching the illumina runs for a case
    is_on_disk = store_with_illumina_sequencing_data.are_all_illumina_runs_on_disk(
        case_id=selected_novaseq_x_case_ids[0]
    )

    # THEN return false
    assert is_on_disk is False


def test_are_all_illumina_runs_on_disk_when_not_on_disk(
    store_with_illumina_sequencing_data_on_disk: Store,
    selected_novaseq_x_case_ids: str,
):
    """Test check if all sequencing runs on a case is on disk when not on disk."""
    # GIVEN a store with two sequencing runs on a case that are not on disk
    sequencing_runs: list[IlluminaSequencingRun] = (
        store_with_illumina_sequencing_data_on_disk.get_illumina_sequencing_runs_by_case(
            selected_novaseq_x_case_ids[0]
        )
    )
    assert sequencing_runs
    assert len(sequencing_runs) == 2
    for sequencing_run in sequencing_runs:
        sequencing_run.data_availability = SequencingRunDataAvailability.RETRIEVED

    # WHEN fetching the sequencing runs for a case
    is_on_disk = store_with_illumina_sequencing_data_on_disk.are_all_illumina_runs_on_disk(
        case_id=selected_novaseq_x_case_ids[0]
    )

    # THEN return false
    assert is_on_disk is False


def test_are_all_illumina_runs_on_disk(
    store_with_illumina_sequencing_data_on_disk: Store,
    selected_novaseq_x_case_ids: str,
):
    """Test check if all sequencing runs on a case is on disk."""
    # GIVEN a store with two sequencing runs on a case that are on disk
    sequencing_runs: list[IlluminaSequencingRun] = (
        store_with_illumina_sequencing_data_on_disk.get_illumina_sequencing_runs_by_case(
            selected_novaseq_x_case_ids[0]
        )
    )
    assert sequencing_runs
    assert len(sequencing_runs) == 2
    for sequencing_run in sequencing_runs:
        assert sequencing_run.data_availability == SequencingRunDataAvailability.ON_DISK

    # WHEN fetching the sequencing runs for a case
    is_on_disk = store_with_illumina_sequencing_data_on_disk.are_all_illumina_runs_on_disk(
        case_id=selected_novaseq_x_case_ids[0]
    )

    # THEN return True
    assert is_on_disk is True


def test_get_customer_id_from_ticket(analysis_store, customer_id, ticket_id: str):
    """Tests if the function in fact returns the correct customer."""
    # Given a store with a ticket

    # Then the function should return the customer connected to the ticket
    assert analysis_store.get_customer_id_from_ticket(ticket_id) == customer_id


def test_get_latest_ticket_from_case(case_id: str, analysis_store_single_case, ticket_id: str):
    """Tests if the correct ticket is returned for the given case."""
    # GIVEN a populated store with a case

    # WHEN the function is called
    ticket_from_case: str = analysis_store_single_case.get_latest_ticket_from_case(case_id=case_id)

    # THEN the ticket should be correct
    assert ticket_id == ticket_from_case


def test_get_ready_made_library_expected_reads(case_id: str, rml_pool_store: Store):
    """Test if the correct number of expected reads is returned."""

    # GIVEN a case with a sample with an application version
    application_version: ApplicationVersion = (
        rml_pool_store.get_case_by_internal_id(internal_id=case_id)
        .links[0]
        .sample.application_version
    )

    # WHEN the expected reads is fetched from the case
    expected_reads: int = rml_pool_store.get_ready_made_library_expected_reads(case_id=case_id)

    # THEN the fetched reads should be equal to the expected reads of the application versions application
    assert application_version.application.expected_reads == expected_reads


def test_get_application_by_case(case_id: str, rml_pool_store: Store):
    """Test that the correct application is returned on a case."""
    # GIVEN a case with a sample with an application version
    application_version: ApplicationVersion = (
        rml_pool_store.get_case_by_internal_id(internal_id=case_id)
        .links[0]
        .sample.application_version
    )

    # WHEN the application is fetched from the case
    application: Application = rml_pool_store.get_application_by_case(case_id=case_id)

    # THEN the fetched application should be equal to the application version application
    assert application_version.application == application


def test_get_application_limitations_by_tag(
    store_with_application_limitations: Store,
    tag: str = StoreConstants.TAG_APPLICATION_WITHOUT_ATTRIBUTES.value,
):
    """Test get application limitations by application tag."""

    # GIVEN a store with some application limitations

    # WHEN filtering by a given application tag
    application_limitations: list[ApplicationLimitations] = (
        store_with_application_limitations.get_application_limitations_by_tag(tag=tag)
    )

    # THEN assert that the application limitations were found
    assert (
        application_limitations
        and len(application_limitations) == 2
        and [
            application_limitation.application.tag == tag
            for application_limitation in application_limitations
        ]
    )


def test_get_application_limitation_by_tag_and_workflow(
    store_with_application_limitations: Store,
    tag: str = StoreConstants.TAG_APPLICATION_WITH_ATTRIBUTES.value,
    workflow: Workflow = Workflow.MIP_DNA,
):
    """Test get application limitations by application tag and workflow."""

    # GIVEN a store with some application limitations

    # WHEN filtering by a given application tag and workflow
    application_limitation: ApplicationLimitations = (
        store_with_application_limitations.get_application_limitation_by_tag_and_workflow(
            tag=tag, workflow=workflow
        )
    )

    # THEN assert that the application limitation was found
    assert (
        application_limitation
        and application_limitation.application.tag == tag
        and application_limitation.workflow == workflow
    )


def test_get_case_samples_by_case_id(
    store_with_analyses_for_cases: Store,
    case_id: str,
):
    """Test that getting case-samples by case id returns a list of CaseSamples."""
    # GIVEN a store with case-samples and a case id

    # WHEN fetching the case-samples matching the case id
    case_samples: list[CaseSample] = store_with_analyses_for_cases.get_case_samples_by_case_id(
        case_internal_id=case_id
    )

    # THEN a list of case-samples should be returned
    assert case_samples
    assert isinstance(case_samples, list)
    assert isinstance(case_samples[0], CaseSample)


def test_get_case_sample_link(
    store_with_analyses_for_cases: Store,
    case_id: str,
    sample_id: str,
):
    """Test that the returned element is a CaseSample with the correct case and sample internal ids."""
    # GIVEN a store with case-samples and valid case and sample internal ids

    # WHEN fetching a case-sample with case and sample internal ids
    case_sample: CaseSample = store_with_analyses_for_cases.get_case_sample_link(
        case_internal_id=case_id,
        sample_internal_id=sample_id,
    )

    # THEN the returned element is a CaseSample
    assert isinstance(case_sample, CaseSample)

    # THEN the returned family sample has the correct case and sample internal ids
    assert case_sample.case.internal_id == case_id
    assert case_sample.sample.internal_id == sample_id


def test_find_cases_for_non_existing_case(store_with_multiple_cases_and_samples: Store):
    """Test that nothing happens when trying to find a case that does not exist."""

    # GIVEN a database containing some cases but not a specific case
    case_id: str = "some_case"
    case: Case = store_with_multiple_cases_and_samples.get_case_by_internal_id(internal_id=case_id)

    assert not case

    # WHEN trying to find cases with samples given the non existing case id
    cases = store_with_multiple_cases_and_samples.filter_cases_with_samples(case_ids=[case_id])

    # THEN no cases are found
    assert not cases


def test_verify_case_exists(
    caplog, case_id_with_multiple_samples: str, store_with_multiple_cases_and_samples: Store
):
    """Test validating a case that exists in the database."""

    caplog.set_level(logging.INFO)

    # GIVEN a database containing the case

    # WHEN validating if the case exists
    store_with_multiple_cases_and_samples.verify_case_exists(
        case_internal_id=case_id_with_multiple_samples
    )

    # THEN the case is found
    assert f"Case {case_id_with_multiple_samples} exists in Status DB" in caplog.text


def test_verify_case_exists_with_non_existing_case(
    case_id_does_not_exist: str, store_with_multiple_cases_and_samples: Store
):
    """Test validating a case that does not exist in the database."""

    # GIVEN a database containing the case

    with pytest.raises(CgError):
        # WHEN validating if the case exists
        store_with_multiple_cases_and_samples.verify_case_exists(
            case_internal_id=case_id_does_not_exist
        )

        # THEN the case is not found


def test_verify_case_exists_with_no_case_samples(
    case_id_without_samples: str, store_with_multiple_cases_and_samples: Store
):
    """Test validating a case without samples that exist in the database."""

    # GIVEN a database containing the case

    with pytest.raises(CgError):
        # WHEN validating if the case exists
        store_with_multiple_cases_and_samples.verify_case_exists(
            case_internal_id=case_id_without_samples
        )

        # THEN the case is found, but has no samples


def test_is_case_down_sampled_true(base_store: Store, case: Case, sample_id: str):
    """Tests the down sampling check when all samples are down sampled."""
    # GIVEN a case where all samples are down sampled
    for sample in case.samples:
        sample.from_sample = sample_id
    base_store.session.commit()

    # WHEN checking if all sample in the case are down sampled
    is_down_sampled: bool = base_store.is_case_down_sampled(case_id=case.internal_id)

    # THEN the return value should be True
    assert is_down_sampled


def test_is_case_down_sampled_false(base_store: Store, case: Case, sample_id: str):
    """Tests the down sampling check when none of the samples are down sampled."""
    # GIVEN a case where all samples are not down sampled
    for sample in case.samples:
        assert not sample.from_sample

    # WHEN checking if all sample in the case are down sampled
    is_down_sampled: bool = base_store.is_case_down_sampled(case_id=case.internal_id)

    # THEN the return value should be False
    assert not is_down_sampled


def test_is_case_external_true(
    base_store: Store, case: Case, helpers: StoreHelpers, sample_id: str
):
    """Tests the external case check when all the samples are external."""
    # GIVEN a case where all samples are not external
    external_application_version: ApplicationVersion = helpers.ensure_application_version(
        store=base_store, is_external=True
    )
    for sample in case.samples:
        sample.application_version = external_application_version
    base_store.session.commit()

    # WHEN checking if all sample in the case are external
    is_external: bool = base_store.is_case_external(case_id=case.internal_id)

    # THEN the return value should be False
    assert is_external


def test_is_case_external_false(base_store: Store, case: Case, sample_id: str):
    """Tests the external case check when none of the samples are external."""
    # GIVEN a case where all samples are not external
    for sample in case.samples:
        assert not sample.application_version.application.is_external

    # WHEN checking if all sample in the case are external
    is_external: bool = base_store.is_case_external(case_id=case.internal_id)

    # THEN the return value should be False
    assert not is_external


def test_get_invoice_by_status(store_with_an_invoice_with_and_without_attributes: Store):
    """Test that invoices can be fetched by status."""
    # GIVEN a database with two invoices of which one has attributes

    # WHEN fetching the invoice by status
    invoices: list[Invoice] = (
        store_with_an_invoice_with_and_without_attributes.get_invoices_by_status(is_invoiced=True)
    )

    # THEN one invoice should be returned
    assert invoices

    # THEN there should be one invoice
    assert len(invoices) == 1

    # THEN the invoice should have that is invoiced
    assert invoices[0].invoiced_at


def test_get_invoice_by_id(store_with_an_invoice_with_and_without_attributes: Store):
    """Test that invoices can be fetched by invoice id."""
    # GIVEN a database with two invoices of which one has attributes

    # WHEN fetching the invoice by invoice id
    invoice: Invoice = store_with_an_invoice_with_and_without_attributes.get_invoice_by_entry_id(
        entry_id=1
    )

    # THEN one invoice should be returned
    assert invoice

    # THEN the invoice should have id 1
    assert invoice.id == 1


def test_get_pools(store_with_multiple_pools_for_customer: Store):
    """Test that pools can be fetched from the store."""
    # GIVEN a database with two pools

    # WHEN getting all pools
    pools: list[Pool] = store_with_multiple_pools_for_customer.get_pools()

    # THEN two pools should be returned
    assert len(pools) == 2


def test_get_pools_by_customer_id(store_with_multiple_pools_for_customer: Store):
    """Test that pools can be fetched from the store by customer id."""
    # GIVEN a database with two pools

    # WHEN getting pools by customer id
    pools: list[Pool] = store_with_multiple_pools_for_customer.get_pools_by_customers(
        customers=store_with_multiple_pools_for_customer.get_customers()
    )

    # THEN two pools should be returned
    assert len(pools) == 2


def test_get_pools_by_name_enquiry(store_with_multiple_pools_for_customer: Store, pool_name_1: str):
    """Test that pools can be fetched from the store by customer id."""
    # GIVEN a database with two pools

    # WHEN fetching pools by customer id
    pools: list[Pool] = store_with_multiple_pools_for_customer.get_pools_by_name_enquiry(
        name_enquiry=pool_name_1
    )

    # THEN one pool should be returned
    assert len(pools) == 1


def test_get_pools_by_order_enquiry(
    store_with_multiple_pools_for_customer: Store, pool_order_1: str
):
    """Test that pools can be fetched from the store by customer id."""
    # GIVEN a database with two pools

    # WHEN getting pools by customer id
    pools: list[Pool] = store_with_multiple_pools_for_customer.get_pools_by_order_enquiry(
        order_enquiry=pool_order_1
    )

    # THEN one pool should be returned
    assert len(pools) == 1


def test_get_pools_to_render_with(
    store_with_multiple_pools_for_customer: Store,
):
    """Test that pools can be fetched from the store by customer id."""
    # GIVEN a database with two pools

    # WHEN fetching pools with no customer or enquiry
    pools: list[Pool] = store_with_multiple_pools_for_customer.get_pools_to_render()

    # THEN two pools should be returned
    assert len(pools) == 2


def test_get_pools_to_render_with_customer(
    store_with_multiple_pools_for_customer: Store,
):
    """Test that pools can be fetched from the store by customer id."""
    # GIVEN a database with two pools

    # WHEN getting pools by customer id
    pools: list[Pool] = store_with_multiple_pools_for_customer.get_pools_to_render(
        customers=store_with_multiple_pools_for_customer.get_customers()
    )

    # THEN two pools should be returned
    assert len(pools) == 2


def test_get_pools_to_render_with_customer_and_name_enquiry(
    store_with_multiple_pools_for_customer: Store,
    pool_name_1: str,
):
    """Test that pools can be fetched from the store by customer id."""
    # GIVEN a database with two pools
    # WHEN fetching pools by customer id and name enquiry
    pools: list[Pool] = store_with_multiple_pools_for_customer.get_pools_to_render(
        customers=store_with_multiple_pools_for_customer.get_customers(), enquiry=pool_name_1
    )

    # THEN one pools should be returned
    assert len(pools) == 1


def test_get_pools_to_render_with_customer_and_order_enquiry(
    store_with_multiple_pools_for_customer: Store,
    pool_order_1: str,
):
    """Test that pools can be fetched from the store by customer id."""
    # GIVEN a database with two pools

    # WHEN fetching pools by customer id and order enquiry

    pools: list[Pool] = store_with_multiple_pools_for_customer.get_pools_to_render(
        customers=store_with_multiple_pools_for_customer.get_customers(), enquiry=pool_order_1
    )

    # THEN one pools should be returned
    assert len(pools) == 1


def test_get_case_by_name_and_customer_case_found(store_with_multiple_cases_and_samples: Store):
    """Test that a case can be found by customer and case name."""
    # GIVEN a database with multiple cases for a customer
    case: Case = store_with_multiple_cases_and_samples._get_query(table=Case).first()
    customer: Customer = store_with_multiple_cases_and_samples._get_query(table=Customer).first()

    assert case.customer == customer

    # WHEN fetching a case by customer and case name
    filtered_case: Case = store_with_multiple_cases_and_samples.get_case_by_name_and_customer(
        customer=customer,
        case_name=case.name,
    )

    # THEN the correct case should be returned
    assert filtered_case is not None
    assert filtered_case.customer_id == customer.id
    assert filtered_case.name == case.name


def test_get_cases_not_analysed_by_sample_internal_id_empty_query(
    store_with_multiple_cases_and_samples: Store, non_existent_id: str
):
    """Test that an empty query is returned if no cases match the sample internal id."""
    # GIVEN a store
    # WHEN getting cases not analysed by the sample internal id
    cases = store_with_multiple_cases_and_samples.get_not_analysed_cases_by_sample_internal_id(
        sample_internal_id=non_existent_id
    )

    # THEN an empty list should be returned
    assert cases == []


def test_get_cases_not_analysed_by_sample_internal_id_multiple_cases(
    store_with_multiple_cases_and_samples: Store,
    sample_id_in_multiple_cases: str,
):
    """Test that multiple cases are returned when more than one case matches the sample internal id."""
    # GIVEN a store with multiple cases having the same sample internal id
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Case)

    # Set all cases to not analysed and HOLD action
    for case in cases_query.all():
        case.action = CaseActions.HOLD

    # WHEN getting cases not analysed by the shared sample internal id
    cases = store_with_multiple_cases_and_samples.get_not_analysed_cases_by_sample_internal_id(
        sample_id_in_multiple_cases
    )

    # THEN multiple cases should be returned
    assert len(cases) > 1

    # Check that all returned cases have the matching sample and are not analysed
    for case in cases:
        assert not case.analyses
        assert any(sample.internal_id == sample_id_in_multiple_cases for sample in case.samples)


def test_get_illumina_metrics_entry_by_device_sample_and_lane(
    store_with_illumina_sequencing_data: Store,
    novaseq_x_flow_cell_id: str,
    selected_novaseq_x_sample_ids: list[str],
):
    """Test that Illumina sample sequencing metrics are filtered by sample, device and lane."""
    # GIVEN a store with Illumina Sample Sequencing Metrics for each sample in the run directories

    # GIVEN a sample id and a lane
    sample_id: str = selected_novaseq_x_sample_ids[0]
    lane: int = 1

    # WHEN fetching an Illumina sample sequencing metrics
    metrics: IlluminaSampleSequencingMetrics = (
        store_with_illumina_sequencing_data.get_illumina_metrics_entry_by_device_sample_and_lane(
            device_internal_id=novaseq_x_flow_cell_id, sample_internal_id=sample_id, lane=lane
        )
    )

    # THEN assert that the correct metrics object is returned
    assert metrics
    assert metrics.sample.internal_id == sample_id
    assert metrics.instrument_run.device.internal_id == novaseq_x_flow_cell_id
    assert metrics.flow_cell_lane == lane


def test_get_illumina_sequencing_run_by_device_internal_id(
    store_with_illumina_sequencing_data: Store,
    novaseq_x_flow_cell_id: str,
):
    """Test that a Illumina sequencing run query is filtered by device internal id."""
    # GIVEN a store with Illumina Sequencing Runs for the canonical Illumina runs

    # WHEN fetching an Illumina sequencing run by device internal id
    run: IlluminaSequencingRun = (
        store_with_illumina_sequencing_data.get_illumina_sequencing_run_by_device_internal_id(
            device_internal_id=novaseq_x_flow_cell_id
        )
    )

    # THEN assert that the correct run object is returned
    assert run
    assert run.device.internal_id == novaseq_x_flow_cell_id


def test_case_with_name_exists(
    store_with_case_and_sample_with_reads: Store, downsample_case_internal_id: str
):
    # GIVEN a store with a case and a sample

    # WHEN checking if a case that is in the store exists
    does_exist: bool = store_with_case_and_sample_with_reads.case_with_name_exists(
        case_name=downsample_case_internal_id,
    )
    # THEN the case does exist
    assert does_exist


def test_case_with_name_does_not_exist(
    store_with_case_and_sample_with_reads: Store,
):
    # GIVEN a store with a case

    # WHEN checking if a case that is not in the store exists
    does_exist: bool = store_with_case_and_sample_with_reads.case_with_name_exists(
        case_name="does_not_exist",
    )
    # THEN the case does not exist
    assert not does_exist


def test_sample_with_id_does_exist(
    store_with_case_and_sample_with_reads: Store, downsample_sample_internal_id_1: str
):
    # GIVEN a store with a sample

    # WHEN checking if a sample that is in the store exists
    does_exist: bool = store_with_case_and_sample_with_reads.sample_with_id_exists(
        sample_id=downsample_sample_internal_id_1
    )

    # THEN the sample does exist
    assert does_exist


def test_sample_with_id_does_not_exist(store_with_case_and_sample_with_reads: Store):
    # GIVEN a store with a sample

    # WHEN checking if a sample that is not in the store exists
    does_exist: bool = store_with_case_and_sample_with_reads.sample_with_id_exists(
        sample_id="does_not_exist"
    )

    # THEN the sample does not exist
    assert not does_exist


def test_get_orders_empty_store(store: Store):
    # GIVEN a store without any orders

    # WHEN fetching orders
    orders, total = store.get_orders(OrdersRequest())

    # THEN none should be returned
    assert not orders
    assert not total


def test_get_orders_populated_store(store: Store, order: Order, order_another: Order):
    # GIVEN a store with two orders

    # WHEN fetching orders
    orders, total = store.get_orders(OrdersRequest())

    # THEN both should be returned
    assert len(orders) == 2
    assert total == 2


def test_get_orders_limited(store: Store, order: Order, order_another: Order):
    # GIVEN a store with two orders
    orders_request = OrdersRequest(pageSize=1, page=1)

    # WHEN fetching a limited amount of orders
    orders, total = store.get_orders(orders_request)

    # THEN only one should be returned
    assert total == 2
    assert len(orders) == 1


def test_get_orders_workflow_filter(
    store: Store, order: Order, order_another: Order, order_balsamic: Order
):
    # GIVEN a store with three orders, one of which is a Balsamic order
    orders_request = OrdersRequest(workflow=Workflow.BALSAMIC)

    # WHEN fetching only balsamic orders
    orders, _ = store.get_orders(orders_request)

    # THEN only one should be returned
    assert len(orders) == 1 and orders[0].workflow == Workflow.BALSAMIC


@pytest.mark.parametrize(
    "limit, expected_returned",
    [(None, 2), (1, 1), (2, 2)],
    ids=[
        "Only workflow filtering",
        "Workflow filtering and maximum one order",
        "Workflow filtering and maximum two orders",
    ],
)
def test_get_orders_mip_dna_and_limit_filter(
    store: Store,
    order: Order,
    order_another: Order,
    order_balsamic: Order,
    limit: int | None,
    expected_returned: int,
):
    # GIVEN a store with three orders, two of which are MIP-DNA orders
    orders_request = OrdersRequest(workflow=Workflow.MIP_DNA, pageSize=limit)
    # WHEN fetching only MIP-DNA orders
    orders, _ = store.get_orders(orders_request)

    # THEN we should get the expected number of orders returned
    assert len(orders) == expected_returned
