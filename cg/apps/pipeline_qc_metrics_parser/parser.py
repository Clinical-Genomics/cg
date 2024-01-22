"""Parse the pipeline qc metrics file."""
from cg.constants.constants import FileFormat
from cg.io.controller import ReadFile
from cg.models.pipeline_qc_metrics.pipeline_qc_metrics import PipelineQCMetric


def parse_pipeline_qc_metric_file(file_path) -> PipelineQCMetric:
    """Parse the pipeline qc metric file."""
    json_content = ReadFile.get_content_from_file(file_format=FileFormat.JSON, file_path=file_path)
    return PipelineQCMetric.model_validate(json_content)
