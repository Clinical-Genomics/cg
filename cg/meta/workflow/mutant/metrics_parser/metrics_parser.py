from pathlib import Path
from cg.exc import CgError
from cg.io.csv import read_csv
from typing import Any
from cg.meta.workflow.mutant.metrics_parser.models import (
    SampleResults,
)
from cg.store.models import Case


class MutantResultsHeaderData:
    SAMPLE_NAME: str = "sample_name"
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
    def parse_samples_results(cls, case: Case, results_file_path: Path) -> dict[str, SampleResults]:
        """Takes a case object and a results_file_path and resturns dict[str, SampleResults] with sample.internal_id as keys."""

        raw_results: list[dict[str, Any]] = cls._get_raw_results(
            results_file_path=results_file_path
        )

        validated_results_list: list[SampleResults] = cls._get_validated_results_list(
            raw_results=raw_results
        )

        samples_results: dict[str, SampleResults] = cls._get_samples_results(
            case=case, results_list=validated_results_list
        )

        return samples_results

    @classmethod
    def _get_raw_results(cls, results_file_path: Path) -> list[dict[str, Any]]:
        """Parses raw_results from the results file."""
        try:
            raw_results: list[dict[Any, Any]] = [
                sample_results
                for sample_results in read_csv(file_path=results_file_path, read_to_dict=True)
            ]
        except FileNotFoundError as exception_object:
            raise CgError(f"Results file not found at {results_file_path}") from exception_object
        except Exception as exception_object:
            raise CgError(
                f"Not possible to read results file {results_file_path}."
            ) from exception_object
        return raw_results

    @classmethod
    def _get_altered_sample_result(cls, sample_result: dict[str, Any]) -> dict[str, Any]:
        """Takes a raw_sample_result with headers from the results file (MutantResultsHeaderRawData)
        and returns an altered_sample_result with the corrected headers from MutantResultsHeaderData.
        """
        altered_sample_result = {}
        for header, value in sample_result.items():
            new_header: str = cls.KEY_MAPPING.get(header, header)
            altered_sample_result[new_header] = value
        return altered_sample_result

    @classmethod
    def _get_validated_results_list(cls, raw_results: list[dict[str, Any]]) -> list[SampleResults]:
        """Takes raw_results and returns a list of validated SampleResults with the corrected headers."""
        validated_results_list = []
        for sample_result in raw_results:
            altered_sample_result: dict[str, Any] = cls._get_altered_sample_result(
                sample_result=sample_result
            )
            validated_result: SampleResults = SampleResults.model_validate(altered_sample_result)
            validated_results_list.append(validated_result)
        return validated_results_list

    @classmethod
    def _get_sample_name_to_id_mapping(cls, case: Case) -> dict[str, str]:
        sample_name_to_id_mapping: dict[str, str] = {}
        for sample in case.samples:
            sample_name_to_id_mapping[sample.name] = sample.internal_id
        return sample_name_to_id_mapping

    @classmethod
    def _get_samples_results(
        cls, case: Case, results_list: list[SampleResults]
    ) -> dict[str, SampleResults]:
        """Takes a Case object and a list of SampleResults and builds a dict[str, SampleResults] with
        sample_internal_ids as keys."""

        sample_name_to_id_mapping: dict[str, str] = cls._get_sample_name_to_id_mapping(case=case)

        samples_results: dict[str, SampleResults] = {}
        for result in results_list:
            sample_internal_id = sample_name_to_id_mapping[result.sample_name]
            samples_results[sample_internal_id] = result
        return samples_results
