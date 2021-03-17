from pydantic import BaseModel


class MutantSampleConfig(BaseModel):
    cg_project_id: str = "MIC3109"  # Is this ticket number or case_id?
    cg_sample_id: str = "MIC3109A1"
    case_id: str = "yellowhog"
    region_code: str = "01"
    lab_code: str = "SE100"
    priority: str = "normal"
    customer_project_id: str = "AAA0000B1"  # Is this customers case name or ticket id?
    customer_sample_id: str = "MG-001"
    customer_id: str = "cust000"
    application_tag: str = "MWGNXTR003"
    date_arrival: str = "0001-01-01 00:00:00"
    date_libprep: str = "0001-01-01 00:00:00"
    date_sequencing: str = "0001-01-01 00:00:00"
    method_libprep: str = "1764:2"
    method_sequencing: str = "1036:15"
    cg_qc_pass: bool = True
    selection_criteria: str = "zombie"
    # please add more fields which wrapper of the  custs might want
