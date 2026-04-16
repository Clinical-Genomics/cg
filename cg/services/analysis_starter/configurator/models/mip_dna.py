from cg.constants.constants import Workflow
from cg.constants.priority import SlurmQos
from cg.services.analysis_starter.configurator.abstract_model import CaseConfig


class MIPDNACaseConfig(CaseConfig):
    conda_binary: str
    conda_environment: str
    email: str
    pipeline_binary: str
    pipeline_command: str
    pipeline_config_path: str
    slurm_qos: SlurmQos
    start_after: str | None = None
    start_with: str | None = None
    workflow: Workflow = Workflow.MIP_DNA
    use_bwa_mem: bool

    def get_start_command(self) -> str:
        start_command = (
            "{conda_binary} run --name {conda_environment} {pipeline_binary} {pipeline_command}"
            " --config {pipeline_config_path} {case_id} --slurm_quality_of_service "
            "{slurm_qos} --email {email}"
        ).format(**self.model_dump())

        if self.start_after:
            start_command += f" --start_after_recipe {self.start_after}"

        if self.start_with:
            start_command += f" --start_with_recipe {self.start_with}"

        if self.use_bwa_mem:
            start_command += " --bwa_mem 1 --bwa_mem2 0"

        return start_command
