"""This API should handle everything around demultiplexing."""

import logging
import shutil
from pathlib import Path

from typing_extensions import Literal

from cg.apps.demultiplex.sbatch import DEMULTIPLEX_COMMAND, DEMULTIPLEX_ERROR
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.slurm.slurm_api import SlurmAPI
from cg.apps.tb import TrailblazerAPI
from cg.constants.constants import FileFormat, Workflow
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.constants.priority import SlurmQos, TrailblazerPriority
from cg.constants.tb import AnalysisType
from cg.exc import HousekeeperFileMissingError
from cg.io.controller import WriteFile
from cg.models.demultiplex.sbatch import SbatchCommand, SbatchError
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData
from cg.models.slurm.sbatch import SbatchDragen

LOG = logging.getLogger(__name__)


class DemultiplexingAPI:
    """Demultiplexing API should deal with anything related to demultiplexing.

    This includes starting demultiplexing, creating sample sheets, creating base masks,
    """

    def __init__(self, config: dict, housekeeper_api: HousekeeperAPI, out_dir: Path | None = None):
        self.slurm_api = SlurmAPI()
        self.hk_api = housekeeper_api
        self.slurm_account: str = config["demultiplex"]["slurm"]["account"]
        self.mail: str = config["demultiplex"]["slurm"]["mail_user"]
        self.sequencing_runs_dir: Path = Path(
            config["run_instruments"]["illumina"]["sequencing_runs_dir"]
        )
        self.demultiplexed_runs_dir: Path = out_dir or Path(
            config["run_instruments"]["illumina"]["demultiplexed_runs_dir"]
        )
        self.environment: str = config.get("environment", "stage")
        LOG.info(f"Set environment to {self.environment}")
        self.dry_run: bool = False

    @property
    def slurm_quality_of_service(self) -> Literal[SlurmQos.HIGH, SlurmQos.LOW]:
        """Return SLURM quality of service."""
        return SlurmQos.LOW if self.environment == "stage" else SlurmQos.HIGH

    @property
    def trailblazer_priority(self) -> Literal[TrailblazerPriority.HIGH, TrailblazerPriority.LOW]:
        """Return Trailblazer quality of service."""
        return TrailblazerPriority.LOW if self.environment == "stage" else TrailblazerPriority.HIGH

    def set_dry_run(self, dry_run: bool) -> None:
        """Set dry run."""
        LOG.debug(f"DemultiplexingAPI: Set dry run to {dry_run}")
        self.dry_run = dry_run
        self.slurm_api.set_dry_run(dry_run=dry_run)

    @staticmethod
    def get_sbatch_error(
        sequencing_run: IlluminaRunDirectoryData,
        email: str,
        demux_dir: Path,
    ) -> str:
        """Create the sbatch error string."""
        LOG.debug("Creating the sbatch error string")
        error_parameters: SbatchError = SbatchError(
            flow_cell_id=sequencing_run.id,
            email=email,
            logfile=DemultiplexingAPI.get_stderr_logfile(sequencing_run=sequencing_run).as_posix(),
            demux_dir=demux_dir.as_posix(),
            demux_started=sequencing_run.demultiplexing_started_path.as_posix(),
        )
        return DEMULTIPLEX_ERROR.format(**error_parameters.model_dump())

    @staticmethod
    def get_sbatch_command(
        run_dir: Path,
        demux_dir: Path,
        sample_sheet: Path,
        demux_completed: Path,
        environment: Literal["production", "stage"] = "stage",
    ) -> str:
        """
        Return sbatch command.
        The unaligned_dir is only used for Bcl2Fastq.
        """
        LOG.debug("Creating the sbatch command string")
        unaligned_dir: Path = Path(demux_dir, DemultiplexingDirsAndFiles.UNALIGNED_DIR_NAME)
        command_parameters: SbatchCommand = SbatchCommand(
            run_dir=run_dir.as_posix(),
            demux_dir=demux_dir.as_posix(),
            unaligned_dir=unaligned_dir.as_posix(),
            sample_sheet=sample_sheet.as_posix(),
            demux_completed_file=demux_completed.as_posix(),
            environment=environment,
        )
        return DEMULTIPLEX_COMMAND.format(**command_parameters.model_dump())

    @staticmethod
    def demultiplex_sbatch_path(sequencing_run: IlluminaRunDirectoryData) -> Path:
        """Get the path to where sbatch script file should be kept."""
        return Path(sequencing_run.path, "demux-novaseq.sh")

    @staticmethod
    def get_run_name(sequencing_run: IlluminaRunDirectoryData) -> str:
        """Create the run name for the sbatch job."""
        return f"{sequencing_run.id}_demultiplex"

    @staticmethod
    def get_stderr_logfile(sequencing_run: IlluminaRunDirectoryData) -> Path:
        """Create the path to the stderr logfile."""
        return Path(sequencing_run.path, f"{DemultiplexingAPI.get_run_name(sequencing_run)}.stderr")

    def demultiplexed_run_dir_path(self, sequencing_run: IlluminaRunDirectoryData) -> Path:
        """Create the path to where the demultiplexed result should be produced."""
        return Path(self.demultiplexed_runs_dir, sequencing_run.path.name)

    def is_sample_sheet_in_housekeeper(self, flow_cell_id: str) -> bool:
        """Returns True if the sample sheet for the flow cell exists in Housekeeper."""
        try:
            self.hk_api.get_sample_sheet_path(flow_cell_id)
            return True
        except HousekeeperFileMissingError:
            return False

    def get_sequencing_run_unaligned_dir(self, sequencing_run: IlluminaRunDirectoryData) -> Path:
        """Returns the path to where the demultiplexed result are located."""
        return Path(
            self.demultiplexed_run_dir_path(sequencing_run),
            DemultiplexingDirsAndFiles.UNALIGNED_DIR_NAME,
        )

    def demultiplexing_completed_path(self, sequencing_run: IlluminaRunDirectoryData) -> Path:
        """Return the path to demultiplexing complete file."""
        LOG.info(
            Path(
                self.demultiplexed_run_dir_path(sequencing_run),
                DemultiplexingDirsAndFiles.DEMUX_COMPLETE,
            )
        )
        return Path(
            self.demultiplexed_run_dir_path(sequencing_run),
            DemultiplexingDirsAndFiles.DEMUX_COMPLETE,
        )

    def is_demultiplexing_possible(self, sequencing_run: IlluminaRunDirectoryData) -> bool:
        """Check if it is possible to start demultiplexing.

        This means that
            - sequencing run should be ready for demultiplexing (all files in place)
            - sample sheet needs to exist
            - demultiplexing should not be running
        """
        LOG.info(f"Check if demultiplexing is possible for {sequencing_run.id}")
        demultiplexing_possible = True
        if not sequencing_run.is_sequencing_run_ready():
            demultiplexing_possible = False

        if not sequencing_run.sample_sheet_exists():
            LOG.warning(
                f"Could not find sample sheet in sequencing run directory for {sequencing_run.id}"
            )
            demultiplexing_possible = False

        if not self.is_sample_sheet_in_housekeeper(flow_cell_id=sequencing_run.id):
            LOG.warning(f"Could not find sample sheet in Housekeeper for {sequencing_run.id}")
            demultiplexing_possible = False

        if (
            sequencing_run.has_demultiplexing_started_locally()
            or sequencing_run.has_demultiplexing_started_on_sequencer()
        ):
            LOG.warning("Demultiplexing has already been started")
            demultiplexing_possible = False

        return demultiplexing_possible

    def create_demultiplexing_started_file(self, demultiplexing_started_path: Path) -> None:
        LOG.info("Creating demultiplexing started file")
        if self.dry_run:
            return
        demultiplexing_started_path.touch(exist_ok=False)

    @staticmethod
    def get_trailblazer_config(slurm_job_id: int) -> dict[str, list[str]]:
        return {"jobs": [str(slurm_job_id)]}

    @staticmethod
    def write_trailblazer_config(content: dict, file_path: Path) -> None:
        """Write the content to a yaml file"""
        LOG.info(f"Writing yaml content {content} to {file_path}")
        WriteFile.write_file_from_content(
            content=content, file_format=FileFormat.YAML, file_path=file_path
        )

    def add_to_trailblazer(
        self, tb_api: TrailblazerAPI, slurm_job_id: int, sequencing_run: IlluminaRunDirectoryData
    ):
        """Add demultiplexing entry to trailblazer."""
        if self.dry_run:
            return
        self.write_trailblazer_config(
            content=self.get_trailblazer_config(slurm_job_id=slurm_job_id),
            file_path=sequencing_run.trailblazer_config_path,
        )
        tb_api.add_pending_analysis(
            case_id=sequencing_run.id,
            analysis_type=AnalysisType.OTHER,
            config_path=sequencing_run.trailblazer_config_path.as_posix(),
            out_dir=sequencing_run.trailblazer_config_path.parent.as_posix(),
            priority=self.trailblazer_priority,
            email=self.mail,
            workflow=Workflow.DEMULTIPLEX,
        )

    def start_demultiplexing(self, sequencing_run: IlluminaRunDirectoryData):
        """Start demultiplexing for a sequencing run."""
        self.create_demultiplexing_started_file(sequencing_run.demultiplexing_started_path)
        log_path: Path = self.get_stderr_logfile(sequencing_run=sequencing_run)
        error_function: str = self.get_sbatch_error(
            sequencing_run=sequencing_run,
            email=self.mail,
            demux_dir=self.demultiplexed_run_dir_path(sequencing_run),
        )
        commands: str = self.get_sbatch_command(
            run_dir=sequencing_run.path,
            demux_dir=self.demultiplexed_run_dir_path(sequencing_run=sequencing_run),
            sample_sheet=sequencing_run.sample_sheet_path,
            demux_completed=self.demultiplexing_completed_path(sequencing_run=sequencing_run),
            environment=self.environment,
        )
        sbatch_parameters: SbatchDragen = SbatchDragen(
            account=self.slurm_account,
            commands=commands,
            email=self.mail,
            error=error_function,
            hours=36,
            job_name=self.get_run_name(sequencing_run),
            log_dir=log_path.parent.as_posix(),
            quality_of_service=self.slurm_quality_of_service,
        )
        sbatch_content: str = self.slurm_api.generate_sbatch_content(
            sbatch_parameters=sbatch_parameters
        )
        sbatch_path: Path = self.demultiplex_sbatch_path(sequencing_run=sequencing_run)
        sbatch_number: int = self.slurm_api.submit_sbatch(
            sbatch_content=sbatch_content, sbatch_path=sbatch_path
        )
        LOG.info(f"Demultiplexing running as job {sbatch_number}")
        return sbatch_number

    def prepare_output_directory(self, sequencing_run: IlluminaRunDirectoryData) -> None:
        """Makes sure the output directory is ready for demultiplexing."""
        self.remove_demultiplexing_output_directory(sequencing_run)
        self.create_demultiplexing_output_dir(sequencing_run)

    def remove_demultiplexing_output_directory(
        self, sequencing_run: IlluminaRunDirectoryData
    ) -> None:
        if (
            not self.dry_run
            and self.demultiplexed_run_dir_path(sequencing_run=sequencing_run).exists()
        ):
            shutil.rmtree(
                self.demultiplexed_run_dir_path(sequencing_run=sequencing_run), ignore_errors=False
            )

    def create_demultiplexing_output_dir(self, sequencing_run: IlluminaRunDirectoryData) -> None:
        """Creates the demultiplexing output directory for the sequencing run."""
        output_directory: Path = self.demultiplexed_run_dir_path(sequencing_run)
        LOG.debug(f"Creating demultiplexing output directory: {output_directory}")
        output_directory.mkdir(exist_ok=False, parents=True)
