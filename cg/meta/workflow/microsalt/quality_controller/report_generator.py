from pathlib import Path

from cg.io.json import write_json
from cg.meta.workflow.microsalt.quality_controller.models import QualityResult


class ReportGenerator:
    @staticmethod
    def report(out_file: Path, results: list[QualityResult]):
        formatted_results: list[dict] = []

        for result in results:
            formatted_result = {
                result.sample_id: {
                    "Passed QC": result.passes_qc,
                    "Passed QC Reads": result.passes_reads_qc,
                    "Passed QC Mapping": result.passes_mapping_qc,
                    "Passed QC Duplication": result.passes_duplication_qc,
                    "Passed QC Insert Size": result.passes_inserts_qc,
                    "Passed QC Coverage": result.passes_coverage_qc,
                    "Passed QC 10x Coverage": result.passes_10x_coverage_qc,
                }
            }
            formatted_results.append(formatted_result)

        write_json(file_path=out_file, content=formatted_results)
