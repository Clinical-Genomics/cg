from cg.constants import Workflow
from cg.constants.constants import FileFormat
from cg.constants.priority import Priority, SlurmQos
from cg.io.controller import ReadFile, WriteStream
from cg.services.analysis_starter.configurator.models.raredisease import RarediseaseCaseConfig
from cg.services.analysis_starter.submitters.seqera_platform.client import SeqeraPlatformClient
from cg.services.analysis_starter.submitters.seqera_platform.dtos import (
    LaunchRequest,
    PipelineResponse,
    WorkflowLaunchRequest,
)
from cg.services.analysis_starter.submitters.submitter import Submitter


class SeqeraPlatformSubmitter(Submitter):

    def __init__(self, client: SeqeraPlatformClient, compute_environment_ids: dict[SlurmQos, str]):
        self.client: SeqeraPlatformClient = client
        self.compute_environment_ids: dict[str, str] = compute_environment_ids

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
        parameters: dict = ReadFile.get_content_from_file(
            file_format=FileFormat.YAML, file_path=case_config.params_file
        )
        parameters_as_string = WriteStream.write_stream_from_content(
            content=parameters, file_format=FileFormat.YAML
        )
        slurm_qos: str = Priority.priority_to_slurm_qos()[case_config.case_priority]
        launch_request = LaunchRequest(
            computeEnvId=self.compute_environment_ids[slurm_qos],
            configText=f"includeConfig {case_config.nextflow_config_file.as_posix()}",
            paramsText=parameters_as_string,
            runName=case_config.case_id,
            workDir=case_config.work_dir.as_posix(),
            **pipeline_config.launch.model_dump(),
        )
        return WorkflowLaunchRequest(launch=launch_request)
