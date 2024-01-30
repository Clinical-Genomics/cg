from pydantic import BaseModel


class SequencingQualityMetrics(BaseModel):
    pass


class PreAnalysisQualityMetrics(BaseModel):
    sequencing_metrics: SequencingQualityMetrics = None
