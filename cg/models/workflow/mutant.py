from pydantic import BaseModel
import datetime as dt


class MutantSampleConfig(BaseModel):
    cg_project_id: str = "MIC3109"  # Is this ticket number or case_id?
    cg_sample_id: str = "MIC3109A1"
    customer_project_id: str = "AAA0000B1"  # Is this customers case name or ticket id?
    customer_sample_id: str = "MG-001"
    customer_id: str = "cust000"
    application_tag: str = "MWGNXTR003"
    date_arrival: dt.datetime = "0001-01-01 00:00:00"
    date_libprep: dt.datetime = "0001-01-01 00:00:00"
    date_sequencing: dt.datetime = "0001-01-01 00:00:00"
    method_libprep: str = "1764:2"
    method_sequencing: str = "1036:15"
    cg_qc_pass: bool = True
    selection_criteria: str = ""
    # please add more fields which wrapper of the  custs might want
