"""Module to parse the metrics deliverables file."""
from pathlib import Path

from cg.apps.deliverables_metrics_parser.models.pipeline_metrics_deliverables import (
    MIPDNAMetricsDeliverables,
)
from cg.constants.constants import FileFormat
from cg.constants.pipeline import Pipeline
from cg.io.controller import ReadFile


def get_metrics_deliverables_file_path(pipeline: str, case_id: str) -> Path:
    """Returns the metrics deliverables from the pipeline for a case."""
    pipelines = {
        Pipeline.MIPDNA: "/home/proj/production/rare-disease/cases/{case_id}/analysis/{case_id}_metrics_deliverables.yaml",
        Pipeline.MIPRNA: "/home/proj/production/rare-disease/cases/{case_id}/analysis/{case_id}_metrics_deliverables.yaml",
        Pipeline.BALSAMIC: "/home/proj/production/cancer/cases/{case_id}/analysis/qc/{case_id}_metrics_deliverables.yaml",
        Pipeline.RNAFUSION: "/home/proj/production/rnafusion/cases/{case_id}/{case_id}_metrics_deliverables.yaml",
        Pipeline.MUTANT: "/home/proj/production/mutant/cases/{case_id}/results/{case_id}_metrics_deliverables.yaml",
    }

    if pipeline in pipelines:
        return Path(pipelines[pipeline].format(case_id=case_id))
    else:
        raise ValueError(f"Invalid pipeline name: {pipeline}")


def read_metrics_deliverables(file_path: Path) -> list[dict]:
    """Read the metrics deliverables file."""
    return ReadFile.get_content_from_file(file_format=FileFormat.YAML, file_path=file_path)


def parse_metrics_deliverables_file(content: list[dict]) -> MIPDNAMetricsDeliverables:
    pass
