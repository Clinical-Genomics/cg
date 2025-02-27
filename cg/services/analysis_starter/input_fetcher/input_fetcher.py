from abc import ABC


class InputFetcher(ABC):
    def ensure_files_are_ready(self, case_id: str):
        pass
