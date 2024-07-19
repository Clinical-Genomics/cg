from pathlib import Path
from cg.services.pacbio.metrics.models import (
    ControlMetrics,
    HiFiMetrics,
    PacBioMetrics,
    PolymeraseMetrics,
    ProductivityMetrics,
    SmrtlinkDatasetsMetrics,
)
from cg.services.pacbio.metrics.utils import (
    parse_control_metrics,
    parse_hifi_metrics,
    parse_polymerase_metrics,
    parse_productivity_metrics,
    parse_dataset_metrics,
)


class PacBioMetricsParser:
    """Class for parsing PacBio sequencing metrics."""

    def parse_metrics(self, smrt_cell_path: Path) -> PacBioMetrics:
        """Return all the relevant PacBio metrics parsed in a single Pydantic object."""
        report_dir = Path(smrt_cell_path, "statistics")
        hifi_metrics: HiFiMetrics = parse_hifi_metrics(report_dir)
        control_metrics: ControlMetrics = parse_control_metrics(report_dir)
        productivity_metrics: ProductivityMetrics = parse_productivity_metrics(report_dir)
        polymerase_metrics: PolymeraseMetrics = parse_polymerase_metrics(report_dir)
        dataset_metrics: SmrtlinkDatasetsMetrics = parse_dataset_metrics(report_dir)

        return PacBioMetrics(
            hifi_metrics=hifi_metrics,
            control_metrics=control_metrics,
            productivity_metrics=productivity_metrics,
            polymerase_metrics=polymerase_metrics,
            dataset_metrics=dataset_metrics,
        )
