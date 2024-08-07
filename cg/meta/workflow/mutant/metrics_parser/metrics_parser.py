from pathlib import Path

from pydantic import TypeAdapter
from cg.io.csv import read_csv
from typing import Any
from cg.meta.workflow.mutant.metrics_parser.models import (
    SampleResults,
)
from cg.store.models import Case


class MetricsParser:
    @classmethod
    def parse_samples_results(cls, case: Case, results_file_path: Path) -> dict[str, SampleResults]:
        """Takes a case object and a results_file_path and resturns dict[str, SampleResults] with sample.internal_id as keys."""

        validated_results_list: list[SampleResults] = cls._get_validated_results_list(
            results_file_path=results_file_path
        )

        samples_results: dict[str, SampleResults] = cls._get_samples_results(
            case=case, results_list=validated_results_list
        )

        return samples_results

    @classmethod
    def _get_validated_results_list(cls, results_file_path: Path) -> list[SampleResults]:
        """Parses the results file and returns a list of validated SampleResults."""

        raw_results: list[dict[Any, Any]] = read_csv(file_path=results_file_path, read_to_dict=True)
        adapter = TypeAdapter(list[SampleResults])
        return adapter.validate_python(raw_results)

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
        """Return the mapping of sample internal ids to SampleResults for a case."""

        sample_name_to_id_mapping: dict[str, str] = cls._get_sample_name_to_id_mapping(case=case)

        samples_results: dict[str, SampleResults] = {}
        for result in results_list:
            sample_internal_id = sample_name_to_id_mapping[result.sample_name]
            samples_results[sample_internal_id] = result
        return samples_results
