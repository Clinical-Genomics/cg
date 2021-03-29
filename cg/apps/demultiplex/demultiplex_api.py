"""This api should handle everything around demultiplexing"""
import logging
from pathlib import Path
from typing import Iterable, Optional

from cg.apps.demultiplex.flowcell import Flowcell
from cg.apps.demultiplex.sbatch import DEMULTIPLEX_COMMAND, DEMULTIPLEX_ERROR
from cg.apps.slurm.slurm_api import SlurmAPI
from cg.models.demultiplex.sbatch import SbatchCommand, SbatchError
from cg.models.slurm.sbatch import Sbatch

LOG = logging.getLogger(__name__)


def fetch_flowcell_paths(in_path: Path) -> Iterable[Path]:
    """Loop over a directory and find all flowcell files

    It is assumed that the flowcell directories are situated as children to in_path
    """
    for child in in_path.iterdir():
        if not child.is_dir():
            continue
        LOG.info("Found directory %s", child)
        yield child


class DemultiplexingAPI:
    """Demultiplexing API should deal with anything related to demultiplexing

    This includes starting demultiplexing, creating sample sheets, creating base masks
    """

    def __init__(self, config: dict, out_dir: Optional[Path] = None):
        self.slurm_api = SlurmAPI()
        self.slurm_account: str = config["demultiplex"]["slurm"]["account"]
        self.mail: str = config["demultiplex"]["slurm"]["mail_user"]
        self.out_dir: Path = out_dir or Path(config["demultiplex"]["out_dir"])
        self.dry_run: bool = False

    def set_dry_run(self, dry_run: bool) -> None:
        LOG.info("Set dry run to %s", dry_run)
        self.dry_run = dry_run
        self.slurm_api.set_dry_run(dry_run=dry_run)

    @staticmethod
    def get_sbatch_error(flowcell_id: str, log_path: Path, email: str) -> str:
        """Create the sbatch error string"""
        error_parameters: SbatchError = SbatchError(
            flowcell_name=flowcell_id, email=email, logfile=log_path.as_posix()
        )
        return DEMULTIPLEX_ERROR.format(**error_parameters.dict())

    @staticmethod
    def get_sbatch_command(run_dir: Path, out_dir: Path, sample_sheet: Path) -> str:
        command_parameters: SbatchCommand = SbatchCommand(
            run_dir=run_dir.as_posix(),
            out_dir=out_dir.as_posix(),
            sample_sheet=sample_sheet.as_posix(),
        )
        return DEMULTIPLEX_COMMAND.format(**command_parameters.dict())

    @staticmethod
    def get_demultiplex_sbatch_path(directory: Path) -> Path:
        """Get the path to where sbatch file should be kept"""
        return directory / "demux-novaseq.sh"

    @staticmethod
    def get_logfile(out_dir: Path, flowcell: Flowcell) -> Path:
        """Create the path to the logfile"""
        # How to handle if a flowcell is redemuxed ?
        return out_dir / f"project.{flowcell.flowcell_id}.log"

    def start_demultiplexing(self, flowcell: Flowcell):
        """Start demultiplexing for a flowcell"""
        flowcell_out_dir: Path = self.out_dir / flowcell.path.name
        LOG.info("Demultiplexing to %s", flowcell_out_dir)
        if not self.dry_run:
            LOG.info("Creating out dir %s", flowcell_out_dir)
            flowcell_out_dir.mkdir(exist_ok=False, parents=True)
        log_path: Path = self.get_logfile(out_dir=flowcell_out_dir, flowcell=flowcell)
        error_function: str = self.get_sbatch_error(
            flowcell_id=flowcell.flowcell_id, log_path=log_path, email=self.mail
        )
        commands: str = self.get_sbatch_command(
            run_dir=flowcell.path, out_dir=flowcell_out_dir, sample_sheet=flowcell.sample_sheet_path
        )

        sbatch_info = {
            "job_name": "_".join([flowcell.flowcell_id, "demultiplex"]),
            "account": self.slurm_account,
            "number_tasks": 18,
            "memory": 50,
            "log_dir": log_path.parent.as_posix(),
            "email": self.mail,
            "hours": 36,
            "commands": commands,
            "error": error_function,
        }
        sbatch_content: str = self.slurm_api.generate_sbatch_content(Sbatch.parse_obj(sbatch_info))
        sbatch_path: Path = self.get_demultiplex_sbatch_path(directory=flowcell_out_dir)
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
