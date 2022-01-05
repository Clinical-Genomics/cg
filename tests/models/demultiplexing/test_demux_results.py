from pathlib import Path

from cg.models.demultiplex.demux_results import DemuxResults, LogfileParameters
from cg.models.demultiplex.flowcell import Flowcell


def test_demux_results_instance(demultiplexed_flowcell: Path, flowcell_object: Flowcell):
    # GIVEN the path to a demultiplexed flowcell and a flowcell object

    # WHEN instantiating a demux results object
    demux_results = DemuxResults(
        demux_dir=demultiplexed_flowcell, flowcell=flowcell_object, bcl_converter="bcl2fastq"
    )

    # THEN assert that the results dir is the unaligned dir
    assert demux_results.results_dir == demultiplexed_flowcell / "Unaligned"
    # THEN assert that the results dir exists
    assert demux_results.results_dir.exists()


def test_parse_log(bcl2fastq_demux_results: DemuxResults):
    # GIVEN som demux results

    # WHEN parsed log file parameters
    log_file_parameters: LogfileParameters = bcl2fastq_demux_results.get_logfile_parameters()

    # THEN assert that it was bcl2fastq that was run
    assert log_file_parameters.id_string == "bcl2fastq v2.20.0.422"
