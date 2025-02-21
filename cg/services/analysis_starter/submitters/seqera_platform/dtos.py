from pydantic import BaseModel


class LaunchResponse:
    configProfiles: list[str]
    pipeline: str
    preRunScript: str
    pullLatest: str
    revision: str


class PipelineResponse(BaseModel):
    """Structured as the response of the /pipelines/:pipelineId endpoint."""

    launch: LaunchResponse


class LaunchRequest(BaseModel):
    computeEnvId: str
    configProfiles: list[str]
    configText: str
    paramsText: str
    pipeline: str
    preRunScript: str
    pullLatest: bool = False
    resume: bool = False
    revision: str
    runName: str
    sessionId: str | None = None
    stubRun: bool = False
    workDir: str


class WorkflowLaunchRequest(BaseModel):
    """Structured as the request for the /workflow/launch endpoint."""

    launch: LaunchRequest
