from pathlib import Path

from cg.io.csv import write_csv


class NalloSampleSheetCreator:
    def create(self, case_id: str, file_path: Path) -> None:
        write_csv(content="", file_path=file_path)
