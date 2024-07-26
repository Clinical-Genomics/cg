from pathlib import Path

from cg.services.post_processing.abstract_classes import PostProcessingMetricsParser
from cg.services.post_processing.pacbio.metrics_parser.models import (
    ControlMetrics,
    HiFiMetrics,
    PacBioMetrics,
    PolymeraseMetrics,
    ProductivityMetrics,
    SmrtlinkDatasetsMetrics,
)
from cg.services.post_processing.pacbio.metrics_parser.utils import (
    parse_control_metrics,
    parse_dataset_metrics,
    parse_hifi_metrics,
    parse_polymerase_metrics,
    parse_productivity_metrics,
)


class PacBioMetricsParser(PostProcessingMetricsParser):
    """Class for parsing PacBio sequencing metrics."""

    @staticmethod
    def parse_metrics(metrics_files: list[Path]) -> PacBioMetrics:
        """Return all the relevant PacBio metrics parsed in a single Pydantic object."""
        hifi_metrics: HiFiMetrics = parse_hifi_metrics(metrics_files)
        control_metrics: ControlMetrics = parse_control_metrics(metrics_files)
        productivity_metrics: ProductivityMetrics = parse_productivity_metrics(metrics_files)
        polymerase_metrics: PolymeraseMetrics = parse_polymerase_metrics(metrics_files)
        dataset_metrics: SmrtlinkDatasetsMetrics = parse_dataset_metrics(metrics_files)

        return PacBioMetrics(
            hifi=hifi_metrics,
            control=control_metrics,
            productivity=productivity_metrics,
            polymerase=polymerase_metrics,
            dataset_metrics=dataset_metrics,
        )
