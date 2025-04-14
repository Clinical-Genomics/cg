import pytest

from cg.constants import DataDelivery, Workflow


@pytest.fixture
def microsalt_mwr_case_id() -> str:
    """Return a microSALT case ID."""
    return "microsalt_case_1"


@pytest.fixture
def microsalt_mwx_case_id() -> str:
    """Return a microSALT case ID."""
    return "microsalt_case_2"


def _get_case_representation(
    case_id: str, case_name: str, workflow: Workflow, data_delivery: DataDelivery
) -> dict:
    """Return a dictionary representation of a case to be added to a store."""
    return {
        "case_id": case_id,
        "case_name": case_name,
        "data_analysis": workflow,
        "data_delivery": data_delivery,
    }


@pytest.fixture
def delivery_cases(microsalt_mwr_case_id: str, microsalt_mwx_case_id: str) -> list[dict]:
    """Return a dictionary of case IDs."""
    return [
        _get_case_representation(
            case_id=microsalt_mwr_case_id,
            case_name=microsalt_mwr_case_id,
            workflow=Workflow.MICROSALT,
            data_delivery=DataDelivery.FASTQ_QC_ANALYSIS,
        ),
        _get_case_representation(
            case_id=microsalt_mwx_case_id,
            case_name=microsalt_mwx_case_id,
            workflow=Workflow.MICROSALT,
            data_delivery=DataDelivery.FASTQ_QC_ANALYSIS,
        ),
    ]
