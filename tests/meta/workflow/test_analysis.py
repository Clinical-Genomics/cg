"""Test for analysis"""
from typing import List

import pytest
from cg.constants import GenePanelMasterList, Priority
from cg.constants.priority import SlurmQos
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.mip import MipAnalysisAPI
from cg.store import Store
from cg.store.models import Family
from cgmodels.cg.constants import Pipeline


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
    """Test get correct gene panel list."""

    # GIVEN a case that has a gene panel included in the gene panel master list
    default_panels_included: List[str] = [GenePanelMasterList.get_panel_names()[0]]
    master_list: List[str] = GenePanelMasterList.get_panel_names()

    # WHEN converting the gene panels between the default and the gene_panel_master_list
    list_of_gene_panels_used = MipAnalysisAPI.convert_panels(
        customer=customer_id, default_panels=default_panels_included
    )

    # THEN the list_of_gene_panels_used should return all gene panels
    assert set(list_of_gene_panels_used) == set(master_list)


def test_gene_panels_not_added(customer_id):
    """Test get only OMIM-AUTO and custom gene panel list."""
    # GIVEN a case that has a gene panel that is NOT included in the gene panel master list
    default_panels_not_included: List[str] = ["PANEL_NOT_IN_GENE_PANEL_MASTER_LIST"]

    # WHEN converting the gene panels between the default and the gene_panel_master_list
    list_of_gene_panels_used = MipAnalysisAPI.convert_panels(
        customer=customer_id, default_panels=default_panels_not_included
    )

    # THEN the list_of_gene_panels_used should return the custom panel and OMIM-AUTO
    assert set(list_of_gene_panels_used) == set(
        default_panels_not_included + [GenePanelMasterList.OMIM_AUTO]
    )


def test_is_flow_cell_check_applicable(cg_context, analysis_store: Store):
    """Tests that a check for flow cells being present on disk is applicable when given a case which has no
    down-sampled nor external samples."""

    mip_analysis_api = MipAnalysisAPI(cg_context, Pipeline.MIP_DNA)

    # GIVEN a case
    case: Family = analysis_store.get_cases()[0]

    # GIVEN that no samples are down-sampled nor external
    for sample in case.samples:
        assert not sample.from_sample
        assert not sample.is_external

    # WHEN checking if a flow cell check is applicable
    # THEN the method should return True
    assert mip_analysis_api._is_flow_cell_check_applicable(case_id=case.internal_id)


def test_is_flow_cell_check_not_applicable_when_external(cg_context, analysis_store: Store):
    """Tests that a check for flow cells being present on disk is applicable when given a case which has no
    down-sampled nor external samples."""

    mip_analysis_api = MipAnalysisAPI(cg_context, Pipeline.MIP_DNA)

    # GIVEN a case
    case: Family = analysis_store.get_cases()[0]

    # WHEN marking all of its samples as external
    for sample in case.samples:
        sample.application_version.application.is_external = True

    # WHEN checking if a flow cell check is applicable
    # THEN the method should return False
    assert not mip_analysis_api._is_flow_cell_check_applicable(case_id=case.internal_id)


def test_is_flow_cell_check_not_applicable_when_down_sampled(cg_context, analysis_store: Store):
    """Tests that a check for flow cells being present on disk is applicable when given a case which has no
    down-sampled nor external samples."""

    mip_analysis_api = MipAnalysisAPI(cg_context, Pipeline.MIP_DNA)

    # GIVEN a case
    case: Family = analysis_store.get_cases()[0]

    # WHEN marking all of its samples as down sampled from TestSample
    for sample in case.samples:
        sample.from_sample = "TestSample"

    # WHEN checking if a flow cell check is applicable
    # THEN the method should return False
    assert not mip_analysis_api._is_flow_cell_check_applicable(case_id=case.internal_id)
