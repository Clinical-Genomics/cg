from pathlib import Path
from cg.io.csv import read_csv
from typing import Any
from cg.meta.workflow.mutant.metrics_parser.models import QualityMetrics, SampleResults


class MutantResultsHeaderData:
    SAMPLE_NAME: str = "sample"
    SELECTION: str = "selection"
    REGION_CODE: str = "region_code"
    TICKET: str = "ticket"
    PCT_N_BASES: str = "pct_n_bases"
    PCT_10X_COVERAGE: str = "pct_10x_coverage"
    QC_PASS: str = "qc_pass"
    LINEAGE: str = "lineage"
    PANGOLIN_DATA_VERSION: str = "pangolin_data_version"
    VOC: str = "voc"
    MUTATIONS: str = "mutations"


class MutantResultsHeaderRawData:
    SAMPLE_NAME: str = "Sample"
    SELECTION: str = "Selection"
    REGION_CODE: str = "Region Code"
    TICKET: str = "Ticket"
    PCT_N_BASES: str = "%N_bases"
    PCT_10X_COVERAGE: str = "%10X_coverage"
    QC_PASS: str = "QC_pass"
    LINEAGE: str = "Lineage"
    PANGOLIN_DATA_VERSION: str = "Pangolin_data_version"
    VOC: str = "VOC"
    MUTATIONS: str = "Mutations"


class MetricsParser:
    KEY_MAPPING: dict[str, str] = {
        MutantResultsHeaderRawData.SAMPLE_NAME: MutantResultsHeaderData.SAMPLE_NAME,
        MutantResultsHeaderRawData.SELECTION: MutantResultsHeaderData.SELECTION,
        MutantResultsHeaderRawData.REGION_CODE: MutantResultsHeaderData.REGION_CODE,
        MutantResultsHeaderRawData.TICKET: MutantResultsHeaderData.TICKET,
        MutantResultsHeaderRawData.PCT_N_BASES: MutantResultsHeaderData.PCT_N_BASES,
        MutantResultsHeaderRawData.PCT_10X_COVERAGE: MutantResultsHeaderData.PCT_10X_COVERAGE,
        MutantResultsHeaderRawData.QC_PASS: MutantResultsHeaderData.QC_PASS,
        MutantResultsHeaderRawData.LINEAGE: MutantResultsHeaderData.LINEAGE,
        MutantResultsHeaderRawData.PANGOLIN_DATA_VERSION: MutantResultsHeaderData.PANGOLIN_DATA_VERSION,
        MutantResultsHeaderRawData.VOC: MutantResultsHeaderData.VOC,
        MutantResultsHeaderRawData.MUTATIONS: MutantResultsHeaderData.MUTATIONS,
    }

    @classmethod
    def alter_metric_keys(cls, metric: dict[str, Any]) -> dict[str, Any]:
        altered_metric = {}
        for key, value in metric.items():
            new_key: str = cls.KEY_MAPPING.get(key, key)
            altered_metric[new_key] = value
        return altered_metric

    @classmethod
    def parse_sample_results(cls, file_path: Path) -> QualityMetrics:  # dict[str, SampleResults]:
        with open(file_path, mode="r") as file:
            raw_results: list[dict[str, Any]] = [
                metric for metric in read_csv(file, read_to_dict=True)
            ]

        results = [cls.alter_metric_keys(metric) for metric in raw_results]

        validated_results: dict[str, SampleResults] = {}
        for result in results:
            validated_results[
                result[MutantResultsHeaderData.SAMPLE_NAME]
            ] = SampleResults.model_validate(result)

        return QualityMetrics.model_validate(validated_results)

    
