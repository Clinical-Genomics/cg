from pydantic import BaseModel, ConfigDict


class QCMetrics(BaseModel):
    """QC metrics analysis model."""
    model_config = ConfigDict(arbitrary_types_allowed=True)