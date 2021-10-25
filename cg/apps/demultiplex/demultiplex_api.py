"""This api should handle everything around demultiplexing"""
import logging
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from typing_extensions import Literal

from cg.apps.demultiplex.sbatch import DEMULTIPLEX_COMMAND, DEMULTIPLEX_ERROR
from cg.apps.slurm.slurm_api import SlurmAPI
from cg.apps.tb import TrailblazerAPI
from cg.constants.priority import SlurmQos
from cg.models.demultiplex.flowcell import Flowcell
from cg.models.demultiplex.sbatch import SbatchCommand, SbatchError
from cg.models.slurm.sbatch import Sbatch, SbatchDragen
from cgmodels.cg.constants import Pipeline

LOG = logging.getLogger(__name__)


class DemultiplexingAPI:
    """Demultiplexing API should deal with anything related to demultiplexing

    This includes starting demultiplexing, creating sample sheets, creating base masks
    """

    def __init__(self, config: dict, out_dir: Optional[Path] = None):
        self.slurm_api = SlurmAPI()
        self.slurm_account: str = config["demultiplex"]["slurm"]["account"]
        self.mail: str = config["demultiplex"]["slurm"]["mail_user"]
        self.run_dir: Path = Path(config["demultiplex"]["run_dir"])
        self.out_dir: Path = out_dir or Path(config["demultiplex"]["out_dir"])
        self.environment: str = config.get("environment", "stage")
        LOG.info("Set environment to %s", self.environment)
        self.dry_run: bool = False

    @property
    def priority(self) -> Literal[SlurmQos.HIGH, SlurmQos.LOW]:
        if self.environment == "stage":
            return SlurmQos.LOW
        return SlurmQos.HIGH

    def set_dry_run(self, dry_run: bool) -> None:
        LOG.debug("Set dry run to %s", dry_run)
        self.dry_run = dry_run
        self.slurm_api.set_dry_run(dry_run=dry_run)

    @staticmethod
    def get_sbatch_error(
        flowcell: Flowcell,
        email: str,
        demux_dir: Path,
    ) -> str:
        """Create the sbatch error string"""
        LOG.info("Creating the sbatch error string")
        error_parameters: SbatchError = SbatchError(
            flowcell_name=flowcell.flowcell_id,
            email=email,
            logfile=DemultiplexingAPI.get_stderr_logfile(flowcell=flowcell).as_posix(),
            demux_dir=demux_dir.as_posix(),
            demux_started=flowcell.demultiplexing_started_path.as_posix(),
        )
        return DEMULTIPLEX_ERROR.format(**error_parameters.dict())

    @staticmethod
    def get_sbatch_command(
        run_dir: Path,
        unaligned_dir: Path,
        sample_sheet: Path,
        demux_completed: Path,
        flowcell: Flowcell,
        environment: Literal["production", "stage"] = "stage",
    ) -> str:
        LOG.info("Creating the sbatch command string")
        command_parameters: SbatchCommand = SbatchCommand(
            run_dir=run_dir.as_posix(),
            demux_dir=unaligned_dir.parent.as_posix(),
            unaligned_dir=unaligned_dir.as_posix(),
            sample_sheet=sample_sheet.as_posix(),
            demux_completed_file=demux_completed.as_posix(),
            environment=environment,
        )
        return DEMULTIPLEX_COMMAND[flowcell.bcl_converter].format(**command_parameters.dict())

    @staticmethod
    def demultiplex_sbatch_path(flowcell: Flowcell) -> Path:
        """Get the path to where sbatch file should be kept"""
        return flowcell.path / "demux-novaseq.sh"

    @staticmethod
    def get_run_name(flowcell: Flowcell) -> str:
        """Create the run name for the sbatch job"""
        return f"{flowcell.flowcell_id}_demultiplex"

    @staticmethod
    def get_stderr_logfile(flowcell: Flowcell) -> Path:
        """Create the path to the logfile"""
        return flowcell.path / f"{DemultiplexingAPI.get_run_name(flowcell)}.stderr"

    @staticmethod
    def get_stdout_logfile(flowcell: Flowcell) -> Path:
        """Create the path to the logfile"""
        return flowcell.path / f"{DemultiplexingAPI.get_run_name(flowcell)}.stdout"

    def flowcell_out_dir_path(self, flowcell: Flowcell) -> Path:
        """Create the path to where the demuliplexed result should be produced"""
        return self.out_dir / flowcell.path.name

    def unaligned_dir_path(self, flowcell: Flowcell) -> Path:
        """Create the path to where the demuliplexed result should be produced"""
        return self.flowcell_out_dir_path(flowcell) / "Unaligned"

    def demultiplexing_completed_path(self, flowcell: Flowcell) -> Path:
        """Create the path to where the demuliplexed result should be produced"""
        return self.flowcell_out_dir_path(flowcell) / "demuxcomplete.txt"

    def is_demultiplexing_completed(self, flowcell: Flowcell) -> bool:
        """Create the path to where the demuliplexed result should be produced"""
        LOG.info("Check if demultiplexing is ready for %s", flowcell.path)
        logfile: Path = self.get_stderr_logfile(flowcell)
        if not logfile.exists():
            LOG.warning("Could not find logfile!")
            return False
        return self.demultiplexing_completed_path(flowcell).exists()

    def is_demultiplexing_ongoing(self, flowcell: Flowcell) -> bool:
        """Check if demultiplexing is ongoing

        This is indicated by if the file demuxstarted.txt exists in the flowcell directory
        AND
        that the demultiplexing completed file does not exist
        """
        LOG.debug("Check if demultiplexing is ongoing for %s", flowcell.flowcell_id)
        if not flowcell.demultiplexing_started_path.exists():
            LOG.debug("Demultiplexing has not been started")
            return False
        LOG.debug("Demultiplexing has been started!")
        if self.is_demultiplexing_completed(flowcell):
            LOG.debug("Demultiplexing is already completed for flowcell %s", flowcell.flowcell_id)
            return False
        LOG.debug("Demultiplexing is not finished!")
        return True

    def is_demultiplexing_possible(self, flowcell: Flowcell) -> bool:
        """Check if it is possible to start demultiplexing

        This means that
            - flowcell should be ready for demultiplexing (all files in place)
            - sample sheet needs to exist
            - demultiplexing should not be running
        """
        LOG.info("Check if demultiplexing is possible for %s", flowcell.flowcell_id)
        demultiplexing_possible = True
        if not flowcell.is_flowcell_ready():
            demultiplexing_possible = False

        if not flowcell.sample_sheet_exists():
            LOG.warning("Could not find sample sheet for %s", flowcell.flowcell_id)
            demultiplexing_possible = False

        if flowcell.is_demultiplexing_started():
            LOG.warning("Demultiplexing has already been started")
            demultiplexing_possible = False

        if self.flowcell_out_dir_path(flowcell=flowcell).exists():
            LOG.warning("Flowcell out dir exists")
            demultiplexing_possible = False

        if self.is_demultiplexing_completed(flowcell):
            LOG.warning("Demultiplexing is already completed for flowcell %s", flowcell.flowcell_id)
            demultiplexing_possible = False
        return demultiplexing_possible

    def create_demultiplexing_started_file(self, demultiplexing_started_path: Path) -> None:
        LOG.info("Creating demultiplexing started file")
        if self.dry_run:
            return
        demultiplexing_started_path.touch(exist_ok=False)

    @staticmethod
    def get_trailblazer_config(slurm_job_id: int) -> Dict[str, List[str]]:
        return {"jobs": [str(slurm_job_id)]}

    @staticmethod
    def write_trailblazer_config(content: dict, file_path: Path) -> None:
        """Write the content to a yaml file"""
        LOG.info("Writing yaml content %s to %s", content, file_path)
        with file_path.open("w") as yaml_file:
            yaml.safe_dump(content, yaml_file, indent=4, explicit_start=True)

    def add_to_trailblazer(self, tb_api: TrailblazerAPI, slurm_job_id: int, flowcell: Flowcell):
        """Add demultiplexing entry to trailblazer"""
        if self.dry_run:
            return
        self.write_trailblazer_config(
            content=self.get_trailblazer_config(slurm_job_id=slurm_job_id),
            file_path=flowcell.trailblazer_config_path,
        )
        tb_api.add_pending_analysis(
            case_id=flowcell.flowcell_id,
            analysis_type="other",
            config_path=flowcell.trailblazer_config_path.as_posix(),
            out_dir=flowcell.trailblazer_config_path.parent.as_posix(),
            priority=self.priority,
            email=self.mail,
            data_analysis=str(Pipeline.DEMULTIPLEX),
        )

    def start_demultiplexing(self, flowcell: Flowcell):
        """Start demultiplexing for a flowcell"""
        self.create_demultiplexing_started_file(flowcell.demultiplexing_started_path)
        demux_dir: Path = self.flowcell_out_dir_path(flowcell=flowcell)
        unaligned_dir: Path = self.unaligned_dir_path(flowcell=flowcell)
        LOG.info("Demultiplexing to %s", unaligned_dir)
        if not self.dry_run:
            LOG.info("Creating demux dir %s", unaligned_dir)
            unaligned_dir.mkdir(exist_ok=False, parents=True)

        log_path: Path = self.get_stderr_logfile(flowcell=flowcell)
        error_function: str = self.get_sbatch_error(
            flowcell=flowcell, email=self.mail, demux_dir=demux_dir
        )
        commands: str = self.get_sbatch_command(
            run_dir=flowcell.path,
            unaligned_dir=unaligned_dir,
            sample_sheet=flowcell.sample_sheet_path,
            demux_completed=self.demultiplexing_completed_path(flowcell=flowcell),
            flowcell=flowcell,
            environment=self.environment,
        )

        if flowcell.bcl_converter == "bcl2fastq":
            sbatch_parameters = Sbatch(
                account=self.slurm_account,
                commands=commands,
                email=self.mail,
                error=error_function,
                hours=36,
                job_name=self.get_run_name(flowcell),
                log_dir=log_path.parent.as_posix(),
                memory=125,
                number_tasks=18,
                priority=self.priority,
            )
        if flowcell.bcl_converter == "dragen":
            sbatch_parameters = SbatchDragen(
                account=self.slurm_account,
                commands=commands,
                email=self.mail,
                error=error_function,
                hours=36,
                job_name=self.get_run_name(flowcell),
                log_dir=log_path.parent.as_posix(),
                priority=self.priority,
            )

        sbatch_content: str = self.slurm_api.generate_sbatch_content(
            sbatch_parameters=sbatch_parameters
        )
        sbatch_path: Path = self.demultiplex_sbatch_path(flowcell=flowcell)
        sbatch_number: int = self.slurm_api.submit_sbatch(
            sbatch_content=sbatch_content, sbatch_path=sbatch_path
        )
        LOG.info("Demultiplexing running as job %s", sbatch_number)
        return sbatch_number
