"""Test for analysis"""

import logging
from datetime import datetime

import mock
import pytest

from cg.constants import GenePanelMasterList, Priority, SequencingRunDataAvailability
from cg.constants.archiving import ArchiveLocations
from cg.constants.constants import ControlOptions
from cg.constants.priority import SlurmQos
from cg.constants.sequencing import Sequencers
from cg.exc import AnalysisNotReadyError
from cg.meta.archive.archive import SpringArchiveAPI
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.mip import MipAnalysisAPI
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.meta.workflow.prepare_fastq import PrepareFastqAPI
from cg.meta.workflow.utils.utils import are_all_samples_control
from cg.models.fastq import FastqFileMeta
from cg.store.models import Case, Sample, IlluminaSequencingRun
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


@pytest.mark.parametrize(
    "priority,expected_slurm_qos",
    [
        (Priority.clinical_trials, SlurmQos.NORMAL),
        (Priority.research, SlurmQos.LOW),
        (Priority.standard, SlurmQos.NORMAL),
        (Priority.priority, SlurmQos.HIGH),
        (Priority.express, SlurmQos.EXPRESS),
    ],
)
def test_get_slurm_qos_for_case(
    case_id: str,
    priority,
    expected_slurm_qos,
    mip_analysis_api: MipDNAAnalysisAPI,
    analysis_store: Store,
):
    """Test get Quality of service (SLURM QOS) from the case priority"""

    # GIVEN a store with a case with a specific priority
    mip_analysis_api.status_db = analysis_store
    case: Case = analysis_store.get_case_by_internal_id(case_id)
    case.priority = priority

    # WHEN getting the SLURM QOS for the priority
    slurm_qos: SlurmQos = mip_analysis_api.get_slurm_qos_for_case(case_id=case_id)

    # THEN the expected slurm QOS should be returned
    assert slurm_qos is expected_slurm_qos


def test_gene_panels_not_part_of_master_list(customer_id: str):
    """Test get only broad non-specific gene panels and custom gene panel list if a supplied gene panels is not part of master list."""
    # GIVEN a customer who is a collaborator on the master list

    # GIVEN a gene panel NOT included in the gene panel master list
    default_panels_not_included: list[str] = ["PANEL_NOT_IN_GENE_PANEL_MASTER_LIST"]

    # WHEN converting the gene panels between the default and the gene panel master list
    list_of_gene_panels_used: list[str] = MipAnalysisAPI.get_aggregated_panels(
        customer_id=customer_id, default_panels=set(default_panels_not_included)
    )

    # THEN the list of gene panels returned is the custom panel and broad non-specific panels
    assert set(
        list_of_gene_panels_used
    ) == GenePanelMasterList.get_non_specific_gene_panels().union(set(default_panels_not_included))


def test_gene_panels_customer_collaborator_and_panel_part_of_master_list(customer_id: str):
    """Test get gene panels when customer is collaborator for gene panel master list, and supplied gene panels are a subset of the masters list."""

    # GIVEN a a gene panel included in the gene panel master list
    default_panels_included: list[str] = [GenePanelMasterList.get_panel_names()[0]]

    # GIVEN a master list

    # WHEN converting the gene panels between the default and the gene panel master list
    list_of_gene_panels_used: list[str] = MipAnalysisAPI.get_aggregated_panels(
        customer_id=customer_id, default_panels=set(default_panels_included)
    )

    # THEN the list of gene panels used should return all gene panels in the master list
    assert set(list_of_gene_panels_used) == set(GenePanelMasterList.get_panel_names())


def test_gene_panels_customer_is_collaborator_and_panel_not_part_of_master_list(customer_id: str):
    """Test get gene panels when customer is collaborator for gene panel master list, but supplied gene panels are not a subset of the masters list."""

    # GIVEN a case that has a customer collaborator for the gene panel master list

    # GIVEN a gene panel not in the master list
    default_panels: list[str] = ["A_PANEL_NOT_IN_MASTER_LIST"]

    # WHEN converting the gene panels between the default and the gene panel master list
    list_of_gene_panels_used: list[str] = MipAnalysisAPI.get_aggregated_panels(
        customer_id=customer_id, default_panels=set(default_panels)
    )

    # THEN the list of gene panels returned the custom panel and broad non-specific panels
    assert set(
        list_of_gene_panels_used
    ) == GenePanelMasterList.get_non_specific_gene_panels().union(set(default_panels))


def test_gene_panels_customer_not_collaborator_for_gene_master_list():
    """Test get gene panels when customer is not collaborator for the gene panel master list."""
    # GIVEN a a gene panel included in the gene panel master list
    default_panels: list[str] = [GenePanelMasterList.get_panel_names()[0]]

    # GIVEN a case that has a customer, who is not a collaborator for the gene panel master list

    # WHEN converting the gene panels between the default and the gene panel master list
    list_of_gene_panels_used: list[str] = MipAnalysisAPI.get_aggregated_panels(
        customer_id="CUSTOMER_NOT_COLLABORATOR_FOR_MASTER_LIST", default_panels=set(default_panels)
    )

    # THEN the list of gene panels returned the custom panel and broad non-specific panels
    assert set(
        list_of_gene_panels_used
    ) == GenePanelMasterList.get_non_specific_gene_panels().union(set(default_panels))


def test_is_illumina_run_check_applicable(
    mip_analysis_api: MipDNAAnalysisAPI, analysis_store: Store
):
    """Tests that a check for flow cells being present on disk is applicable when given a case which has no
    down-sampled nor external samples."""

    # GIVEN a case
    case: Case = analysis_store.get_cases()[0]

    # GIVEN that no samples are down-sampled nor external
    for sample in case.samples:
        assert not sample.from_sample

    # WHEN checking if a flow cell check is applicable
    # THEN the method should return True
    assert mip_analysis_api._is_illumina_run_check_applicable(case_id=case.internal_id)


def test_is_flow_cell_check_not_applicable_when_external(
    mip_analysis_api: MipDNAAnalysisAPI, analysis_store: Store
):
    """Tests that a check for flow cells being present on disk is applicable when given a case which has no
    down-sampled nor external samples."""

    # GIVEN a case
    case: Case = analysis_store.get_cases()[0]

    # WHEN marking all of its samples as external
    for sample in case.samples:
        sample.application_version.application.is_external = True

    # WHEN checking if a flow cell check is applicable
    # THEN the method should return False
    assert not mip_analysis_api._is_illumina_run_check_applicable(case_id=case.internal_id)


def test_is_illumina_run_check_not_applicable_when_down_sampled(
    mip_analysis_api: MipDNAAnalysisAPI,
    store_with_illumina_sequencing_data_on_disk: Store,
    selected_novaseq_x_case_ids: list[str],
):
    """Tests that a check for Illumina runs being on disk is applicable when given a case which has no
    down-sampled nor external samples."""

    # GIVEN a case
    case: Case = store_with_illumina_sequencing_data_on_disk.get_case_by_internal_id(
        selected_novaseq_x_case_ids[0]
    )

    # WHEN marking all of its samples as down sampled from TestSample
    for sample in case.samples:
        sample.from_sample = "TestSample"

    # WHEN checking if an Illumina run check is applicable
    # THEN the method should return False
    assert not mip_analysis_api._is_illumina_run_check_applicable(case_id=case.internal_id)


def test_ensure_illumina_run_on_disk_check_not_applicable(
    mip_analysis_api: MipDNAAnalysisAPI,
    store_with_illumina_sequencing_data_on_disk: Store,
    selected_novaseq_x_case_ids: list[str],
    caplog,
):
    """Tests that ensure_illumina_run_on_disk does not perform any action
    when is_illumina_runs_check_applicable returns false."""
    caplog.set_level(logging.INFO)
    # GIVEN a case
    case: Case = store_with_illumina_sequencing_data_on_disk.get_case_by_internal_id(
        selected_novaseq_x_case_ids[0]
    )

    # WHEN _is_flow_cell_check_available returns False
    with mock.patch.object(
        AnalysisAPI,
        "_is_illumina_run_check_applicable",
        return_value=False,
    ):
        mip_analysis_api.ensure_illumina_run_on_disk(case.internal_id)

    # THEN a warning should be logged
    assert (
        "Illumina run check is not applicable - the case is either down sampled or external."
        in caplog.text
    )


def test_ensure_illumina_runs_on_disk_does_not_request_runs(
    mip_analysis_api: MipDNAAnalysisAPI,
    store_with_illumina_sequencing_data_on_disk: Store,
    helpers: StoreHelpers,
    selected_novaseq_x_case_ids: list[str],
):
    """Tests that ensure_illumina_run_on_disk does not perform any action
    when is_Illumina_runs_check_applicable returns True and all runs are ON_DISK already."""

    # GIVEN a case

    # WHEN _is_illumina_run_check_available returns True and the attached flow cell is ON_DISK
    with mock.patch.object(
        AnalysisAPI,
        "_is_illumina_run_check_applicable",
        return_value=True,
    ), mock.patch.object(
        Store, "request_sequencing_runs_for_case", return_value=None
    ) as request_checker:
        mip_analysis_api.ensure_illumina_run_on_disk(selected_novaseq_x_case_ids[0])

    # THEN runs should not be requested for the case
    assert request_checker.call_count == 0


def test_ensure_illumina_run_on_disk_does_request_run(
    mip_analysis_api: MipDNAAnalysisAPI,
    store_with_illumina_sequencing_data_on_disk: Store,
    helpers: StoreHelpers,
    selected_novaseq_x_case_ids: list[str],
):
    """Tests that ensure_illumina_run_on_disk requests a removed flow cell
    when is_flow_cell_check_applicable returns True.."""

    # GIVEN a case with a REMOVED Illumina run
    sequencing_runs: list[IlluminaSequencingRun] = (
        store_with_illumina_sequencing_data_on_disk.get_illumina_sequencing_runs_by_case(
            selected_novaseq_x_case_ids[0]
        )
    )
    for sequencing_run in sequencing_runs:
        sequencing_run.data_availability = SequencingRunDataAvailability.REMOVED

    # WHEN _is_flow_cell_check_available returns True
    with mock.patch.object(
        AnalysisAPI,
        "_is_illumina_run_check_applicable",
        return_value=True,
    ):
        mip_analysis_api.ensure_illumina_run_on_disk(selected_novaseq_x_case_ids[0])

    # THEN the flow cell's status should be set to REQUESTED for the case
    modified_runs: list[IlluminaSequencingRun] = (
        store_with_illumina_sequencing_data_on_disk.get_illumina_sequencing_runs_by_case(
            selected_novaseq_x_case_ids[0]
        )
    )
    for run in modified_runs:
        assert run.data_availability == SequencingRunDataAvailability.REQUESTED


def test_is_case_ready_for_analysis_true(
    mip_analysis_api: MipDNAAnalysisAPI,
    store_with_illumina_sequencing_data_on_disk: Store,
    selected_novaseq_x_case_ids: list[str],
):
    """Tests that is_case_ready_for_analysis returns true for a case whose illumina runs are all ON_DISK and whose
    files need no decompression nor are being decompressed currently."""
    # GIVEN a case and a flow cell with status ON_DISK

    # GIVEN that no decompression is needed nor running
    with mock.patch.object(
        PrepareFastqAPI, "is_spring_decompression_needed", return_value=False
    ), mock.patch.object(PrepareFastqAPI, "is_spring_decompression_running", return_value=False):
        # WHEN running is_case_ready_for_analysis

        # THEN the result should be true
        assert mip_analysis_api.is_raw_data_ready_for_analysis(selected_novaseq_x_case_ids[0])


def test_is_case_ready_for_analysis_decompression_needed(
    mip_analysis_api: MipDNAAnalysisAPI,
    store_with_illumina_sequencing_data_on_disk: Store,
    selected_novaseq_x_case_ids: list[str],
):
    """Tests that is_case_ready_for_analysis returns false for a case whose sequencing runs are all ON_DISK but whose
    files need decompression."""

    # GIVEN a case and an Illumina run

    # GIVEN that some files need to be decompressed
    with mock.patch.object(
        PrepareFastqAPI, "is_spring_decompression_needed", return_value=True
    ), mock.patch.object(PrepareFastqAPI, "is_spring_decompression_running", return_value=False):
        # WHEN running is_case_ready_for_analysis
        # THEN the result should be false
        assert not mip_analysis_api.is_raw_data_ready_for_analysis(selected_novaseq_x_case_ids[0])


def test_is_case_ready_for_analysis_decompression_running(
    mip_hk_store,
    selected_novaseq_x_case_ids: list[str],
    mip_analysis_api: MipDNAAnalysisAPI,
):
    """Tests that is_case_ready_for_analysis returns false for a case whose Illumina run are all ON_DISK but whose
    files are being decompressed currently."""

    # GIVEN a case and a Illumina sequencing run

    # GIVEN that some files are being decompressed
    with mock.patch.object(
        PrepareFastqAPI, "is_spring_decompression_needed", return_value=False
    ), mock.patch.object(PrepareFastqAPI, "is_spring_decompression_running", return_value=True):
        # WHEN running is_case_ready_for_analysis
        # THEN the result should be false
        assert not mip_analysis_api.is_raw_data_ready_for_analysis(selected_novaseq_x_case_ids[0])


@pytest.mark.parametrize(
    "is_spring_decompression_needed, is_spring_decompression_running",
    [(False, False), (True, False), (False, True), (True, True)],
)
def test_prepare_fastq_files_success(
    mip_analysis_api: MipDNAAnalysisAPI,
    store_with_illumina_sequencing_data_on_disk: Store,
    selected_novaseq_x_case_ids: list[str],
    helpers,
    is_spring_decompression_needed,
    is_spring_decompression_running,
):
    """Tests that no error is thrown when running prepare_fastq_files when its Illumina runs are all ON_DISK,
    and no spring decompression is needed nor is running."""

    # GIVEN a case with an Illumina run ON_DISK

    # GIVEN that no decompression is or running and adding the files to Housekeeper goes well
    with mock.patch.object(
        PrepareFastqAPI,
        "is_spring_decompression_needed",
        return_value=is_spring_decompression_needed,
    ), mock.patch.object(MipAnalysisAPI, "decompress_case", return_value=None), mock.patch.object(
        PrepareFastqAPI,
        "is_spring_decompression_running",
        return_value=is_spring_decompression_running,
    ), mock.patch.object(
        PrepareFastqAPI, "add_decompressed_fastq_files_to_housekeeper", return_value=None
    ):
        # WHEN running prepare_fastq_files
        if is_spring_decompression_running or is_spring_decompression_needed:
            with pytest.raises(AnalysisNotReadyError):
                mip_analysis_api.prepare_fastq_files(
                    case_id=selected_novaseq_x_case_ids[0], dry_run=False
                )
        else:
            mip_analysis_api.prepare_fastq_files(
                case_id=selected_novaseq_x_case_ids[0], dry_run=False
            )


def test_prepare_fastq_files_request_miria(
    mip_analysis_api: MipDNAAnalysisAPI,
    selected_novaseq_x_case_ids: list[str],
):
    """Tests that samples' input files are requested via Miria for a Clinical customer, if files are archived."""

    # GIVEN a case belonging to a non-PDC customer with at least one archived spring file
    case: Case = mip_analysis_api.status_db.get_case_by_internal_id(selected_novaseq_x_case_ids[0])
    case.customer.data_archive_location = ArchiveLocations.KAROLINSKA_BUCKET

    # GIVEN that at least one file is archived and not retrieved
    with mock.patch.object(
        PrepareFastqAPI, "is_spring_decompression_needed", return_value=False
    ), mock.patch.object(
        PrepareFastqAPI, "is_spring_decompression_running", return_value=False
    ), mock.patch.object(
        PrepareFastqAPI, "add_decompressed_fastq_files_to_housekeeper", return_value=None
    ), mock.patch.object(
        SpringArchiveAPI, "retrieve_spring_files_for_case"
    ), mock.patch.object(
        AnalysisAPI, "is_raw_data_ready_for_analysis", return_value=False
    ) as request_submitter:
        with pytest.raises(AnalysisNotReadyError):
            # WHEN running prepare_fastq_files

            # THEN an AnalysisNotReadyError should be thrown
            mip_analysis_api.prepare_fastq_files(case_id=case.internal_id, dry_run=False)

    # THEN retrieve_samples should have been invoked
    assert request_submitter.call_count == 1


def test_prepare_fastq_files_does_not_request_miria(
    mip_analysis_api: MipDNAAnalysisAPI,
    store_with_illumina_sequencing_data_on_disk: Store,
    helpers: StoreHelpers,
    selected_novaseq_x_case_ids: list[str],
):
    """Tests that samples' input files are not requested via Miria for a Clinical customer, if no files are archived."""

    # GIVEN a case belonging to a non-PDC customer

    # GIVEN that no files have entries in the Archive table
    case: Case = store_with_illumina_sequencing_data_on_disk.get_case_by_internal_id(
        selected_novaseq_x_case_ids[0]
    )
    case.customer.data_archive_location = ArchiveLocations.KAROLINSKA_BUCKET

    # GIVEN that all Illumina runs have status on disk
    with mock.patch.object(
        PrepareFastqAPI, "is_spring_decompression_needed", return_value=False
    ), mock.patch.object(
        PrepareFastqAPI, "is_spring_decompression_running", return_value=False
    ), mock.patch.object(
        PrepareFastqAPI, "add_decompressed_fastq_files_to_housekeeper", return_value=None
    ):
        # WHEN running prepare_fastq_files

        # THEN no error should be raised
        mip_analysis_api.prepare_fastq_files(case_id=case.internal_id, dry_run=False)


def test_are_all_spring_files_present_true_when_all_present(
    mip_analysis_api: MipDNAAnalysisAPI,
    analysis_store: Store,
    non_archived_spring_file,
    case_id: str,
    father_sample_id: str,
    helpers: StoreHelpers,
):
    """Tests that are_all_spring_files_present returns True when no files for a case are archived."""

    # GIVEN that the only Spring file belonging to a case has no Archive entry

    # WHEN checking if all spring files are present

    # THEN the result should be True
    assert mip_analysis_api.are_all_spring_files_present(case_id)


def test_are_all_spring_files_present_false_when_none_present(
    mip_analysis_api: MipDNAAnalysisAPI,
    analysis_store: Store,
    archived_spring_file,
    case_id: str,
    sample_id: str,
):
    """Tests that are_all_spring_files_present returns False when all files for a case are archived and not retrieved."""

    # GIVEN that the only Spring file belonging to a case has an Archive entry which has retrieved_at not set

    # WHEN checking if all spring files are present

    # THEN the result should be False
    assert not mip_analysis_api.are_all_spring_files_present(case_id)


def test_ensure_files_are_present(
    mip_analysis_api: MipDNAAnalysisAPI,
    analysis_store: Store,
    archived_spring_file,
    case_id: str,
    sample_id: str,
):
    """Tests that archived files are requested via Miria after the flow cell check has been performed."""

    # GIVEN that the only Spring file belonging to a case has an Archive entry which has retrieved_at not set

    # WHEN ensuring that all files are present

    with mock.patch.object(AnalysisAPI, "ensure_illumina_run_on_disk"), mock.patch.object(
        SpringArchiveAPI,
        "retrieve_spring_files_for_case",
    ) as request_submitter:
        mip_analysis_api.ensure_files_are_present(case_id)

    # THEN the files should have been requested
    request_submitter.assert_called()


@pytest.mark.parametrize(
    "data_availability, result",
    [(SequencingRunDataAvailability.REMOVED, True), (SequencingRunDataAvailability.ON_DISK, False)],
)
def test_does_any_spring_file_need_to_be_retrieved_flow_cell_status(
    mip_analysis_api: MipDNAAnalysisAPI,
    store_with_illumina_sequencing_data_on_disk: Store,
    selected_novaseq_x_case_ids: list[str],
    helpers: StoreHelpers,
    data_availability: str,
    result: bool,
):
    """Tests that does_any_spring_file_need_to_be_retrieved returns True if one of
    the Illumina run has data availability 'removed' and False if the status is instead 'ondisk'."""

    # GIVEN a case with an illumina with provided data availability
    sequencing_runs: list[IlluminaSequencingRun] = (
        store_with_illumina_sequencing_data_on_disk.get_illumina_sequencing_runs_by_case(
            selected_novaseq_x_case_ids[0]
        )
    )
    for run in sequencing_runs:
        run.data_availability = data_availability

    # WHEN checking if any files need to be retrieved

    # THEN the outcome should be False if the Illumina run data availability is on disk but not otherwise
    assert (
        mip_analysis_api.does_any_file_need_to_be_retrieved(selected_novaseq_x_case_ids[0])
        == result
    )


def test_does_any_spring_file_need_to_be_retrieved_archived_file(
    mip_analysis_api: MipDNAAnalysisAPI,
    analysis_store: Store,
    case_id: str,
    archived_spring_file,
    non_archived_spring_file,
):
    """Tests that does_any_spring_file_need_to_be_retrieved returns true if no flow cell is removed but some
    files need to be retrieved via Miria."""

    assert mip_analysis_api.does_any_file_need_to_be_retrieved(case_id)


def test_does_any_spring_file_need_to_be_retrieved_files_present(
    mip_analysis_api: MipDNAAnalysisAPI,
    analysis_store: Store,
    case_id: str,
    non_archived_spring_file,
):
    """Tests that does_any_spring_file_need_to_be_retrieved returns true if no flow cell is removed and no
    files need to be retrieved via Miria."""

    assert mip_analysis_api.does_any_file_need_to_be_retrieved(case_id)


def test_link_fastq_files_for_sample(
    analysis_store: Store,
    caplog,
    mip_analysis_api: MipDNAAnalysisAPI,
    fastq_file_meta_raw: dict,
    mocker,
):
    caplog.set_level(logging.INFO)
    # GIVEN a case
    case: Case = analysis_store.get_cases()[0]

    # GIVEN a sample
    sample: Sample = case.links[0].sample

    with mocker.patch.object(
        AnalysisAPI,
        "gather_file_metadata_for_sample",
        return_value=[FastqFileMeta.model_validate(fastq_file_meta_raw)],
    ):
        # WHEN parsing header
        mip_analysis_api.link_fastq_files_for_sample(case=case, sample=sample)

        # THEN broadcast linking of files
        assert "Linking: " in caplog.text


def test_are_all_samples_control(analysis_store: Store, case_id: str) -> None:
    """Tests that are_all_samples_control returns True if all samples in a case are controls."""

    # GIVEN a case with all samples being positive controls
    case: Case = analysis_store.get_case_by_internal_id(case_id)
    for sample in case.samples:
        sample.control = ControlOptions.POSITIVE

    # WHEN checking if all samples are controls
    # THEN the result should be True
    assert are_all_samples_control(case)


@pytest.mark.parametrize(
    "sample_controls, expected_qos",
    [
        (
            [ControlOptions.POSITIVE, ControlOptions.POSITIVE, ControlOptions.POSITIVE],
            SlurmQos.EXPRESS,
        ),
        (
            [ControlOptions.POSITIVE, ControlOptions.NEGATIVE, ControlOptions.EMPTY],
            SlurmQos.NORMAL,
        ),
    ],
    ids=["all_controls", "not_all_controls"],
)
def test_case_with_controls_get_correct_slurmqos(
    mip_analysis_api: MipDNAAnalysisAPI,
    analysis_store: Store,
    case_id: str,
    sample_controls: list[str],
    expected_qos: str,
) -> None:
    """Tests that get_slurm_qos_for_case returns the correct SLURM QOS for a case with control samples."""

    # GIVEN a case with the specified sample control types
    mip_analysis_api.status_db = analysis_store
    case: Case = analysis_store.get_case_by_internal_id(case_id)
    for index, control in enumerate(sample_controls):
        case.samples[index].control = control

    # WHEN getting the SLURM QOS for the case
    qos: SlurmQos = mip_analysis_api.get_slurm_qos_for_case(case_id)

    # THEN the result should match the expected QOS
    assert qos == expected_qos
