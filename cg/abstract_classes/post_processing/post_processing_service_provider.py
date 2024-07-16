"""Abstract class for a post-processing service provider."""

from abc import abstractmethod, ABC


class PostProcessingServiceProvider(ABC):

    @abstractmethod
    def create_post_processing_service(self):
        pass
