from pathlib import Path

from cg.constants.constants import FileFormat
from cg.constants.priority import SlurmQos
from cg.io.controller import ReadFile, WriteStream
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
        parameters: dict = ReadFile.get_content_from_file(
            file_format=FileFormat.YAML, file_path=Path(case_config.params_file)
        )
        parameters_as_string = WriteStream.write_stream_from_content(
            content=parameters, file_format=FileFormat.YAML
        )
        launch_request = LaunchRequest(
            computeEnvId=self.compute_environment_ids[case_config.case_priority],
            configProfiles=case_config.config_profiles,
            configText=f"includeConfig '{case_config.nextflow_config_file}'",
            paramsText=parameters_as_string,
            pipeline=case_config.pipeline_repository,
            preRunScript=case_config.pre_run_script,
            revision=case_config.revision,
            runName=case_config.case_id,
            stubRun=case_config.stub_run,
            workDir=case_config.work_dir,
        )
        return WorkflowLaunchRequest(launch=launch_request)
