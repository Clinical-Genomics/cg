from cg.constants import Priority, Workflow
from cg.constants.constants import FileFormat
from cg.io.controller import ReadFile
from cg.services.analysis_starter.configurator.models.raredisease import RarediseaseCaseConfig
from cg.services.analysis_starter.submitters.seqera_platform.client import SeqeraPlatformClient
from cg.services.analysis_starter.submitters.seqera_platform.dtos import (
    LaunchRequest,
    PipelineResponse,
    WorkflowLaunchRequest,
)
from cg.services.analysis_starter.submitters.submitter import Submitter


class SeqeraPlatformSubmitter(Submitter):

    def __init__(self, client: SeqeraPlatformClient, compute_environment_ids: dict[Priority, str]):
        self.client: SeqeraPlatformClient = client
        self.compute_environment_ids: dict[Priority, str] = compute_environment_ids

    def submit(self, case_config) -> str:
        """Starts a case and returns the workflow id for the job."""
        workflow: Workflow = case_config.workflow
        pipeline_config: PipelineResponse = self.client.get_pipeline_config(workflow)
        run_request: WorkflowLaunchRequest = self._create_launch_request(
            case_config=case_config, pipeline_config=pipeline_config
        )
        return self.client.run_case(run_request)

    def _create_launch_request(
        self, case_config: RarediseaseCaseConfig, pipeline_config: PipelineResponse
    ) -> WorkflowLaunchRequest:
        parameters: str = ReadFile.get_content_from_file(
            file_format=FileFormat.YAML, file_path=case_config.params_file
        )
        launch_request = LaunchRequest(
            computeEnvId=self.compute_environment_ids[case_config.case_priority],
            configText=f"includeConfig {case_config.nextflow_config_file.as_posix()}",
            paramsText=parameters,
            runName=case_config.case_id,
            workDir=case_config.work_dir.as_posix(),
            **pipeline_config.launch.model_dump(),
        )
        return WorkflowLaunchRequest(launch=launch_request)
