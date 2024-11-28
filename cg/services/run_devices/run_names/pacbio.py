from pathlib import Path

from cg.services.run_devices.run_names.service import RunNamesService


class PacbioRunNamesService(RunNamesService):

    def get_run_names(self) -> list[str]:
        """
        Get all the run names from the PacBio sequencing directory in the form
        <sequencing_run>/<SMRTcell>, for example:
            r84202_20240913_121403/1_C01
        """

        run_names = []
        for run_folder in Path(self.run_directory).iterdir():
            if run_folder.is_dir():
                for cell_folder in run_folder.iterdir():
                    run_names.append(f"{run_folder.name}/{cell_folder.name}")
        return run_names
