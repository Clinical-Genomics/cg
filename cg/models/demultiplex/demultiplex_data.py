import logging
from pathlib import Path

from cg.models.demultiplex.run_parameters import RunParameters

LOG = logging.getLogger(__name__)


class DemultiplexData:
    """Holds information about demultiplexing based on a flowcell path"""

    def __init__(self, run: Path):
        self.run: Path = run

    @property
    def run_parameters_object(self) -> RunParameters:
        if not self.run_parameters_path.exists():
            raise FileNotFoundError(
                "Could not find run parameters file %s".format(self.run_parameters_path)
            )
        return RunParameters(run_parameters_path=self.run_parameters_path)

    @property
    def run_parameters_path(self) -> Path:
        return self.run / "runParameters.xml"

    @property
    def run_name(self) -> str:
        return self.run.name

    @property
    def sample_sheet_path(self) -> Path:
        """Return a string with the run name"""
        return self.run / "SampleSheet.csv"

    def base_mask(self) -> str:
        return self.run_parameters_object.base_mask()


if __name__ == "__main__":
    run_path = Path(
        "/Users/mans.magnusson/PycharmProjects/cg/tests/fixtures/DEMUX/160219_D00410_0217_AHJKMYBCXX"
    )

    demux_object = DemultiplexData(run_path)
    print(demux_object.base_mask())
    print(demux_object.run_name)
