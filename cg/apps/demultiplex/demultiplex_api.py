"""This api should handle everything around demultiplexing"""
import logging
from pathlib import Path
from typing import Iterable

from cg.apps.demultiplex.sbatch import DEMULTIPLEX_COMMAND, DEMULTIPLEX_ERROR
from cg.apps.slurm.slurm_api import SlurmAPI
from cg.models.demultiplex.sbatch import SbatchCommand, SbatchError
from cg.models.slurm.sbatch import Sbatch

LOG = logging.getLogger(__name__)

"""
We loop over all flowcell directories and check if sequencing and transfering is done. This is indicated by the two
files RTAComplete.txt and CopyComplete.txt.
We also create file (demuxcomplete.txt) that indicates if is finished.

### THIS IS THE PART I DON'T UNDERSTAND ATM
I think that the file delivery.txt indicates that demultiplexing has started.


Then check if there is a SampleSheet.csv file, if not this is created by fetching raw information from LIMS and then
convert it to a format that bcl2fastq accepts.

When that file exists we start demultiplexing by sending a batch job with instructions to slurm.

Before starting demux we will need to create a basemask.

for RUN_DIR in ${IN_DIR}/*; do
    if [[ ! -d ${RUN_DIR} ]]; then # -d means directory exists
        continue
    fi

    RUN=$(basename ${RUN_DIR})
    FC=${RUN##*_}
    FC=${FC:1}
    PROJECTLOG=${DEMUXES_DIR}/${RUN}/projectlog.$(date +'%Y%m%d%H%M%S').log

    if [[ -f ${RUN_DIR}/RTAComplete.txt && -f ${RUN_DIR}/CopyComplete.txt ]]; then
        if [[ ! -f ${RUN_DIR}/demuxstarted.txt ]]; then

            # start with a clean slate: remove empty sample sheets before continuing
            if [[ -e ${RUN_DIR}/SampleSheet.csv && ! -s ${RUN_DIR}/SampleSheet.csv  ]]; then
                rm ${RUN_DIR}/SampleSheet.csv
            fi

            if [[ ! -e ${RUN_DIR}/SampleSheet.csv ]]; then
                log "demux sheet fetch --application nova --pad --longest ${FC} > ${RUN_DIR}/SampleSheet.csv"
                demux sheet fetch --application nova --pad --longest ${FC} > ${RUN_DIR}/SampleSheet.csv
            fi

            # exit if samplesheet is still empty after running demux sheet fetch
            if [[ -e ${RUN_DIR}/SampleSheet.csv && ! -s ${RUN_DIR}/SampleSheet.csv ]]; then
                echo "Sample sheet empty! Exiting!" 1>&2
                continue
            fi

            log "mkdir -p ${DEMUXES_DIR}/${RUN}/"
            mkdir -p ${DEMUXES_DIR}/${RUN}/

            log "date +'%Y%m%d%H%M%S' > ${RUN_DIR}/demuxstarted.txt"
            date +'%Y%m%d%H%M%S' > ${RUN_DIR}/demuxstarted.txt

            log "bash ${SCRIPT_DIR}/demux-novaseq.bash ${RUN_DIR} ${DEMUXES_DIR} &>> ${PROJECTLOG}"
            bash ${SCRIPT_DIR}/demux-novaseq.bash ${RUN_DIR} ${DEMUXES_DIR} ${FC} ${PROJECTLOG} &>> ${PROJECTLOG}

            if [[ $? == 0 ]]; then
                # indicate demultiplexing is finished
                log "date +'%Y%m%d%H%M%S' > ${DEMUXES_DIR}/${RUN}/demuxcomplete.txt"
                date +'%Y%m%d%H%M%S' > ${DEMUXES_DIR}/${RUN}/demuxcomplete.txt
                # create trigger file for delivery script
                log "date +'%Y%m%d%H%M%S' > ${DEMUXES_DIR}/${RUN}/copycomplete.txt"
                date +'%Y%m%d%H%M%S' > ${DEMUXES_DIR}/${RUN}/copycomplete.txt
                # remove delivery.txt (if present) to trigger delivery
                log "date +'%Y%m%d%H%M%S' remove delivery.txt"
                rm -f date ${DEMUXES_DIR}/${RUN}/delivery.txt
            fi

            # This is an easy way to avoid running multiple demuxes at the same time
            break
        else
            log "${RUN} is finished and demultiplexing has already started"
        fi
    else
        log "${RUN} is not finished yet"
    fi
done
"""


def is_sequencing_done(in_path: Path) -> bool:
    """Check if sequencing is done

    This is indicated by that the file RTAComplete.txt exists
    """
    return Path(in_path, "RTAComplete.txt").exists()


def is_copy_completed(in_path: Path) -> bool:
    """Check if copy of flowcell is done

    This is indicated by that the file CopyComplete.txt exists
    """
    return Path(in_path, "CopyComplete.txt").exists()


def is_demultiplexing_ongoing(in_path: Path) -> bool:
    """Check if demultiplexing is ongoing

    This is indicated by if the file demuxstarted.txt exists (?)
    """
    return Path(in_path, "demuxstarted.txt").exists()


def sample_sheet_exists(in_path: Path) -> bool:
    """Check if sample sheet exists"""
    return Path(in_path, "SampleSheet.csv").exists()


def is_flowcell_ready(in_path: Path) -> bool:
    """Check if a flowcell is ready for demultiplexing

    A flowcell is ready if the two files RTAComplete.txt and CopyComplete.txt exists in the flowcell directory
    """
    if not is_sequencing_done(in_path):
        LOG.info("Sequencing is not completed for run %s", in_path.name)
        return False

    if not is_copy_completed(in_path):
        LOG.info("Copy of sequence data is not ready for flowcell %s", in_path.name)
        return False

    LOG.info("Flowcell %s is ready for demultiplexing", in_path.name)
    return True


def fetch_flowcell_paths(in_path: Path) -> Iterable[Path]:
    """Loop over a directory and find all flowcell files

    It is assumed that the flowcell directories are situated as children to in_path
    """
    for child in in_path.iterdir():
        if not child.is_dir():
            continue
        LOG.info("Found directory %s", child)
        yield child


def fetch_logfile_path(flowcell: Path, out_dir: Path, basemask: Path) -> Path:
    """Create the path to the logfile"""
    return out_dir / "_".join(["Unaligned", basemask.name]) / f"project.{flowcell.name}.log"


class DemultiplexingAPI:
    """Demultiplexing API should deal with anything related to demultiplexing

    This includes starting demultiplexing, creating sample sheets, creating base masks
    """

    DEMUX_MAIL = "clinical-demux@scilifelab.se"

    def __init__(self, config: dict):
        self.slurm_api = SlurmAPI()
        self.slurm_account = config["demultiplex"]["slurm"]["account"]
        self.dry_run = False

    @staticmethod
    def get_sbatch_error(flowcell: Path, log_path: Path, email: str) -> str:
        """Create the sbatch error string"""
        error_parameters: SbatchError = SbatchError(
            flowcell_name=flowcell.name, email=email, logfile=log_path.as_posix()
        )
        return DEMULTIPLEX_ERROR.format(**error_parameters.dict())

    @staticmethod
    def get_sbatch_command(run_dir: Path, out_dir: Path, basemask: Path, sample_sheet: Path) -> str:
        command_parameters: SbatchCommand = SbatchCommand(
            run_dir=run_dir.as_posix(),
            out_dir=out_dir.as_posix(),
            basemask=basemask.as_posix(),
            sample_sheet=sample_sheet.as_posix(),
        )
        return DEMULTIPLEX_COMMAND(**command_parameters.dict())

    @staticmethod
    def get_demultiplex_sbatch_path(directory: Path) -> Path:
        """Get the path to where sbatch file should be kept"""
        return directory / "demux-novaseq.sh"

    def start_demultiplexing(
        self, flowcell: Path, out_dir: Path, basemask: Path, sample_sheet: Path
    ):
        """Start demultiplexing for a flowcell"""
        log_path: Path = fetch_logfile_path(flowcell=flowcell, out_dir=out_dir, basemask=basemask)
        error_function: str = self.get_sbatch_error(
            flowcell=flowcell, log_path=log_path, email=self.DEMUX_MAIL
        )
        commands: str = self.get_sbatch_command(
            run_dir=flowcell, out_dir=out_dir, basemask=basemask, sample_sheet=sample_sheet
        )

        sbatch_info = {
            "job_name": "_".join([flowcell.name, "demultiplex"]),
            "account": self.slurm_account,
            "number_tasks": 18,
            "memory": 50,
            "log_dir": log_path.parent.as_posix(),
            "email": self.DEMUX_MAIL,
            "hours": 36,
            "commands": commands,
            "error": error_function,
        }
        sbatch_content: str = self.slurm_api.generate_sbatch_content(Sbatch.parse_obj(sbatch_info))
        sbatch_path: Path = self.get_demultiplex_sbatch_path(directory=out_dir)
        sbatch_number: int = self.slurm_api.submit_sbatch(
            sbatch_content=sbatch_content, sbatch_path=sbatch_path
        )
        LOG.info("Fastq compression running as job %s", sbatch_number)
        return sbatch_number


if __name__ == "__main__":
    cg_dir = Path("/Users/mans.magnusson/PycharmProjects/cg/cg/")
    for flowcell_directory in fetch_flowcell_paths(cg_dir):
        run_name = flowcell_directory.name
        print(type(flowcell_directory), flowcell_directory, run_name)
