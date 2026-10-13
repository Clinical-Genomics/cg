from abc import ABC, abstractmethod


class InputValidator(ABC):

    @abstractmethod
    def ensure_files_are_ready(self, case_id: str):
        pass
