from pydantic import BaseModel

from cg.constants import Workflow
from cg.services.analysis_starter.configurator.abstract_model import CaseConfig


class MicrosaltConfigContent(BaseModel):
    CG_ID_project: str | None
    Customer_ID_project: str | None
    CG_ID_sample: str
    Customer_ID_sample: str
    organism: str
    priority: str
    reference: str | None
    Customer_ID: str
    application_tag: str
    date_arrival: str
    date_sequencing: str
    date_libprep: str
    method_libprep: str
    method_sequencing: str
    sequencing_qc_passed: bool


class MicrosaltCaseConfig(CaseConfig):
    binary: str
    conda_binary: str
    config_file: str
    environment: str
    fastq_directory: str
    workflow: Workflow = Workflow.MICROSALT

    def get_start_command(self) -> str:
        return (
            "{conda_binary} run --name {environment} "
            "{binary} analyse {config_file} --input {fastq_directory}".format(**self.model_dump())
        )
