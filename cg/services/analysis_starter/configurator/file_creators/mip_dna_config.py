from pathlib import Path

from cg.apps.lims import LimsAPI
from cg.io.yaml import write_yaml
from cg.store.store import Store


class MIPDNAConfigFileCreator:
    def __init__(self, lims_api: LimsAPI, store: Store):
        self.lims_api = lims_api
        self.store = store

    def create(self, case_id: str, bed_flag: str | None) -> None:
        bed_file: str | None = self._get_bed_file_name(bed_flag)
        write_yaml(content="", file_path=Path(""))

    def _get_content(
        self,
        bed_file: str,
    ):
        bed_file = self._get_bed_file()
        pass

    def _get_bed_file(self):
        return "bed_file.bed"
