from pathlib import Path

from cg.apps.lims import LimsAPI
from cg.constants.constants import FileExtensions
from cg.io.yaml import write_yaml
from cg.store.models import BedVersion, Case
from cg.store.store import Store


class MIPDNAConfigFileCreator:
    def __init__(self, lims_api: LimsAPI, store: Store):
        self.lims_api = lims_api
        self.store = store

    def create(self, case_id: str, bed_flag: str | None) -> None:
        bed_file: str | None = self._get_bed_file_name(bed_flag)
        content: dict = self._get_content(bed_file=bed_file, case_id=case_id)
        write_yaml(content="", file_path=Path(""))

    def _get_content(self, bed_file: str | None, case_id: str) -> dict:
        content = {"case": "", "default_gene_panels": [], "samples": []}
        case: Case = self.store.get_case_by_internal_id_strict(case_id)
        bed_file = self._get_sample_bed_file()
        return content

    def _get_sample_bed_file(self):
        return "bed_file.bed"

    def _get_bed_file_name(self, bed_flag: str | None):
        if bed_flag is None:
            return None
        elif bed_flag.endswith(FileExtensions.BED):
            return bed_flag
        bed_version: BedVersion | None = self.store.get_bed_version_by_short_name(
            bed_version_short_name=bed_flag
        )
        if not bed_version:
            raise CgError("Please provide a valid panel shortname or a path to panel.bed file!")

        return bed_version.filename
