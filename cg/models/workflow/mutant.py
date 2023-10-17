from pydantic import AfterValidator, BaseModel
from typing_extensions import Annotated

from cg.models.workflow.validators import get_first_word


class MutantSampleConfig(BaseModel):
    CG_ID_project: str
    CG_ID_sample: str
    case_ID: str
    region_code: Annotated[str, AfterValidator(get_first_word)]
    lab_code: Annotated[str, AfterValidator(get_first_word)]
    priority: str
    Customer_ID_project: int
    Customer_ID_sample: str
    customer_id: str
    application_tag: str
    date_arrival: str
    date_libprep: str
    date_sequencing: str
    method_libprep: str
    method_sequencing: str
    sequencing_qc_pass: bool
    selection_criteria: str
    primer: str
