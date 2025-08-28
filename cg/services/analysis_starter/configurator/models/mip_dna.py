from pydantic import Field

from cg.constants.constants import Workflow
from cg.services.analysis_starter.configurator.abstract_model import CaseConfig


class MIPDNACaseConfig(CaseConfig):
    conda_binary: str
    conda_environment: str
    email: str
    pipeline_binary: str
    pipeline_config_path: str
    slurm_qos: str
    start_after_recipe: str | None = Field(default=None, alias="start_after")
    start_with_recipe: str | None = Field(default=None, alias="start_with")
    workflow: Workflow = Workflow.MIP_DNA
    use_bwa_mem: bool

    def get_start_command(self) -> str:
        start_command = (
            "{conda_binary} run --name {conda_environment} {pipeline_binary} analyse rd_dna"
            " --config {pipeline_config_path} {case_id} --slurm_quality_of_service "
            "{slurm_qos} --email {email}"
        ).format(**self.model_dump())

        if self.start_after_recipe:
            start_command += f" --start_after_recipe {self.start_after_recipe}"

        if self.start_with_recipe:
            start_command += f" --start_with_recipe {self.start_with_recipe}"

        if self.use_bwa_mem:
            start_command += " --bwa_mem 1 --bwa_mem2 0"

        return start_command
