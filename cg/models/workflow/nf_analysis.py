from pydantic.v1 import BaseModel


class PipelineParameters(BaseModel):
    clusterOptions: str
    priority: str
