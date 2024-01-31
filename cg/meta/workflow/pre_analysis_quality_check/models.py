from pydantic import BaseModel


class SequencingQualityMetrics(BaseModel):
    sequencing_quality: bool


class PreAnalysisQualityMetrics(BaseModel):
    sequencing_metrics: SequencingQualityMetrics
