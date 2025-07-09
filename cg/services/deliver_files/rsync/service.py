"""Module for building the rsync command to send files to customer inbox on the delivery server."""

import datetime as dt
import glob
import logging
from pathlib import Path
from typing import Iterable

from cg.apps.slurm.slurm_api import SlurmAPI
from cg.apps.tb import TrailblazerAPI
from cg.constants import Workflow
from cg.constants.constants import FileFormat
from cg.constants.delivery import INBOX_NAME
from cg.constants.priority import SlurmAccount, SlurmQos, TrailblazerPriority
from cg.constants.slurm import (
    SLURM_UPLOAD_EXCLUDED_COMPUTE_NODES,
    SLURM_UPLOAD_MAX_HOURS,
    SLURM_UPLOAD_MEMORY,
    SLURM_UPLOAD_TASKS,
)
from cg.constants.tb import AnalysisType
from cg.exc import CgError
from cg.io.controller import WriteFile
from cg.models.slurm.sbatch import Sbatch
from cg.services.deliver_files.rsync.models import RsyncDeliveryConfig
from cg.services.deliver_files.rsync.sbatch_commands import (
    COVID_REPORT_RSYNC,
    COVID_RSYNC,
    CREATE_INBOX_COMMAND,
    ERROR_CREATE_INBOX_FUNCTION,
    ERROR_RSYNC_FUNCTION,
    RSYNC_COMMAND,
)
from cg.store.models import Case
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class DeliveryRsyncService:
    def __init__(
        self,
        delivery_path: str,
        rsync_config: RsyncDeliveryConfig,
        status_db: Store,
    ):
        self.status_db = status_db
        self.delivery_path: str = delivery_path
        self.destination_path: str = rsync_config.destination_path
        self.covid_destination_path: str = rsync_config.covid_destination_path
        self.covid_report_path: str = rsync_config.covid_report_path
        self.base_path: Path = Path(rsync_config.base_path)
        self.account: str = rsync_config.account
        self.log_dir: Path = Path(rsync_config.base_path)
        self.mail_user: str = rsync_config.mail_user
        self.workflow: str = Workflow.RSYNC

    @property
    def slurm_quality_of_service(self) -> SlurmQos:
        """Return the slurm quality of service depending on the slurm account."""
        return SlurmQos.HIGH if self.account == SlurmAccount.PRODUCTION else SlurmQos.LOW

    @property
    def trailblazer_priority(self) -> TrailblazerPriority:
        """Return the trailblazer priority depending on the slurm account."""
        return (
            TrailblazerPriority.HIGH
            if self.account == SlurmAccount.PRODUCTION
            else TrailblazerPriority.LOW
        )

    @property
    def trailblazer_config_path(self) -> Path:
        """Return Path to trailblazer config."""
        return self.log_dir / "slurm_job_ids.yaml"

    @property
    def rsync_processes(self) -> Iterable[Path]:
        """Yield existing rsync processes."""
        yield from self.base_path.iterdir()

    @staticmethod
    def format_covid_destination_path(
        covid_destination_path: str, customer_internal_id: str
    ) -> str:
        """Return destination path of covid report."""
        return covid_destination_path % customer_internal_id

    @staticmethod
    def get_trailblazer_config(slurm_job_id: int) -> dict[str, list[str]]:
        """Return dictionary of slurm job IDs."""
        return {"jobs": [str(slurm_job_id)]}

    @staticmethod
    def write_trailblazer_config(content: dict, config_path: Path, dry_run: bool = False) -> None:
        """Write slurm job IDs to a .YAML file used as the trailblazer config."""
        if dry_run:
            LOG.info(f"Dry-run: it would write slurm jobs to {config_path.as_posix()}")
            return
        LOG.info(f"Writing slurm jobs to {config_path.as_posix()}")
        WriteFile.write_file_from_content(
            content=content, file_format=FileFormat.YAML, file_path=config_path
        )

    @staticmethod
    def process_ready_to_clean(before: dt.datetime, process: Path) -> bool:
        """Return True if analysis is old enough to be cleaned."""

        ctime: dt.datetime = dt.datetime.fromtimestamp(process.stat().st_ctime)

        return before > ctime

    def concatenate_rsync_commands(
        self,
        folder_list: set[Path],
        source_and_destination_paths: dict[str, Path],
        ticket: str,
        case: Case,
    ) -> str:
        """Concatenates the rsync commands for each folder to be transferred."""
        command: str = ""
        for folder in folder_list:
            source_path = Path(source_and_destination_paths["delivery_source_path"], folder.name)
            destination_path: Path = Path(
                source_and_destination_paths["rsync_destination_path"], ticket
            )

            command += RSYNC_COMMAND.format(
                source_path=source_path, destination_path=destination_path
            )
        if case.data_analysis == Workflow.MUTANT:
            covid_report_path: str = self.format_covid_report_path(case=case, ticket=ticket)
            covid_destination_path: str = self.format_covid_destination_path(
                self.covid_destination_path, customer_internal_id=case.customer.internal_id
            )
            command += COVID_REPORT_RSYNC.format(
                covid_report_path=covid_report_path,
                covid_destination_path=covid_destination_path,
                log_dir=self.log_dir,
            )
        return command

    def set_log_dir(self, folder_prefix: str) -> None:
        if folder_prefix not in str(self.log_dir.as_posix()):
            timestamp = dt.datetime.now()
            timestamp_str = timestamp.strftime("%y%m%d_%H_%M_%S_%f")
            folder_name = Path("_".join([folder_prefix, timestamp_str]))
            LOG.info(f"Setting log dir to: {self.base_path / folder_name}")
            self.log_dir: Path = self.base_path / folder_name

    def get_all_cases_from_ticket(self, ticket: str) -> list[Case]:
        return self.status_db.get_cases_by_ticket_id(ticket_id=ticket)

    def get_source_and_destination_paths(
        self, ticket: str, customer_internal_id: str
    ) -> dict[str, Path]:
        """Return the source and destination paths."""
        source_and_destination_paths: dict[str, Path] = {
            "delivery_source_path": Path(
                self.delivery_path, customer_internal_id, INBOX_NAME, ticket
            ),
            "rsync_destination_path": Path(self.destination_path, customer_internal_id, INBOX_NAME),
        }
        return source_and_destination_paths

    def add_to_trailblazer_api(
        self, tb_api: TrailblazerAPI, slurm_job_id: int, ticket: str, dry_run: bool
    ) -> None:
        """Add rsync process to trailblazer."""
        if dry_run:
            return
        self.write_trailblazer_config(
            content=self.get_trailblazer_config(slurm_job_id),
            config_path=self.trailblazer_config_path,
        )
        tb_api.add_pending_analysis(
            case_id=ticket,
            analysis_type=AnalysisType.OTHER,
            config_path=self.trailblazer_config_path.as_posix(),
            out_dir=self.log_dir.as_posix(),
            priority=self.trailblazer_priority,
            email=self.mail_user,
            workflow=Workflow.RSYNC,
            ticket=ticket,
        )

    def format_covid_report_path(self, case: Case, ticket: str) -> str:
        """Return a formatted of covid report path."""
        covid_report_options: list[str] = glob.glob(
            self.covid_report_path % (case.internal_id, ticket)
        )
        if not covid_report_options:

            raise FileNotFoundError(
                f"No report file could be found with path"
                f" {self.covid_report_path % (case.internal_id, ticket)}!"
            )
        return covid_report_options[0]

    def create_log_dir(self, dry_run: bool) -> None:
        """Create log dir."""
        log_dir: Path = self.log_dir
        LOG.info(f"Creating folder: {log_dir}")
        if log_dir.exists():
            LOG.warning(f"Could not create {log_dir}, this folder already exist")
        elif dry_run:
            LOG.info(f"Would have created path {log_dir}, but this is a dry run")
        else:
            log_dir.mkdir(parents=True, exist_ok=True)

    def run_rsync_for_case(self, case: Case, dry_run: bool, folders_to_deliver: set[Path]) -> int:
        """Submit Rsync commands for delivering a case to the delivery server and return the job id."""
        ticket: str | None = case.latest_ticket
        if not ticket:
            raise CgError(f"Could not find ticket for case {case.internal_id}")

        source_and_destination_paths: dict[str, Path] = self.get_source_and_destination_paths(
            ticket=ticket, customer_internal_id=case.customer.internal_id
        )

        self.set_log_dir(folder_prefix=case.internal_id)
        self.create_log_dir(dry_run=dry_run)

        folder_creation_job_id: int = self._create_remote_ticket_inbox(
            dry_run=dry_run,
            ticket=ticket,
            source_and_destination_paths=source_and_destination_paths,
        )

        return self._deliver_folder_contents(
            case=case,
            dry_run=dry_run,
            folder_creation_job_id=folder_creation_job_id,
            folders_to_deliver=folders_to_deliver,
            ticket=ticket,
            source_and_destination_paths=source_and_destination_paths,
        )

    def run_rsync_for_ticket(self, ticket: str, dry_run: bool) -> int:
        """Runs rsync of a whole ticket folder to the delivery server."""
        self.set_log_dir(folder_prefix=ticket)
        self.create_log_dir(dry_run=dry_run)
        cases: list[Case] = self.get_all_cases_from_ticket(ticket=ticket)
        if not cases:
            LOG.warning(f"Could not find any cases for ticket {ticket}")
            raise CgError()
        customer_internal_id: str = cases[0].customer.internal_id
        source_and_destination_paths: dict[str, Path] = self.get_source_and_destination_paths(
            ticket=ticket, customer_internal_id=customer_internal_id
        )
        if cases[0].data_analysis == Workflow.MUTANT:
            LOG.info("Delivering report for SARS-COV-2 analysis")
            commands = COVID_RSYNC.format(
                source_path=source_and_destination_paths["delivery_source_path"],
                destination_path=source_and_destination_paths["rsync_destination_path"],
                covid_report_path=self.format_covid_report_path(case=cases[0], ticket=ticket),
                covid_destination_path=self.format_covid_destination_path(
                    self.covid_destination_path, customer_internal_id=customer_internal_id
                ),
                log_dir=self.log_dir,
            )
        else:
            commands = RSYNC_COMMAND.format(
                source_path=source_and_destination_paths["delivery_source_path"],
                destination_path=source_and_destination_paths["rsync_destination_path"],
            )

        return self._generate_and_submit_sbatch(
            commands=commands,
            dry_run=dry_run,
            error_command=ERROR_RSYNC_FUNCTION,
            exclude=SLURM_UPLOAD_EXCLUDED_COMPUTE_NODES,
            job_name=f"{ticket}_rsync",
        )

    def _create_remote_ticket_inbox(
        self, dry_run: bool, ticket: str, source_and_destination_paths: dict[str, Path]
    ) -> int:
        host, inbox_path = (
            source_and_destination_paths["rsync_destination_path"].as_posix().split(":")
        )
        inbox_path: str = f"{inbox_path}/{ticket}"
        job_name: str = f"{ticket}_create_inbox"

        commands: str = CREATE_INBOX_COMMAND.format(host=host, inbox_path=inbox_path)
        error_command = ERROR_CREATE_INBOX_FUNCTION

        return self._generate_and_submit_sbatch(
            commands=commands, error_command=error_command, job_name=job_name, dry_run=dry_run
        )

    def _deliver_folder_contents(
        self,
        case: Case,
        folder_creation_job_id: int,
        folders_to_deliver: set[Path],
        ticket: str,
        source_and_destination_paths: dict[str, Path],
        dry_run: bool = False,
    ) -> int:
        """Submit the job that rsyncs case data to the delivery server and return the job id."""
        command: str = self.concatenate_rsync_commands(
            folder_list=folders_to_deliver,
            source_and_destination_paths=source_and_destination_paths,
            ticket=ticket,
            case=case,
        )

        return self._generate_and_submit_sbatch(
            commands=command,
            dry_run=dry_run,
            error_command=ERROR_RSYNC_FUNCTION,
            exclude=SLURM_UPLOAD_EXCLUDED_COMPUTE_NODES,
            job_name=f"{case.internal_id}_rsync",
            dependency=f"--dependency=afterok:{folder_creation_job_id}",
        )

    def _generate_and_submit_sbatch(
        self,
        job_name: str,
        commands: str,
        error_command: str,
        dry_run: bool = False,
        dependency: str | None = None,
        exclude: str | None = None,
    ) -> int:
        sbatch_parameters: Sbatch = Sbatch(
            account=self.account,
            commands=commands,
            dependency=dependency,
            email=self.mail_user,
            error=error_command,
            exclude=exclude,
            hours=SLURM_UPLOAD_MAX_HOURS,
            job_name=job_name,
            log_dir=self.log_dir.as_posix(),
            memory=SLURM_UPLOAD_MEMORY,
            number_tasks=SLURM_UPLOAD_TASKS,
            quality_of_service=self.slurm_quality_of_service,
        )

        slurm_api = SlurmAPI()
        slurm_api.set_dry_run(dry_run=dry_run)
        sbatch_content: str = slurm_api.generate_sbatch_content(sbatch_parameters=sbatch_parameters)
        sbatch_path = Path(self.log_dir, f"{job_name}.sh")
        sbatch_number: int = slurm_api.submit_sbatch(
            sbatch_content=sbatch_content, sbatch_path=sbatch_path
        )
        return sbatch_number
