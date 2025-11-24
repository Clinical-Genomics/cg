from datetime import datetime
from pathlib import Path

from cg.constants.priority import SlurmQos
from cg.exc import SeqeraError
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

    def submit(self, case_config: NextflowCaseConfig) -> NextflowCaseConfig:
        """Starts a case and returns the workflow id for the job."""
        new_case_config: NextflowCaseConfig = case_config.model_copy()
        run_request: WorkflowLaunchRequest = self._create_launch_request(new_case_config)
        response: dict = self.client.run_case(run_request)
        if (not response.get("sessionId")) or (not response.get("workflowId")):
            raise SeqeraError(f"sessionId and/or workflowId missing from response: {response}")
        new_case_config.session_id = response["sessionId"]
        new_case_config.workflow_id = response["workflowId"]
        return new_case_config

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
            resume=case_config.resume,
            revision=case_config.revision,
            runName=self._create_run_name(case_id=case_config.case_id, resume=case_config.resume),
            sessionId=case_config.session_id,
            workDir=case_config.work_dir,
        )
        return WorkflowLaunchRequest(launch=launch_request)

    @staticmethod
    def _create_run_name(case_id: str, resume: bool) -> str:
        if resume:
            return f"{case_id}_resumed_{datetime.now().strftime('%Y-%m-%d_%H-%M')}"
        else:
            return case_id
