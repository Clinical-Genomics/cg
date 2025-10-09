import logging
from pathlib import Path

from cg.apps.lims import LimsAPI
from cg.constants.constants import DEFAULT_CAPTURE_KIT, FileExtensions, StatusOptions
from cg.constants.tb import AnalysisType
from cg.io.yaml import write_yaml
from cg.store.models import BedVersion, Case, CaseSample, Sample
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class MIPDNAConfigFileCreator:
    def __init__(self, lims_api: LimsAPI, root: str, store: Store):
        self.lims_api = lims_api
        self.root = root
        self.store = store

    def create(self, case_id: str, bed_flag: str | None, file_path: Path) -> None:
        provided_bed_file: str | None = self._get_bed_file_name(bed_flag) if bed_flag else None
        content: dict = self._get_content(provided_bed_file=provided_bed_file, case_id=case_id)
        write_yaml(
            content=content,
            file_path=file_path,
        )
        LOG.info(f"Created MIP-DNA config file for case {case_id} at {file_path}")

    def _get_content(self, provided_bed_file: str | None, case_id: str) -> dict:
        case: Case = self.store.get_case_by_internal_id_strict(case_id)
        samples_data = []
        for case_sample in case.links:
            sample_content: dict = self._get_sample_content(
                provided_bed_file=provided_bed_file, case_sample=case_sample
            )
            samples_data.append(sample_content)
        return {
            "case": case.internal_id,
            "default_gene_panels": case.panels,
            "samples": samples_data,
        }

    def _get_sample_content(self, provided_bed_file: str | None, case_sample: CaseSample) -> dict:
        case: Case = case_sample.case
        sample: Sample = case_sample.sample
        bed_file: str = provided_bed_file or self._get_sample_bed_file(case=case, sample=sample)
        mother: str = case_sample.mother.internal_id if case_sample.mother else "0"
        father: str = case_sample.father.internal_id if case_sample.father else "0"

        phenotype = case_sample.status
        if len(case.links) == 1 and case_sample.status == StatusOptions.UNKNOWN:
            phenotype = StatusOptions.UNAFFECTED.value

        return {
            "analysis_type": sample.prep_category,
            "capture_kit": bed_file,
            "expected_coverage": sample.application_version.application.min_sequencing_depth,
            "father": father,
            "mother": mother,
            "phenotype": phenotype,
            "sample_display_name": sample.name,
            "sample_id": sample.internal_id,
            "sex": sample.sex,
        }

    def _get_bed_file_name(self, bed_flag: str) -> str:
        if bed_flag.endswith(FileExtensions.BED):
            return bed_flag
        bed_version: BedVersion = self.store.get_bed_version_by_short_name_strict(bed_flag)
        return bed_version.filename

    def _get_sample_bed_file(self, case: Case, sample: Sample) -> str:
        if sample.prep_category == AnalysisType.WGS:
            return DEFAULT_CAPTURE_KIT
        return self._get_target_bed_from_lims(case)

    def _get_target_bed_from_lims(self, case: Case) -> str:
        """Get target bed filename from LIMS."""
        # Should the input to the function be the sample instead of the case?
        sample: Sample = case.samples[0]
        bed_shortname: str = self.lims_api.get_capture_kit_strict(
            sample.from_sample or sample.internal_id
        )
        bed_version: BedVersion = self.store.get_bed_version_by_short_name_strict(bed_shortname)
        return bed_version.filename
