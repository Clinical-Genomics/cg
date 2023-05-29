"""Test for analysis"""
from typing import List

import pytest

from cg.constants import Priority, GenePanelMasterList
from cg.constants.priority import SlurmQos
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.mip import MipAnalysisAPI


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
