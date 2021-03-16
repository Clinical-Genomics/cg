import logging
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree

LOG = logging.getLogger(__name__)


class RunParameters:
    """Class to handle the run parameters from a sequencing run"""

    def __init__(self, run_parameters: Path, application_type: str = "nova_seek"):
        self.run_parameters: Path = run_parameters
        self.application_type: str = application_type
        with open(run_parameters, "rt") as in_file:
            self.tree: ElementTree = ElementTree.parse(in_file)

    def get_node_integer_value(self, node_name: str) -> int:
        xml_node = self.tree.find(node_name)
        return int(xml_node.text)

    def index_read_one(self) -> int:
        """Get the value for index read one"""
        node_name = "./IndexRead1NumberOfCycles"
        return self.get_node_integer_value(node_name)

    def index_read_two(self) -> int:
        """Get the value for index read one"""
        node_name = "./IndexRead2NumberOfCycles"
        return self.get_node_integer_value(node_name)

    def read_one_nr_cycles(self) -> int:
        """Get the nr of cycles for read one"""
        node_name = "./Read1NumberOfCycles"
        return self.get_node_integer_value(node_name)

    def read_two_nr_cycles(self) -> int:
        """Get the nr of cycles for read one"""
        node_name = "./Read2NumberOfCycles"
        return self.get_node_integer_value(node_name)

    def base_mask(self) -> str:
        """create the bcl2fastq basemask for novaseq flowcells

        Basemask is used in this comma format as an argument to bcl2fastq.
        When creating the unaligned path the commas are stripped
        """
        return (
            f"Y{self.read_one_nr_cycles()},"
            f"I{self.index_read_one()},"
            f"I{self.read_two_nr_cycles()},"
            f"Y{self.index_read_two()}"
        )


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
        return RunParameters(run_parameters=self.run_parameters_path)

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
