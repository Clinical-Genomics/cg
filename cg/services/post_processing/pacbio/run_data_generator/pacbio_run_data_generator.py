from pathlib import Path
from cg.services.post_processing.abstract_classes import RunDataGenerator
from cg.services.post_processing.pacbio.run_data_generator.run_data import PacBioRunData
from cg.services.post_processing.validators import (
    validate_name_pre_fix,
    validate_has_expected_parts,
)
from cg.utils.string import get_element_from_split


class PacBioRunDataGenerator(RunDataGenerator):

    def _validate_run_name(self, run_name) -> None:
        validate_name_pre_fix(run_name)
        validate_has_expected_parts(run_name=run_name, expected_parts=2)

    def get_run_data(self, run_name: str, sequencing_dir: str) -> PacBioRunData:
        """
        Get the run data for a PacBio SMRT cell run.
        run_name should include the PacBio run including plate well, e.g. 'r84202_20240522_133539/1_A01'
        """
        self._validate_run_name(run_name)
        full_path = Path(sequencing_dir, run_name)

        return PacBioRunData(
            full_path=full_path,
            sequencing_run_name=self._get_sequencing_run_name(run_name),
            well_name=self._get_well(run_name),
            plate=self._get_plate(run_name),
        )

    @staticmethod
    def _get_sequencing_run_name(run_name: str) -> str:
        return get_element_from_split(value=run_name, element_position=0, split="/")

    @staticmethod
    def _get_plate_well(run_name: str) -> str:
        return get_element_from_split(value=run_name, element_position=-1, split="/")

    def _get_plate(self, run_name: str) -> str:
        plate_well: str = self._get_plate_well(run_name)
        return get_element_from_split(value=plate_well, element_position=0, split="_")

    def _get_well(self, run_name: str) -> str:
        plate_well: str = self._get_plate_well(run_name)
        return get_element_from_split(value=plate_well, element_position=-1, split="_")