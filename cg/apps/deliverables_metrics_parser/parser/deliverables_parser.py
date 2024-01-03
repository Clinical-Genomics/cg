"""Module to parse the metrics deliverables file."""
from enum import Enum
from pathlib import Path

from cg.apps.deliverables_metrics_parser.models.pipeline_metrics_deliverables import (
    MIPDNAMetricsDeliverables,
)
from cg.constants.constants import FileFormat
from cg.constants.pipeline import Pipeline
from cg.io.controller import ReadFile


class MetricsParserConstants(Enum):
    NAME: str = "name"
    VALUE: str = "value"
    ID: str = "id"
    METRICS: str = "metrics"


class MetricsDeliverablesParser:
    """Parent"""

    def __init__(self, case_id: str, pipeline: str):
        self.case_id: str = case_id
        self.pipeline: str = pipeline

    @staticmethod
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

    @staticmethod
    def _read_metrics_deliverables(file_path: Path) -> list[dict]:
        """Read the metrics deliverables file."""
        return ReadFile.get_content_from_file(file_format=FileFormat.YAML, file_path=file_path)

    @staticmethod
    def _get_metrics_from_content(content: list[dict[list[dict]]]) -> list[dict]:
        """Get the metrics from the deliverables content."""
        return content[MetricsParserConstants.METRICS]

    @staticmethod
    def _get_unique_sample_ids_in_content(content: list[dict]) -> set:
        """Get the unique sample ids present in the deliverables."""
        return {entry[MetricsParserConstants.ID] for entry in content}

    @staticmethod
    def extract_name_value_pairs(metrics: list[dict], sample_id: str):
        """
        Extract the name value pairs for all metrics and a given sample id.
            The YAML file contains unwanted fields here we extract only the name and value fields for each metric
        """
        extracted_name_value_pairs: list[dict] = []
        return (
            extracted_name_value_pairs.append(
                {entry[MetricsParserConstants.name]: entry[MetricsParserConstants.VALUE]}
            )
            for entry in metrics
            if entry[MetricsParserConstants.ID] == sample_id
        )

    def _format_metrics(self, metrics: list[dict]):
        """Reformat the metrics content per sample id."""
        sample_ids: set[str] = self._get_unique_sample_ids_in_content(metrics)
        sample_metrics: dict = {}
        for sample_id in sample_ids:
            sample_metrics[sample_id] = self.extract_name_value_pairs(
                metrics=metrics, sample_id=sample_id
            )
        return sample_metrics

    def _summarise_lane_metrics(self, pipeline: str):
        """Summarise lane metrics."""

    def parse_metrics_deliverables_file(self) -> None:
        """Parse the metrics deliverables file."""
        file_path: Path = self.get_metrics_deliverables_file_path(
            pipeline=self.pipeline, case_id=self.case_id
        )
        content: list[dict[list[dict]]] = self._read_metrics_deliverables(file_path)
        metrics: list[dict] = self._get_metrics_from_content(content)

        reformatted_metrics: list[dict] = self._format_metrics(metrics)

        return None
