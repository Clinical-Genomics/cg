"""Module to parse the metrics deliverables file."""
import operator
from enum import Enum
from functools import reduce
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


# we need some kind of standardisation across pipelines for these fields
READ_INFORMATION_FIELDS = [
    "reads_mapped",
    "raw_total_sequences",
    "percentage_mapped_reads",
    "PCT_PF_READS_IMPROPER_PAIRS",
]


def generate_metrics_deliverables_model(
    sample_id: str, sample_metrics: dict
) -> MIPDNAMetricsDeliverables:
    """Generate the metrics deliverable model for a sample."""
    sample_metrics["id"] = sample_id
    return MIPDNAMetricsDeliverables.model_validate(sample_metrics)


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


def get_metrics_from_content(content: list[dict[list[dict]]]) -> list[dict]:
    """Get the metrics from the deliverables content."""
    return content[MetricsParserConstants.METRICS.value]


def get_unique_sample_ids_in_content(content: list[dict]) -> set:
    """Get the unique sample ids present in the deliverables."""
    return {entry[MetricsParserConstants.ID.value] for entry in content}


def extract_name_value_pairs(metrics: list[dict], sample_id: str) -> list[dict]:
    """
    Extract the name value pairs for all metrics and a given sample id.
        The YAML file contains unwanted fields here we extract only the name and value fields for each metric.
    """
    extracted_name_value_pairs: list[dict] = []
    for entry in metrics:
        if (
            entry["id"] == sample_id
            # Skipping read information for now TO DO remove this.
            and entry[MetricsParserConstants.NAME.value] not in READ_INFORMATION_FIELDS
        ):
            extracted_name_value_pairs.append(
                {
                    entry[MetricsParserConstants.NAME.value]: entry[
                        MetricsParserConstants.VALUE.value
                    ]
                }
            )
    return extracted_name_value_pairs


def order_metrics_per_sample(metrics: list[dict]) -> dict[list[dict]]:
    """Order the metrics content per sample id."""
    sample_ids: set[str] = get_unique_sample_ids_in_content(metrics)
    sample_metrics: dict = {}
    for sample_id in sample_ids:
        # TO DO Parse read information once decided on formatting of deliverables
        sample_metrics[sample_id] = extract_name_value_pairs(metrics=metrics, sample_id=sample_id)
    return sample_metrics


def get_metrics_deliverables_model(
    metrics_per_sample: dict[list[dict]],
) -> list[MIPDNAMetricsDeliverables]:
    """Get the metrics deliverables model."""
    metrics_models: list = []
    for key, values in metrics_per_sample.items():
        sample_id: str = key.__str__()
        sample_metrics: dict = reduce(operator.ior, values, {})
        metrics_models.append(
            generate_metrics_deliverables_model(sample_id=sample_id, sample_metrics=sample_metrics)
        )
    return metrics_models


def parse_metrics_deliverables_file(pipeline: str, case_id: str) -> list[MIPDNAMetricsDeliverables]:
    """Parse the metrics deliverables file."""
    file_path: Path = get_metrics_deliverables_file_path(pipeline=pipeline, case_id=case_id)
    content: list[dict[list[dict]]] = read_metrics_deliverables(file_path)
    metrics: list[dict] = get_metrics_from_content(content)
    metrics_per_sample: dict[list[dict]] = order_metrics_per_sample(metrics)
    return get_metrics_deliverables_model(metrics_per_sample)
