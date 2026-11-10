from collections.abc import Iterator
from pathlib import Path
from typing import Any

from cg.constants.constants import FileExtensions, MultiQC
from cg.io.json import read_json
from cg.meta.workflow.nf_analysis import MultiQCSearchPattern
from cg.models.deliverables.metric_deliverables import MetricsBase, MultiqcDataJson
from cg.store.store import Store


class MultiQCParser:
    def __init__(self, status_db: Store) -> None:
        self.status_db = status_db

    def parse_and_validate(self, case_id: str, file: Path) -> None:
        multiqc_json = MultiqcDataJson(**read_json(file_path=file))
        metrics = []
        for pattern in self._get_multiqc_search_patterns(case_id=case_id):
            metrics_for_pattern: list[MetricsBase] = self.get_multiqc_metrics_for_sample(
                search_pattern=pattern.pattern,
                multiqc_json=multiqc_json,
                sample_id=pattern.sample_id,
                exact_match=self.is_multiqc_pattern_search_exact(),
            )
            metrics.extend(metrics_for_pattern)
        metrics = self.get_deduplicated_metrics(metrics=metrics)

    def _get_multiqc_search_patterns(self, case_id: str) -> list[MultiQCSearchPattern]:
        # TODO simplify this method to avoid the MultiQCSearchPattern
        """Return a list of MultiQC search patterns for a case.
        Each pattern pairs a search string with its corresponding sample ID.
        Search patterns are typically sample IDs used to extract metrics from MultiQC data."""
        sample_ids: Iterator[str] = self.status_db.get_sample_ids_by_case_id(case_id)
        return [
            MultiQCSearchPattern(pattern=sample_id, sample_id=sample_id) for sample_id in sample_ids
        ]

    def get_multiqc_metrics_for_sample(
        self,
        search_pattern: str,
        multiqc_json: MultiqcDataJson,
        sample_id: str,
        exact_match: bool = False,
    ) -> list[MetricsBase]:
        """Parse a MultiqcDataJson and returns a list of metrics."""
        metrics: list[MetricsBase] = []
        list_of_metric_dicts: list[dict[str, Any]] = multiqc_json.report_general_stats_data
        for section in list_of_metric_dicts:
            for subsection, metrics_dict in section.items():
                if self._is_pattern_found(
                    pattern=search_pattern, text=subsection, exact_match=exact_match
                ):
                    for metric_name, metric_value in metrics_dict.items():
                        metric: MetricsBase = self.get_multiqc_metric(
                            metric_name=metric_name, metric_value=metric_value, sample_id=sample_id
                        )
                        metrics.append(metric)
        return metrics

    def is_multiqc_pattern_search_exact(self) -> bool:
        """Return True if only exact pattern search is allowed to collect metrics information from MultiQC file.
        If false, pattern must be present but does not need to be exact."""
        return False

    @staticmethod
    def get_deduplicated_metrics(metrics: list[MetricsBase]) -> list[MetricsBase]:
        """Return deduplicated metrics based on metric ID and name. If duplicated entries are found
        only the first one will be kept."""
        deduplicated_metric_id_name = set([])
        deduplicated_metrics: list = []
        for metric in metrics:
            if (metric.id, metric.name) not in deduplicated_metric_id_name:
                deduplicated_metric_id_name.add((metric.id, metric.name))
                deduplicated_metrics.append(metric)
        return deduplicated_metrics

    def get_multiqc_metric(
        self, metric_name: str, metric_value: str | int | float, sample_id: str
    ) -> MetricsBase:
        """Return a MetricsBase object for a given metric."""
        return MetricsBase(
            header=None,
            id=sample_id,
            input=MultiQC.MULTIQC_DATA + FileExtensions.JSON,
            name=metric_name,
            step=MultiQC.MULTIQC,
            value=metric_value,
            condition=self.get_qc_conditions_for_workflow(sample_id).get(metric_name, None),
        )

    @staticmethod
    def _is_pattern_found(pattern: str, text: str, exact_match: bool) -> bool:
        if exact_match:
            is_pattern_found: bool = pattern == text
        else:
            is_pattern_found: bool = pattern in text
        return is_pattern_found

    def get_qc_conditions_for_workflow(self, sample_id) -> dict:
        # TODO: Fill this out for Trana
        # TODO: Make this vary on workflow
        pass
