from pathlib import Path

from cg.constants.priority import SlurmQos
from cg.io.yaml import read_yaml, write_yaml_stream
from cg.services.analysis_starter.configurator.models.nextflow import NextflowCaseConfig
from cg.services.analysis_starter.submitters.seqera_platform.client import SeqeraPlatformClient
from cg.services.analysis_starter.submitters.seqera_platform.dtos import (
    LaunchRequest,
    WorkflowLaunchRequest,
)
from cg.services.analysis_starter.submitters.submitter import Submitter


class SeqeraPlatformSubmitter(Submitter):

    def __init__(self, client: SeqeraPlatformClient, compute_environment_ids: dict[SlurmQos, str]):
        self.client: SeqeraPlatformClient = client
        self.compute_environment_ids: dict[str, str] = compute_environment_ids

    def submit(self, case_config: NextflowCaseConfig) -> str:
        """Starts a case and returns the workflow id for the job."""
        run_request: WorkflowLaunchRequest = self._create_launch_request(case_config)
        return self.client.run_case(run_request)

    def _create_launch_request(self, case_config: NextflowCaseConfig) -> WorkflowLaunchRequest:
        parameters: dict = read_yaml(Path(case_config.params_file))
        parameter_stream: str = write_yaml_stream(parameters)
        launch_request = LaunchRequest(
            computeEnvId=self.compute_environment_ids[case_config.case_priority],
            configProfiles=case_config.config_profiles,
            configText=f"includeConfig '{case_config.nextflow_config_file}'",
            paramsText=parameter_stream,
            pipeline=case_config.pipeline_repository,
            preRunScript=case_config.pre_run_script,
            revision=case_config.revision,
            runName=case_config.case_id,
            workDir=case_config.work_dir,
        )
        return WorkflowLaunchRequest(launch=launch_request)
