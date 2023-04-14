from pathlib import Path
from typing import List

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.meta.archive.ddn_dataflow import DDNDataFlowApi


class ArchiveAPI:
    def __int__(self):
        self.housekeeper_api: HousekeeperAPI = None
        self.ddn_api: DDNDataFlowApi = None

    def archive_sample(self, sample_id: str) -> None:
        files_to_archive: List[Path] = self.housekeeper_api.get_file_paths(
            bundle=sample_id, tags=[SequencingFileTag.SPRING]
        )
        task_id: int = self.ddn_api.archive_folders(
            {file: Path(sample_id) for file in files_to_archive}
        )
        self.housekeeper_api.update_file_task_id(files_to_archive, task_id)

    def retrieve_sample(self) -> None:
        pass

        # TODO how to not instantly remove retrieved SPRING FILES
