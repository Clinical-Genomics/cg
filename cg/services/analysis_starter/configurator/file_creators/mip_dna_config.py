from pathlib import Path

from cg.apps.lims import LimsAPI
from cg.io.yaml import write_yaml
from cg.store.store import Store


class MIPDNAConfigFileCreator:
    def __init__(self, lims_api: LimsAPI, store: Store):
        self.lims_api = lims_api
        self.store = store

    def create(self, case_id: str) -> None:
        write_yaml(content="", file_path=Path(""))