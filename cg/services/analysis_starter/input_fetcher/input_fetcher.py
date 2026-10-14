from abc import ABC, abstractmethod


class AnalysisInputValidator(ABC):

    @abstractmethod
    def ensure_files_are_ready(self, case_id: str):
        pass
