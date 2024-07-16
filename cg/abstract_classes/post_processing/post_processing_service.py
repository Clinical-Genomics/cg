"""Abstract class for the post processing services."""

from abc import abstractmethod, ABC


class PostProcessingService(ABC):
    @abstractmethod
    def post_process(self, run_name: str):
        pass
