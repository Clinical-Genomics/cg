"""Test for analysis"""

from datetime import datetime

import mock
import pytest

from cg.constants import FlowCellStatus, GenePanelMasterList, Priority
from cg.constants.priority import SlurmQos
from cg.constants.sequencing import Sequencers
from cg.exc import AnalysisNotReadyError
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.mip import MipAnalysisAPI
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.meta.workflow.prepare_fastq import PrepareFastqAPI
from cg.store import Store
from cg.store.models import Case


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
def test_get_slurm_qos_for_case(mocker, case_id: str, priority, expected_slurm_qos):
    """Test qet Quality of service (SLURM QOS) from the case priority"""

    # GIVEN a case that has a priority
    mocker.patch.object(AnalysisAPI, "get_priority_for_case")
    AnalysisAPI.get_priority_for_case.return_value = priority

    # When getting the SLURM QOS for the priority
    slurm_qos = AnalysisAPI.get_slurm_qos_for_case(AnalysisAPI, case_id=case_id)

    # THEN the expected slurm QOS should be returned
    assert slurm_qos is expected_slurm_qos


def test_gene_panels_correctly_added(customer_id):
    """Test get a correct gene panel list."""

    # GIVEN a case that has a gene panel included in the gene panel master list
    default_panels_included: list[str] = [GenePanelMasterList.get_panel_names()[0]]
    master_list: list[str] = GenePanelMasterList.get_panel_names()

    # WHEN converting the gene panels between the default and the gene_panel_master_list
    list_of_gene_panels_used: list[str] = MipAnalysisAPI.get_aggregated_panels(
        customer_id=customer_id, default_panels=set(default_panels_included)
    )

    # THEN the list_of_gene_panels_used should return all gene panels
    assert set(list_of_gene_panels_used) == set(master_list)


def test_gene_panels_not_added(customer_id):
    """Test get only OMIM-AUTO and custom gene panel list."""
    # GIVEN a case that has a gene panel that is NOT included in the gene panel master list
    default_panels_not_included: list[str] = ["PANEL_NOT_IN_GENE_PANEL_MASTER_LIST"]

    # WHEN converting the gene panels between the default and the gene_panel_master_list
    list_of_gene_panels_used: list[str] = MipAnalysisAPI.get_aggregated_panels(
        customer_id=customer_id, default_panels=set(default_panels_not_included)
    )

    # THEN the list_of_gene_panels_used should return the custom panel and OMIM-AUTO
    assert set(list_of_gene_panels_used) == set(
        default_panels_not_included
        + [GenePanelMasterList.OMIM_AUTO, GenePanelMasterList.PANELAPP_GREEN]
    )


def test_is_flow_cell_check_applicable(mip_analysis_api: MipDNAAnalysisAPI, analysis_store: Store):
    """Tests that a check for flow cells being present on disk is applicable when given a case which has no
    down-sampled nor external samples."""

    # GIVEN a case
    case: Case = analysis_store.get_cases()[0]

    # GIVEN that no samples are down-sampled nor external
    for sample in case.samples:
        assert not sample.from_sample
        assert not sample.is_external

    # WHEN checking if a flow cell check is applicable
    # THEN the method should return True
    assert mip_analysis_api._is_flow_cell_check_applicable(case_id=case.internal_id)


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
    assert not mip_analysis_api._is_flow_cell_check_applicable(case_id=case.internal_id)


def test_is_flow_cell_check_not_applicable_when_down_sampled(
    mip_analysis_api: MipDNAAnalysisAPI, analysis_store: Store
):
    """Tests that a check for flow cells being present on disk is applicable when given a case which has no
    down-sampled nor external samples."""

    # GIVEN a case
    case: Case = analysis_store.get_cases()[0]

    # WHEN marking all of its samples as down sampled from TestSample
    for sample in case.samples:
        sample.from_sample = "TestSample"

    # WHEN checking if a flow cell check is applicable
    # THEN the method should return False
    assert not mip_analysis_api._is_flow_cell_check_applicable(case_id=case.internal_id)


def test_ensure_flow_cells_on_disk_check_not_applicable(
    mip_analysis_api: MipDNAAnalysisAPI, analysis_store: Store, caplog
):
    """Tests that ensure_flow_cells_on_disk does not perform any action
    when is_flow_cell_check_applicable returns false."""

    # GIVEN a case
    case: Case = analysis_store.get_cases()[0]

    # WHEN _is_flow_cell_check_available returns False
    with mock.patch.object(
        AnalysisAPI,
        "_is_flow_cell_check_applicable",
        return_value=False,
    ):
        caplog.set_level("INFO")
        mip_analysis_api.ensure_flow_cells_on_disk(case.internal_id)

    # THEN a warning should be logged
    assert (
        "Flow cell check is not applicable - the case is either down sampled or external."
        in caplog.text
    )


def test_ensure_flow_cells_on_disk_does_not_request_flow_cells(
    mip_analysis_api: MipDNAAnalysisAPI, analysis_store: Store, helpers
):
    """Tests that ensure_flow_cells_on_disk does not perform any action
    when is_flow_cell_check_applicable returns True and all flow cells are ON_DISK already."""

    # GIVEN a case
    case: Case = analysis_store.get_cases()[0]

    helpers.add_flow_cell(
        analysis_store,
        flow_cell_name="flow_cell_test",
        archived_at=datetime.now(),
        sequencer_type=Sequencers.NOVASEQ,
        samples=analysis_store.get_samples_by_case_id(case.internal_id),
        status=FlowCellStatus.ON_DISK,
        date=datetime.now(),
    )

    # WHEN _is_flow_cell_check_available returns True and the attached flow cell is ON_DISK
    with mock.patch.object(
        AnalysisAPI,
        "_is_flow_cell_check_applicable",
        return_value=True,
    ), mock.patch.object(
        Store, "request_flow_cells_for_case", return_value=None
    ) as request_checker:
        mip_analysis_api.ensure_flow_cells_on_disk(case.internal_id)

    # THEN flow cells should not be requested for the case
    assert request_checker.call_count == 0


def test_ensure_flow_cells_on_disk_does_request_flow_cells(
    mip_analysis_api: MipDNAAnalysisAPI, analysis_store: Store, helpers
):
    """Tests that ensure_flow_cells_on_disk requests a removed flow cell
    when is_flow_cell_check_applicable returns True.."""

    # GIVEN a case with a REMOVED flow cell
    case: Case = analysis_store.get_cases()[0]
    helpers.add_flow_cell(
        analysis_store,
        flow_cell_name="flow_cell_test",
        archived_at=datetime.now(),
        sequencer_type=Sequencers.NOVASEQ,
        samples=analysis_store.get_samples_by_case_id(case.internal_id),
        status=FlowCellStatus.REMOVED,
        date=datetime.now(),
    )

    # WHEN _is_flow_cell_check_available returns True
    with mock.patch.object(
        AnalysisAPI,
        "_is_flow_cell_check_applicable",
        return_value=True,
    ):
        mip_analysis_api.ensure_flow_cells_on_disk(case.internal_id)

    # THEN the flow cell's status should be set to REQUESTED for the case
    assert analysis_store.get_flow_cell_by_name("flow_cell_test").status == FlowCellStatus.REQUESTED


def test_is_case_ready_for_analysis_true(
    mip_analysis_api: MipDNAAnalysisAPI, analysis_store, helpers
):
    """Tests that is_case_ready_for_analysis returns true for a case whose flow cells are all ON_DISK and whose
    files need no decompression nor are being decompressed currently."""

    # GIVEN a case and a flow cell with status ON_DISK
    case: Case = analysis_store.get_cases()[0]
    helpers.add_flow_cell(
        analysis_store,
        flow_cell_name="flowcell_test",
        archived_at=datetime.now(),
        sequencer_type=Sequencers.NOVASEQ,
        samples=analysis_store.get_samples_by_case_id(case.internal_id),
        status=FlowCellStatus.ON_DISK,
        date=datetime.now(),
    )

    # GIVEN that no decompression is needed nor running
    with mock.patch.object(
        PrepareFastqAPI, "is_spring_decompression_needed", return_value=False
    ), mock.patch.object(PrepareFastqAPI, "is_spring_decompression_running", return_value=False):
        # WHEN running is_case_ready_for_analysis
        # THEN the result should be true
        assert mip_analysis_api.is_case_ready_for_analysis(case_id=case.internal_id)


def test_is_case_ready_for_analysis_decompression_needed(
    mip_analysis_api: MipDNAAnalysisAPI, analysis_store, helpers
):
    """Tests that is_case_ready_for_analysis returns false for a case whose flow cells are all ON_DISK but whose
    files need decompression."""

    # GIVEN a case and a flow cell
    case: Case = analysis_store.get_cases()[0]
    helpers.add_flow_cell(
        analysis_store,
        flow_cell_name="flowcell_test",
        archived_at=datetime.now(),
        sequencer_type=Sequencers.NOVASEQ,
        samples=analysis_store.get_samples_by_case_id(case.internal_id),
        status=FlowCellStatus.ON_DISK,
        date=datetime.now(),
    )

    # GIVEN that some files need to be decompressed
    with mock.patch.object(
        PrepareFastqAPI, "is_spring_decompression_needed", return_value=True
    ), mock.patch.object(PrepareFastqAPI, "is_spring_decompression_running", return_value=False):
        # WHEN running is_case_ready_for_analysis
        # THEN the result should be false
        assert not mip_analysis_api.is_case_ready_for_analysis(case_id=case.internal_id)


def test_is_case_ready_for_analysis_decompression_running(
    mip_hk_store,
    analysis_store,
    helpers,
    mip_analysis_api: MipDNAAnalysisAPI,
):
    """Tests that is_case_ready_for_analysis returns false for a case whose flow cells are all ON_DISK but whose
    files are being decompressed currently."""

    # GIVEN a case and a flow cell
    case: Case = analysis_store.get_cases()[0]
    helpers.add_flow_cell(
        analysis_store,
        flow_cell_name="flowcell_test",
        archived_at=datetime.now(),
        sequencer_type=Sequencers.NOVASEQ,
        samples=analysis_store.get_samples_by_case_id(case.internal_id),
        status=FlowCellStatus.ON_DISK,
        date=datetime.now(),
    )

    # GIVEN that some files are being decompressed
    with mock.patch.object(
        PrepareFastqAPI, "is_spring_decompression_needed", return_value=False
    ), mock.patch.object(PrepareFastqAPI, "is_spring_decompression_running", return_value=True):
        # WHEN running is_case_ready_for_analysis
        # THEN the result should be false
        assert not mip_analysis_api.is_case_ready_for_analysis(case_id=case.internal_id)


def test_prepare_fastq_files_success(mip_analysis_api: MipDNAAnalysisAPI, analysis_store, helpers):
    """Tests that no error is thrown when running prepare_fastq_files when its flow cells are all ON_DISK,
    and no spring decompression is needed nor is running."""

    # GIVEN a case with a flow cell ON_DISK
    case: Case = analysis_store.get_cases()[0]
    helpers.add_flow_cell(
        analysis_store,
        flow_cell_name="flowcell_test",
        archived_at=datetime.now(),
        sequencer_type=Sequencers.NOVASEQ,
        samples=analysis_store.get_samples_by_case_id(case.internal_id),
        status=FlowCellStatus.ON_DISK,
        date=datetime.now(),
    )

    # GIVEN that no decompression is or running and adding the files to Housekeeper goes well
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


def test_prepare_fastq_files_decompression_needed(
    mip_analysis_api: MipDNAAnalysisAPI, analysis_store, helpers
):
    """Tests that an AnalysisNotReady error is raised when decompression of spring files is needed
    when running prepare_fastq_files."""

    # GIVEN a case with its flow cell with status ON_DISK
    case: Case = analysis_store.get_cases()[0]
    helpers.add_flow_cell(
        analysis_store,
        flow_cell_name="flowcell_test",
        archived_at=datetime.now(),
        sequencer_type=Sequencers.NOVASEQ,
        samples=analysis_store.get_samples_by_case_id(case.internal_id),
        status=FlowCellStatus.ON_DISK,
        date=datetime.now(),
    )

    # GIVEN that spring decompression is needed, and decompression is started successfully.
    with mock.patch.object(
        PrepareFastqAPI, "is_spring_decompression_needed", return_value=True
    ), mock.patch.object(MipAnalysisAPI, "decompress_case", return_value=None), mock.patch.object(
        PrepareFastqAPI, "is_spring_decompression_running", return_value=False
    ), mock.patch.object(
        PrepareFastqAPI, "add_decompressed_fastq_files_to_housekeeper", return_value=None
    ):
        with pytest.raises(AnalysisNotReadyError):
            # WHEN running prepare_fastq_files
            # THEN an AnalysisNotReadyError should be raised.
            mip_analysis_api.prepare_fastq_files(case_id=case.internal_id, dry_run=False)


def test_prepare_fastq_files_decompression_running(
    mip_analysis_api: MipDNAAnalysisAPI, analysis_store, helpers
):
    """Tests that an AnalysisNotReady error is raised when decompression of spring files is running
    when running prepare_fastq_files."""

    # GIVEN a case with all its flow cells being ON_DISK
    case: Case = analysis_store.get_cases()[0]
    helpers.add_flow_cell(
        analysis_store,
        flow_cell_name="flowcell_test",
        archived_at=datetime.now(),
        sequencer_type=Sequencers.NOVASEQ,
        samples=analysis_store.get_samples_by_case_id(case.internal_id),
        status=FlowCellStatus.ON_DISK,
        date=datetime.now(),
    )

    # GIVEN that decompression of spring files is running.
    with mock.patch.object(
        PrepareFastqAPI, "is_spring_decompression_needed", return_value=False
    ), mock.patch.object(
        PrepareFastqAPI, "is_spring_decompression_running", return_value=True
    ), mock.patch.object(
        PrepareFastqAPI, "add_decompressed_fastq_files_to_housekeeper", return_value=None
    ):
        with pytest.raises(AnalysisNotReadyError):
            # WHEN running prepare_fastq_files
            # THEN an AnalysisNotReadyError should be thrown
            mip_analysis_api.prepare_fastq_files(case_id=case.internal_id, dry_run=False)
