"""This API should handle everything around demultiplexing."""
import logging
import shutil
from pathlib import Path

from typing_extensions import Literal

from cg.apps.demultiplex.sbatch import DEMULTIPLEX_COMMAND, DEMULTIPLEX_ERROR
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.slurm.slurm_api import SlurmAPI
from cg.apps.tb import TrailblazerAPI
from cg.constants.constants import FileFormat, Pipeline
from cg.constants.demultiplexing import BclConverter, DemultiplexingDirsAndFiles
from cg.constants.priority import SlurmQos
from cg.constants.tb import AnalysisTypes
from cg.exc import HousekeeperFileMissingError
from cg.io.controller import WriteFile
from cg.models.demultiplex.sbatch import SbatchCommand, SbatchError
from cg.models.flow_cell.flow_cell import FlowCellDirectoryData
from cg.models.slurm.sbatch import Sbatch, SbatchDragen

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
        self.flow_cells_dir: Path = Path(config["flow_cells_dir"])
        self.demultiplexed_runs_dir: Path = out_dir or Path(config["demultiplexed_flow_cells_dir"])
        self.environment: str = config.get("environment", "stage")
        LOG.info(f"Set environment to {self.environment}")
        self.dry_run: bool = False

    @property
    def slurm_quality_of_service(self) -> Literal[SlurmQos.HIGH, SlurmQos.LOW]:
        """Return SLURM quality of service."""
        return SlurmQos.LOW if self.environment == "stage" else SlurmQos.HIGH

    def set_dry_run(self, dry_run: bool) -> None:
        """Set dry run."""
        LOG.debug(f"DemultiplexingAPI: Set dry run to {dry_run}")
        self.dry_run = dry_run
        self.slurm_api.set_dry_run(dry_run=dry_run)

    @staticmethod
    def get_sbatch_error(
        flow_cell: FlowCellDirectoryData,
        email: str,
        demux_dir: Path,
    ) -> str:
        """Create the sbatch error string."""
        LOG.debug("Creating the sbatch error string")
        error_parameters: SbatchError = SbatchError(
            flow_cell_id=flow_cell.id,
            email=email,
            logfile=DemultiplexingAPI.get_stderr_logfile(flow_cell=flow_cell).as_posix(),
            demux_dir=demux_dir.as_posix(),
            demux_started=flow_cell.demultiplexing_started_path.as_posix(),
        )
        return DEMULTIPLEX_ERROR.format(**error_parameters.model_dump())

    @staticmethod
    def get_sbatch_command(
        run_dir: Path,
        demux_dir: Path,
        sample_sheet: Path,
        demux_completed: Path,
        flow_cell: FlowCellDirectoryData,
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
        return DEMULTIPLEX_COMMAND[flow_cell.bcl_converter].format(
            **command_parameters.model_dump()
        )

    @staticmethod
    def demultiplex_sbatch_path(flow_cell: FlowCellDirectoryData) -> Path:
        """Get the path to where sbatch script file should be kept."""
        return Path(flow_cell.path, "demux-novaseq.sh")

    @staticmethod
    def get_run_name(flow_cell: FlowCellDirectoryData) -> str:
        """Create the run name for the sbatch job."""
        return f"{flow_cell.id}_demultiplex"

    @staticmethod
    def get_stderr_logfile(flow_cell: FlowCellDirectoryData) -> Path:
        """Create the path to the stderr logfile."""
        return Path(flow_cell.path, f"{DemultiplexingAPI.get_run_name(flow_cell)}.stderr")

    @staticmethod
    def get_stdout_logfile(flow_cell: FlowCellDirectoryData) -> Path:
        """Create the path to the stdout logfile."""
        return Path(flow_cell.path, f"{DemultiplexingAPI.get_run_name(flow_cell)}.stdout")

    def flow_cell_out_dir_path(self, flow_cell: FlowCellDirectoryData) -> Path:
        """Create the path to where the demultiplexed result should be produced."""
        return Path(self.demultiplexed_runs_dir, flow_cell.path.name)

    def is_sample_sheet_in_housekeeper(self, flow_cell_id: str) -> bool:
        """Returns True if the sample sheet for the flow cell exists in Housekeeper."""
        try:
            self.hk_api.get_sample_sheet_path(flow_cell_id)
            return True
        except HousekeeperFileMissingError:
            return False

    def get_flow_cell_unaligned_dir(self, flow_cell: FlowCellDirectoryData) -> Path:
        """Returns the path to where the demultiplexed result are located."""
        return Path(
            self.flow_cell_out_dir_path(flow_cell), DemultiplexingDirsAndFiles.UNALIGNED_DIR_NAME
        )

    def demultiplexing_completed_path(self, flow_cell: FlowCellDirectoryData) -> Path:
        """Return the path to demultiplexing complete file."""
        LOG.info(
            Path(self.flow_cell_out_dir_path(flow_cell), DemultiplexingDirsAndFiles.DEMUX_COMPLETE)
        )
        return Path(
            self.flow_cell_out_dir_path(flow_cell), DemultiplexingDirsAndFiles.DEMUX_COMPLETE
        )

    def is_demultiplexing_possible(self, flow_cell: FlowCellDirectoryData) -> bool:
        """Check if it is possible to start demultiplexing.

        This means that
            - flow cell should be ready for demultiplexing (all files in place)
            - sample sheet needs to exist
            - demultiplexing should not be running
        """
        LOG.info(f"Check if demultiplexing is possible for {flow_cell.id}")
        demultiplexing_possible = True
        if not flow_cell.is_flow_cell_ready():
            demultiplexing_possible = False

        if not flow_cell.sample_sheet_exists():
            LOG.warning(f"Could not find sample sheet in flow cell directory for {flow_cell.id}")
            demultiplexing_possible = False

        if not self.is_sample_sheet_in_housekeeper(flow_cell_id=flow_cell.id):
            LOG.warning(f"Could not find sample sheet in Housekeeper for {flow_cell.id}")
            demultiplexing_possible = False

        if (
            flow_cell.has_demultiplexing_started_locally()
            or flow_cell.has_demultiplexing_started_on_sequencer()
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
        self, tb_api: TrailblazerAPI, slurm_job_id: int, flow_cell: FlowCellDirectoryData
    ):
        """Add demultiplexing entry to trailblazer."""
        if self.dry_run:
            return
        self.write_trailblazer_config(
            content=self.get_trailblazer_config(slurm_job_id=slurm_job_id),
            file_path=flow_cell.trailblazer_config_path,
        )
        tb_api.add_pending_analysis(
            case_id=flow_cell.id,
            analysis_type=AnalysisTypes.OTHER,
            config_path=flow_cell.trailblazer_config_path.as_posix(),
            out_dir=flow_cell.trailblazer_config_path.parent.as_posix(),
            slurm_quality_of_service=self.slurm_quality_of_service,
            email=self.mail,
            data_analysis=str(Pipeline.DEMULTIPLEX),
        )

    def start_demultiplexing(self, flow_cell: FlowCellDirectoryData):
        """Start demultiplexing for a flow cell."""
        self.create_demultiplexing_started_file(flow_cell.demultiplexing_started_path)
        log_path: Path = self.get_stderr_logfile(flow_cell=flow_cell)
        error_function: str = self.get_sbatch_error(
            flow_cell=flow_cell, email=self.mail, demux_dir=self.flow_cell_out_dir_path(flow_cell)
        )
        commands: str = self.get_sbatch_command(
            run_dir=flow_cell.path,
            demux_dir=self.flow_cell_out_dir_path(flow_cell=flow_cell),
            sample_sheet=flow_cell.sample_sheet_path,
            demux_completed=self.demultiplexing_completed_path(flow_cell=flow_cell),
            flow_cell=flow_cell,
            environment=self.environment,
        )

        if flow_cell.bcl_converter == BclConverter.BCL2FASTQ:
            sbatch_parameters: Sbatch = Sbatch(
                account=self.slurm_account,
                commands=commands,
                email=self.mail,
                error=error_function,
                hours=36,
                job_name=self.get_run_name(flow_cell),
                log_dir=log_path.parent.as_posix(),
                memory=125,
                number_tasks=18,
                quality_of_service=self.slurm_quality_of_service,
            )
        if flow_cell.bcl_converter == BclConverter.DRAGEN:
            sbatch_parameters: SbatchDragen = SbatchDragen(
                account=self.slurm_account,
                commands=commands,
                email=self.mail,
                error=error_function,
                hours=36,
                job_name=self.get_run_name(flow_cell),
                log_dir=log_path.parent.as_posix(),
                quality_of_service=self.slurm_quality_of_service,
            )

        sbatch_content: str = self.slurm_api.generate_sbatch_content(
            sbatch_parameters=sbatch_parameters
        )
        sbatch_path: Path = self.demultiplex_sbatch_path(flow_cell=flow_cell)
        sbatch_number: int = self.slurm_api.submit_sbatch(
            sbatch_content=sbatch_content, sbatch_path=sbatch_path
        )
        LOG.info(f"Demultiplexing running as job {sbatch_number}")
        return sbatch_number

    def prepare_output_directory(self, flow_cell: FlowCellDirectoryData) -> None:
        """Makes sure the output directory is ready for demultiplexing."""
        self.remove_demultiplexing_output_directory(flow_cell)
        self.create_demultiplexing_output_dir(flow_cell)

    def remove_demultiplexing_output_directory(self, flow_cell: FlowCellDirectoryData) -> None:
        if not self.dry_run and self.flow_cell_out_dir_path(flow_cell=flow_cell).exists():
            shutil.rmtree(self.flow_cell_out_dir_path(flow_cell=flow_cell), ignore_errors=False)

    def create_demultiplexing_output_dir(self, flow_cell: FlowCellDirectoryData) -> None:
        """Creates the demultiplexing output directory and, if necessary, the unaligned directory."""
        output_directory: Path = self.flow_cell_out_dir_path(flow_cell)
        LOG.debug(f"Creating demultiplexing output directory: {output_directory}")
        output_directory.mkdir(exist_ok=False, parents=True)
        if flow_cell.bcl_converter == BclConverter.BCL2FASTQ:
            self.get_flow_cell_unaligned_dir(flow_cell).mkdir(exist_ok=False, parents=False)
