import logging
from datetime import datetime

import pytest
from sqlalchemy.orm import Query

from cg.constants import FlowCellStatus, Priority
from cg.constants.constants import CaseActions, MicrosaltAppTags, Workflow
from cg.constants.subject import PhenotypeStatus
from cg.exc import CgError
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
    Flowcell,
    Invoice,
    Order,
    Organism,
    Pool,
    Sample,
    SampleLaneSequencingMetrics,
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
    pipeline = Workflow.MIP_DNA
    helpers.add_analysis(store=sample_store, completed_at=timestamp, workflow=pipeline)

    # WHEN fetching all pipelines that are analysed with MIP
    records: list[Analysis] = [
        analysis_obj for analysis_obj in sample_store.get_analyses_to_upload(workflow=pipeline)
    ]

    for analysis_obj in records:
        # THEN the workflow should be MIP in the analysis object
        assert analysis_obj.pipeline == str(pipeline)


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
        for analysis_obj in sample_store.get_analyses_to_upload(workflow=Workflow.FASTQ)
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


def test_sequencing_qc_priority_express_sample_with_one_half_of_the_reads(
    base_store: Store, helpers, timestamp_now
):
    """Test if priority express sample(s), having more than 50% of the application target reads, pass sample QC."""

    # GIVEN a database with a case which has an express sample with half the number of reads
    sample: Sample = helpers.add_sample(base_store, last_sequenced_at=timestamp_now)
    application: Application = sample.application_version.application
    application.target_reads = 40
    sample.reads = 20
    sample.priority = Priority.express

    # WHEN retrieving the sequencing qc property of a express sample
    sequencing_qc_ok: bool = sample.sequencing_qc

    # THEN the qc property should be True
    assert sequencing_qc_ok


def test_sequencing_qc_priority_standard_sample_with_one_half_of_the_reads(
    base_store: Store, helpers, timestamp_now
):
    """Test if priority standard sample(s), having more than 50% of the application target reads, pass sample QC."""

    # GIVEN a database with a case which has a normal sample with half the number of reads
    sample: Sample = helpers.add_sample(base_store, last_sequenced_at=timestamp_now)
    application: Application = sample.application_version.application
    application.target_reads = 40
    sample.reads = 20
    sample.priority = Priority.standard

    # WHEN retrieving the sequencing qc property of a normal sample
    sequencing_qc_ok: bool = sample.sequencing_qc

    # THEN the qc property should be False
    assert not sequencing_qc_ok


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


def test_get_flow_cell_sample_links_query(re_sequenced_sample_store: Store):
    """Test function to return the flow cell sample links query from the database."""

    # GIVEN a store with two flow cells

    # WHEN getting the query for the flow cells
    flow_cell_query: Query = re_sequenced_sample_store._get_join_flow_cell_sample_links_query()

    # THEN a query should be returned
    assert isinstance(flow_cell_query, Query)


def test_get_flow_cells(re_sequenced_sample_store: Store):
    """Test function to return the flow cells from the database."""

    # GIVEN a store with two flow cells

    # WHEN fetching the flow cells
    flow_cells: list[Flowcell] = re_sequenced_sample_store._get_query(table=Flowcell)

    # THEN a flow cells should be returned
    assert flow_cells

    # THEN a flow cell model should be returned
    assert isinstance(flow_cells[0], Flowcell)


def test_get_flow_cell(bcl2fastq_flow_cell_id: str, re_sequenced_sample_store: Store):
    """Test returning the latest flow cell from the database."""

    # GIVEN a store with two flow cells

    # WHEN fetching the latest flow cell
    flow_cell: Flowcell = re_sequenced_sample_store.get_flow_cell_by_name(
        flow_cell_name=bcl2fastq_flow_cell_id
    )

    # THEN the returned flow cell should have the same name as the one in the database
    assert flow_cell.name == bcl2fastq_flow_cell_id


def test_get_flow_cells_by_case(
    base_store: Store,
    bcl2fastq_flow_cell_id: str,
    bcl_convert_flow_cell_id: str,
    case: Case,
    helpers: StoreHelpers,
    sample: Sample,
):
    """Test returning the latest flow cell from the database by case."""

    # GIVEN a store with two flow cell
    helpers.add_flow_cell(store=base_store, flow_cell_name=bcl2fastq_flow_cell_id, samples=[sample])

    helpers.add_flow_cell(store=base_store, flow_cell_name=bcl_convert_flow_cell_id)

    # WHEN fetching the latest flow cell
    flow_cells: list[Flowcell] = base_store.get_flow_cells_by_case(case=case)

    # THEN the flow cell samples for the case should be returned
    for flow_cell in flow_cells:
        for sample in flow_cell.samples:
            assert sample in case.samples

    # THEN the returned flow cell should have the same name as the one in the database
    assert flow_cells[0].name == bcl2fastq_flow_cell_id


def test_get_flow_cells_by_statuses(
    bcl_convert_flow_cell_id: str, re_sequenced_sample_store: Store
):
    """Test returning the latest flow cell from the database by statuses."""

    # GIVEN a store with two flow cells

    # WHEN fetching the latest flow cell
    flow_cells: list[Flowcell] = re_sequenced_sample_store.get_flow_cells_by_statuses(
        flow_cell_statuses=[FlowCellStatus.ON_DISK, FlowCellStatus.REQUESTED]
    )

    # THEN the flow cell status should be "ondisk"
    for flow_cell in flow_cells:
        assert flow_cell.status == FlowCellStatus.ON_DISK

    # THEN the returned flow cell should have the same name as the one in the database
    assert flow_cells[0].name == bcl_convert_flow_cell_id


def test_get_flow_cells_by_statuses_when_multiple_matches(re_sequenced_sample_store: Store):
    """Test returning the latest flow cell from the database by statuses when multiple matches."""

    # GIVEN a store with two flow cells

    # GIVEN a flow cell that exist in status db with status "requested"
    flow_cells: list[Flowcell] = re_sequenced_sample_store._get_query(table=Flowcell)
    flow_cells[0].status = FlowCellStatus.REQUESTED
    re_sequenced_sample_store.session.add(flow_cells[0])
    re_sequenced_sample_store.session.commit()

    # WHEN fetching the latest flow cell
    flow_cells: list[Flowcell] = re_sequenced_sample_store.get_flow_cells_by_statuses(
        flow_cell_statuses=[FlowCellStatus.ON_DISK, FlowCellStatus.REQUESTED]
    )

    # THEN the flow cell status should be "ondisk" or "requested"
    for flow_cell in flow_cells:
        assert flow_cell.status in [FlowCellStatus.ON_DISK, FlowCellStatus.REQUESTED]

    # THEN the returned flow cell should have the same status as the ones in the database
    assert flow_cells[0].status == FlowCellStatus.REQUESTED

    assert flow_cells[1].status == FlowCellStatus.ON_DISK


def test_get_flow_cells_by_statuses_when_incorrect_status(re_sequenced_sample_store: Store):
    """Test returning the latest flow cell from the database when no flow cell with incorrect status."""

    # GIVEN a store with two flow cells

    # WHEN fetching the latest flow cell
    flow_cells: list[Flowcell] = re_sequenced_sample_store.get_flow_cells_by_statuses(
        flow_cell_statuses=["does_not_exist"]
    )

    # THEN no flow cells should be returned
    assert not list(flow_cells)


def test_get_flow_cell_by_enquiry_and_status(
    bcl2fastq_flow_cell_id: str, re_sequenced_sample_store: Store
):
    """Test returning the latest flow cell from the database by enquiry and status."""

    # GIVEN a store with two flow cells

    # WHEN fetching the latest flow cell
    flow_cell: list[Flowcell] = re_sequenced_sample_store.get_flow_cell_by_name_pattern_and_status(
        flow_cell_statuses=[FlowCellStatus.ON_DISK], name_pattern=bcl2fastq_flow_cell_id[:4]
    )

    # THEN the returned flow cell should have the same name as the one in the database
    assert flow_cell[0].name == bcl2fastq_flow_cell_id

    # THEN the returned flow cell should have the same status as the query
    assert flow_cell[0].status == FlowCellStatus.ON_DISK


def test_get_samples_from_flow_cell(
    bcl2fastq_flow_cell_id: str, sample_id: str, re_sequenced_sample_store: Store
):
    """Test returning samples present on the latest flow cell from the database."""

    # GIVEN a store with two flow cells

    # WHEN fetching the samples from the latest flow cell
    samples: list[Sample] = re_sequenced_sample_store.get_samples_from_flow_cell(
        flow_cell_id=bcl2fastq_flow_cell_id
    )

    # THEN the returned sample id should have the same id as the one in the database
    assert samples[0].internal_id == sample_id


def test_get_latest_flow_cell_on_case(
    re_sequenced_sample_store: Store, case_id: str, bcl2fastq_flow_cell_id: str
):
    """Test returning the latest sequenced flow cell on a case."""

    # GIVEN a store with two flow cells in it, one being the latest sequenced of the two
    latest_flow_cell: Flowcell = re_sequenced_sample_store.get_flow_cell_by_name(
        flow_cell_name=bcl2fastq_flow_cell_id
    )

    # WHEN fetching the latest flow cell on a case with a sample that has been sequenced on both flow cells
    latest_flow_cell_on_case: Flowcell = re_sequenced_sample_store.get_latest_flow_cell_on_case(
        family_id=case_id
    )

    # THEN the fetched flow cell should have the same name as the other
    assert latest_flow_cell.name == latest_flow_cell_on_case.name


def test_is_all_flow_cells_on_disk_when_no_flow_cell(
    base_store: Store,
    caplog,
    case_id: str,
):
    """Test check if all flow cells for samples on a case is on disk when no flow cells."""
    caplog.set_level(logging.DEBUG)

    # WHEN fetching the latest flow cell
    is_on_disk = base_store.are_all_flow_cells_on_disk(case_id=case_id)

    # THEN return false
    assert is_on_disk is False

    # THEN log no flow cells found
    assert "No flow cells found" in caplog.text


def test_are_all_flow_cells_on_disk_when_not_on_disk(
    base_store: Store,
    caplog,
    bcl2fastq_flow_cell_id: str,
    bcl_convert_flow_cell_id: str,
    case_id: str,
    helpers: StoreHelpers,
    sample: Sample,
):
    """Test check if all flow cells for samples on a case is on disk when not on disk."""
    caplog.set_level(logging.DEBUG)
    # GIVEN a store with two flow cell
    helpers.add_flow_cell(
        store=base_store,
        flow_cell_name=bcl2fastq_flow_cell_id,
        samples=[sample],
        status=FlowCellStatus.PROCESSING,
    )

    helpers.add_flow_cell(
        store=base_store,
        flow_cell_name=bcl_convert_flow_cell_id,
        samples=[sample],
        status=FlowCellStatus.RETRIEVED,
    )

    # WHEN fetching the latest flow cell
    is_on_disk = base_store.are_all_flow_cells_on_disk(case_id=case_id)

    # THEN return false
    assert is_on_disk is False


def test_are_all_flow_cells_on_disk_when_requested(
    base_store: Store,
    caplog,
    bcl2fastq_flow_cell_id: str,
    bcl_convert_flow_cell_id: str,
    case_id: str,
    helpers: StoreHelpers,
    sample: Sample,
    request,
):
    """Test check if all flow cells for samples on a case is on disk when requested."""
    caplog.set_level(logging.DEBUG)
    # GIVEN a store with two flow cell
    helpers.add_flow_cell(
        store=base_store,
        flow_cell_name=bcl2fastq_flow_cell_id,
        samples=[sample],
        status=FlowCellStatus.REMOVED,
    )
    helpers.add_flow_cell(
        store=base_store,
        flow_cell_name=bcl_convert_flow_cell_id,
        samples=[sample],
        status=FlowCellStatus.REQUESTED,
    )

    # WHEN fetching the latest flow cell
    is_on_disk = base_store.are_all_flow_cells_on_disk(case_id=case_id)

    # THEN return false
    assert is_on_disk is False


def test_are_all_flow_cells_on_disk(
    base_store: Store,
    caplog,
    bcl2fastq_flow_cell_id: str,
    bcl_convert_flow_cell_id: str,
    case_id: str,
    helpers: StoreHelpers,
    sample: Sample,
):
    """Test check if all flow cells for samples on a case is on disk."""
    caplog.set_level(logging.DEBUG)

    # GIVEN a store with two flow cell
    helpers.add_flow_cell(store=base_store, flow_cell_name=bcl2fastq_flow_cell_id, samples=[sample])
    helpers.add_flow_cell(store=base_store, flow_cell_name=bcl_convert_flow_cell_id)

    # WHEN fetching the latest flow cell
    is_on_disk = base_store.are_all_flow_cells_on_disk(case_id=case_id)

    # THEN return true
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
) -> ApplicationLimitations:
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
) -> ApplicationLimitations:
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
        and application_limitation.pipeline == workflow
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
    pools: list[Pool] = store_with_multiple_pools_for_customer.get_pools_by_customer_id(
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


def test_get_total_counts_passing_q30(
    store_with_sequencing_metrics: Store, sample_id: str, expected_total_reads: int
):
    # GIVEN a store with sequencing metrics

    total_reads_count_passing_q30 = (
        store_with_sequencing_metrics.get_number_of_reads_for_sample_passing_q30_threshold(
            sample_internal_id=sample_id, q30_threshold=0
        )
    )
    # THEN assert that the total read count is correct
    assert total_reads_count_passing_q30 == expected_total_reads


def test_get_metrics_entry_by_flow_cell_name_sample_internal_id_and_lane(
    store_with_sequencing_metrics: Store, sample_id: str, flow_cell_name: str, lane: int = 1
):
    # GIVEN a store with sequencing metrics

    # WHEN getting a metrics entry by flow cell name, sample internal id and lane
    metrics_entry: SampleLaneSequencingMetrics = (
        store_with_sequencing_metrics.get_metrics_entry_by_flow_cell_name_sample_internal_id_and_lane(
            sample_internal_id=sample_id, flow_cell_name=flow_cell_name, lane=lane
        )
    )

    assert metrics_entry is not None
    assert metrics_entry.flow_cell_name == flow_cell_name
    assert metrics_entry.flow_cell_lane_number == lane
    assert metrics_entry.sample_internal_id == sample_id


def test_get_number_of_reads_for_flow_cell_from_sample_lane_metrics(
    store_with_sequencing_metrics: Store,
    flow_cell_name_demultiplexed_with_bcl2fastq: str,
    expected_total_reads_flow_cell_bcl2fastq: int,
):
    # GIVEN a store with sequencing metrics
    # WHEN getting total read counts for a flow cell
    reads = store_with_sequencing_metrics.get_number_of_reads_for_flow_cell(
        flow_cell_name=flow_cell_name_demultiplexed_with_bcl2fastq
    )
    # THEN assert that the total read count is correct
    assert reads == expected_total_reads_flow_cell_bcl2fastq


def test_get_average_bases_above_q30_for_sample_from_metrics(
    store_with_sequencing_metrics: Store,
    expected_average_q30_for_sample: float,
    mother_sample_id: str,
    flow_cell_name_demultiplexed_with_bcl2fastq: str,
):
    # GIVEN a store with sequencing metrics

    # WHEN getting average bases above q30 for a sample
    average_bases_above_q30 = store_with_sequencing_metrics.get_average_q30_for_sample_on_flow_cell(
        sample_internal_id=mother_sample_id,
        flow_cell_name=flow_cell_name_demultiplexed_with_bcl2fastq,
    )

    # THEN assert that the average bases above q30 is correct
    assert average_bases_above_q30 == expected_average_q30_for_sample


def test_get_average_passing_q30_for_sample_from_metrics(
    store_with_sequencing_metrics: Store,
    expected_average_q30_for_flow_cell: float,
    flow_cell_name_demultiplexed_with_bcl2fastq: str,
):
    # GIVEN a store with sequencing metrics

    # WHEN getting average passing q30 for a sample
    average_passing_q30 = (
        store_with_sequencing_metrics.get_average_percentage_passing_q30_for_flow_cell(
            flow_cell_name=flow_cell_name_demultiplexed_with_bcl2fastq,
        )
    )

    # THEN assert that the average passing q30 is correct
    assert average_passing_q30 == expected_average_q30_for_flow_cell


def test_get_number_of_reads_for_sample_passing_q30_threshold(
    store_with_sequencing_metrics: Store,
    sample_id: str,
):
    # GIVEN a store with sequencing metrics
    metrics: Query = store_with_sequencing_metrics._get_query(table=SampleLaneSequencingMetrics)

    # GIVEN a metric for a specific sample
    sample_metric: SampleLaneSequencingMetrics | None = metrics.filter(
        SampleLaneSequencingMetrics.sample_internal_id == sample_id
    ).first()
    assert sample_metric

    # GIVEN a Q30 threshold that the sample will pass
    q30_threshold = int(sample_metric.sample_base_percentage_passing_q30 / 2)

    # WHEN getting the number of reads for the sample that pass the Q30 threshold
    number_of_reads: int = (
        store_with_sequencing_metrics.get_number_of_reads_for_sample_passing_q30_threshold(
            sample_internal_id=sample_id, q30_threshold=q30_threshold
        )
    )

    # THEN assert that the number of reads is an integer
    assert isinstance(number_of_reads, int)

    # THEN assert that the number of reads is at least the number of reads in the lane for the sample passing the q30
    assert number_of_reads >= sample_metric.sample_total_reads_in_lane


def test_get_number_of_reads_for_sample_with_some_not_passing_q30_threshold(
    store_with_sequencing_metrics: Store, sample_id: str
):
    # GIVEN a store with sequencing metrics
    metrics: Query = store_with_sequencing_metrics._get_query(table=SampleLaneSequencingMetrics)

    # GIVEN a metric for a specific sample
    sample_metrics: list[SampleLaneSequencingMetrics] = metrics.filter(
        SampleLaneSequencingMetrics.sample_internal_id == sample_id
    ).all()

    assert sample_metrics

    # GIVEN a Q30 threshold that some of the sample's metrics will not pass
    q30_values = [metric.sample_base_percentage_passing_q30 for metric in sample_metrics]
    q30_threshold = sorted(q30_values)[len(q30_values) // 2]  # This is the median

    # WHEN getting the number of reads for the sample that pass the Q30 threshold
    number_of_reads: int = (
        store_with_sequencing_metrics.get_number_of_reads_for_sample_passing_q30_threshold(
            sample_internal_id=sample_id, q30_threshold=q30_threshold
        )
    )

    # THEN assert that the number of reads is less than the total number of reads for the sample
    total_sample_reads = sum([metric.sample_total_reads_in_lane for metric in sample_metrics])
    assert number_of_reads < total_sample_reads


def test_get_sample_lane_sequencing_metrics_by_flow_cell_name(
    store_with_sequencing_metrics: Store, flow_cell_name: str
):
    # GIVEN a store with sequencing metrics

    # WHEN getting sequencing metrics for a flow cell
    metrics: list[SampleLaneSequencingMetrics] = (
        store_with_sequencing_metrics.get_sample_lane_sequencing_metrics_by_flow_cell_name(
            flow_cell_name=flow_cell_name
        )
    )

    # THEN assert that the metrics are returned
    assert metrics
    for metric in metrics:
        assert metric.flow_cell_name == flow_cell_name


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
    # THEN none should be returned
    assert not store.get_orders_by_workflow()


def test_get_orders_populated_store(store: Store, order: Order, order_another: Order):
    # GIVEN a store with two orders

    # WHEN fetching orders
    # THEN both should be returned
    assert len(store.get_orders_by_workflow()) == 2


def test_get_orders_limited(store: Store, order: Order, order_another: Order):
    # GIVEN a store with two orders

    # WHEN fetching a limited amount of orders
    # THEN only one should be returned
    assert len(store.get_orders_by_workflow(limit=1)) == 1


def test_get_orders_workflow_filter(
    store: Store, order: Order, order_another: Order, order_balsamic: Order
):
    # GIVEN a store with three orders, one of which is a Balsamic order

    # WHEN fetching only balsamic orders
    orders: list[Order] = store.get_orders_by_workflow(workflow=Workflow.BALSAMIC)
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

    # WHEN fetching only MIP-DNA orders
    orders: list[Order] = store.get_orders_by_workflow(workflow=Workflow.MIP_DNA, limit=limit)

    # THEN we should get the expected number of orders returned
    assert len(orders) == expected_returned
