"""Test for analysis"""
from cg.constants import Priority
from cg.constants.priority import SlurmQos
from cg.meta.workflow.analysis import AnalysisAPI


def test_get_priority_for_case(mocker, case_id: str):
    """Test qet Quality of service (SLURM QOS) from the case priority"""

    # GIVEN a case that has a priority
    mocker.patch.object(AnalysisAPI, "get_priority_for_case")
    AnalysisAPI.get_priority_for_case.return_value = Priority.research

    # When getting the SLURM QOS for the priority
    slurm_qos = AnalysisAPI.get_slurm_qos_for_case(AnalysisAPI, case_id=case_id)

    # THEN slurm QOS should be low
    assert slurm_qos is SlurmQos.LOW


def test_get_priority_for_case_when_standard(mocker, case_id: str):
    """Test qet Quality of service (SLURM QOS) a case with standard priority"""

    # GIVEN a case that has a priority
    mocker.patch.object(AnalysisAPI, "get_priority_for_case")
    AnalysisAPI.get_priority_for_case.return_value = Priority.standard

    # When getting the SLURM QOS for the priority
    slurm_qos = AnalysisAPI.get_slurm_qos_for_case(AnalysisAPI, case_id=case_id)

    # THEN slurm QOS should be normal
    assert slurm_qos is SlurmQos.NORMAL


def test_get_priority_for_case_when_express(mocker, case_id: str):
    """Test qet Quality of service (SLURM QOS) a case with express priority"""

    # GIVEN a case that has a priority
    mocker.patch.object(AnalysisAPI, "get_priority_for_case")
    AnalysisAPI.get_priority_for_case.return_value = Priority.express

    # When getting the SLURM QOS for the priority
    slurm_qos = AnalysisAPI.get_slurm_qos_for_case(AnalysisAPI, case_id=case_id)

    # THEN slurm QOS should be express
    assert slurm_qos is SlurmQos.EXPRESS
