import pytest

from cg.constants import DataDelivery, Workflow


@pytest.fixture
def fluffy_case_id() -> str:
    """Return a Fluffy case ID."""
    return "enlightendfox"


@pytest.fixture
def microsalt_mwr_case_id() -> str:
    """Return a microSALT case ID with MWR app tag."""
    return "microsalt_case_1"


@pytest.fixture
def microsalt_mwx_case_id() -> str:
    """Return a microSALT case ID with MWX app tag."""
    return "microsalt_case_2"


@pytest.fixture
def mip_case_id() -> str:
    """Return a MIP-DNA case ID."""
    return "yellowhog"


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
def delivery_cases(
    fluffy_case_id: str,
    microsalt_mwr_case_id: str,
    microsalt_mwx_case_id: str,
    mip_case_id: str,
) -> list[dict]:
    """Return a list of dictionary representations of cases."""
    return [
        _get_case_representation(
            case_id=fluffy_case_id,
            case_name=f"{fluffy_case_id}-1",
            workflow=Workflow.FLUFFY,
            data_delivery=DataDelivery.STATINA,
        ),
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
        _get_case_representation(
            case_id=mip_case_id,
            case_name=mip_case_id,
            workflow=Workflow.MIP_DNA,
            data_delivery=DataDelivery.ANALYSIS_SCOUT,
        ),
    ]
