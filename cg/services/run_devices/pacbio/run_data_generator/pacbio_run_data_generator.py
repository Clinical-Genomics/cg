from pathlib import Path

from cg.services.run_devices.abstract_classes import RunDataGenerator
from cg.services.run_devices.error_handler import handle_post_processing_errors
from cg.services.run_devices.exc import PostProcessingRunDataGeneratorError
from cg.services.run_devices.pacbio.run_data_generator.run_data import PacBioRunData
from cg.services.run_devices.validators import validate_has_expected_parts, validate_name_pre_fix


class PacBioRunDataGenerator(RunDataGenerator):

    @staticmethod
    def _validate_run_name(run_name) -> None:
        validate_name_pre_fix(run_name, pre_fix="r")
        validate_has_expected_parts(run_name=run_name, expected_parts=2)

    @handle_post_processing_errors(
        to_except=(ValueError,), to_raise=PostProcessingRunDataGeneratorError
    )
    def get_run_data(self, smrt_cell_full_name: str, sequencing_dir: str) -> PacBioRunData:
        """
        Get the run data for a PacBio SMRT cell run.
        internal_id should include the PacBio run including plate well, e.g. 'r84202_20240522_133539/1_A01'
        """
        self._validate_run_name(smrt_cell_full_name)
        full_path = Path(sequencing_dir, smrt_cell_full_name)

        return PacBioRunData(
            full_path=full_path,
            sequencing_run_name=self._get_sequencing_run_internal_id(smrt_cell_full_name),
            well_name=self._get_well(smrt_cell_full_name),
            plate=self._get_plate(smrt_cell_full_name),
        )

    @staticmethod
    def _get_sequencing_run_internal_id(
        run_name: str,
    ) -> str:  # TODO: Rename input to something more meaningful
        return run_name.split("/")[0]

    @staticmethod
    def _get_plate_well(run_name: str) -> str:
        return run_name.split("/")[1]

    def _get_plate(self, run_name: str) -> str:
        plate_well: str = self._get_plate_well(run_name)
        return plate_well.split("_")[0]

    def _get_well(self, run_name: str) -> str:
        plate_well: str = self._get_plate_well(run_name)
        return plate_well.split("_")[-1]
