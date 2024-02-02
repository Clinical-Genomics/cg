from abc import ABC, abstractmethod


class SlurmService(ABC):
    @abstractmethod
    def submit_job(self, job):
        pass
