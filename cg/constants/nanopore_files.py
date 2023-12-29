from enum import StrEnum
from pathlib import Path


class NanoporeDirsAndFiles(StrEnum):
    data_directory: str = "nanopore"
    sequencing_summary_pattern: str = r"final_summary_*.txt"
    systemd_trigger_directory: str = "new_transferred_data"

    @classmethod
    def sequencing_summary_file(cls, flow_cell_directory: Path) -> Path | None:
        try:
            file = Path(next(flow_cell_directory.glob(cls.sequencing_summary_pattern.value)))
        except StopIteration:
            file = None
        return file

    @classmethod
    def sequencing_complete(cls, flow_cell_directory: Path) -> bool:
        return bool(cls.sequencing_summary_file(flow_cell_directory))
