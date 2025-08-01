from pydantic import BaseModel


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
    workDir: str


class WorkflowLaunchRequest(BaseModel):
    """Structured as the request for the /workflow/launch endpoint."""

    launch: LaunchRequest
