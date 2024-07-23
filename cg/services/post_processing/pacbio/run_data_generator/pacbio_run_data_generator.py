from cg.services.post_processing.abstract_classes import RunDataGenerator
from cg.services.post_processing.pacbio.run_data_generator.run_data import PacbioRunData


class PacbioRunDataGenerator(RunDataGenerator):

    def _validate_run_path(self) -> None:
        pass

    def get_run_data(self) -> PacbioRunData:
        pass
