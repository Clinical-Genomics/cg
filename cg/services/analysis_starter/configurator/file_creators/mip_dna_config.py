from pathlib import Path

from cg.apps.lims import LimsAPI
from cg.constants.constants import DEFAULT_CAPTURE_KIT, FileExtensions
from cg.constants.tb import AnalysisType
from cg.exc import CgError
from cg.io.yaml import write_yaml
from cg.store.models import Case, CaseSample, Sample
from cg.store.store import Store


class MIPDNAConfigFileCreator:
    def __init__(self, lims_api: LimsAPI, store: Store):
        self.lims_api = lims_api
        self.store = store

    def create(self, case_id: str, bed_flag: str | None) -> None:
        bed_file: str | None = self._get_bed_file_name(bed_flag)
        content: dict = self._get_content(bed_file=bed_file, case_id=case_id)
        write_yaml(content=content, file_path=Path(""))

    def _get_content(self, bed_file: str | None, case_id: str) -> dict:
        content = {"case": "", "default_gene_panels": [], "samples": []}
        case: Case = self.store.get_case_by_internal_id_strict(case_id)
        samples_data = []
        for case_sample in case.links:
            sample_content: dict = self._get_sample_content(
                bed_file=bed_file, case_id=case_id, case_sample=case_sample
            )
            samples_data.append(sample_content)
        content["case"] = case.internal_id
        content["default_gene_panels"] = []
        content["samples"] = samples_data
        return content

    def _get_sample_bed_file(self, bed_file_name: str | None, case_id: str, sample: Sample) -> str:
        if bed_file_name:
            return bed_file_name
        if sample.prep_category == AnalysisType.WGS:
            return DEFAULT_CAPTURE_KIT
        else:
            return self._get_target_bed_from_lims(case_id)

    def _get_bed_file_name(self, bed_flag: str | None):
        if bed_flag is None:
            return None
        elif bed_flag.endswith(FileExtensions.BED):
            return bed_flag
        if bed_version := self.store.get_bed_version_by_short_name(bed_flag):
            return bed_version.filename
        raise CgError("Please provide a valid panel shortname or a path to panel.bed file!")

    def _get_target_bed_from_lims(self, case_id):
        return "mock_bed_file"

    def _get_sample_content(self, bed_file: str, case_id: str, case_sample: CaseSample) -> dict:
        sample: Sample = case_sample.sample
        bed_file: str = self._get_sample_bed_file(
            bed_file_name=bed_file, case_id=case_id, sample=sample
        )
        mother: str = case_sample.mother.internal_id if case_sample.mother else "0"
        father: str = case_sample.father.internal_id if case_sample.father else "0"

        return {
            "analysis_type": sample.prep_category,
            "capture_kit": bed_file,
            "expected_coverage": sample.application_version.application.min_sequencing_depth,
            "father": father,
            "mother": mother,
            "phenotype": case_sample.status,
            "sample_display_name": sample.name,
            "sample_id": sample.internal_id,
            "sex": sample.sex,
        }
