from pydantic import BaseModel, validator


class MutantSampleConfig(BaseModel):
    CG_ID_project: str
    CG_ID_sample: str
    case_ID: str
    region_code: str
    lab_code: str
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

    @validator("region_code", "lab_code")
    def sanitize_values(cls, value):
        return value.split(" ")[0]
