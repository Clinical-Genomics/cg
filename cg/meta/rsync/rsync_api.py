"""Module for building the rsync command to send files to customer inbox on the delivery server."""
import datetime as dt
import glob
import logging
from pathlib import Path
from typing import Iterable

from cg.apps.slurm.slurm_api import SlurmAPI
from cg.apps.tb import TrailblazerAPI
from cg.constants import Pipeline
from cg.constants.constants import FileFormat
from cg.constants.delivery import INBOX_NAME
from cg.constants.priority import SlurmAccount, SlurmQos
from cg.constants.tb import AnalysisTypes
from cg.exc import CgError
from cg.io.controller import WriteFile
from cg.meta.meta import MetaAPI
from cg.meta.rsync.sbatch import COVID_RSYNC, ERROR_RSYNC_FUNCTION, RSYNC_COMMAND
from cg.models.cg_config import CGConfig
from cg.models.slurm.sbatch import Sbatch
from cg.store.models import Family

LOG = logging.getLogger(__name__)


class RsyncAPI(MetaAPI):
    def __init__(self, config: CGConfig):
        super().__init__(config)
        self.delivery_path: str = config.delivery_path
        self.destination_path: str = config.data_delivery.destination_path
        self.covid_destination_path: str = config.data_delivery.covid_destination_path
        self.covid_report_path: str = config.data_delivery.covid_report_path
        self.base_path: Path = Path(config.data_delivery.base_path)
        self.account: str = config.data_delivery.account
        self.log_dir: Path = Path(config.data_delivery.base_path)
        self.mail_user: str = config.data_delivery.mail_user
        self.pipeline: str = Pipeline.RSYNC

    @property
    def slurm_quality_of_service(self) -> str:
        """Return the slurm quality of service depending on the slurm account."""
        return SlurmQos.HIGH if self.account == SlurmAccount.PRODUCTION.value else SlurmQos.LOW

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
    def write_trailblazer_config(content: dict, config_path: Path) -> None:
        """Write slurm job IDs to a .YAML file used as the trailblazer config."""
        LOG.info(f"Writing slurm jobs to {config_path.as_posix()}")
        WriteFile.write_file_from_content(
            content=content, file_format=FileFormat.YAML, file_path=config_path
        )

    @staticmethod
    def process_ready_to_clean(before: dt.datetime, process: Path) -> bool:
        """Return True if analysis is old enough to be cleaned."""

        ctime: dt.datetime = dt.datetime.fromtimestamp(process.stat().st_ctime)

        return before > ctime

    @staticmethod
    def concatenate_rsync_commands(
        folder_list: list[str], source_and_destination_paths: dict[str, Path], ticket: str
    ) -> str:
        """Concatenates the rsync commands for each folder to be transferred."""
        commands = ""
        for folder in folder_list:
            source_path: Path = Path(source_and_destination_paths["delivery_source_path"], folder)
            destination_path: Path = Path(
                source_and_destination_paths["rsync_destination_path"], ticket
            )
            commands += RSYNC_COMMAND.format(
                source_path=source_path, destination_path=destination_path
            )
        return commands

    def set_log_dir(self, folder_prefix: str) -> None:
        if folder_prefix not in str(self.log_dir.as_posix()):
            timestamp = dt.datetime.now()
            timestamp_str = timestamp.strftime("%y%m%d_%H_%M_%S_%f")
            folder_name = Path("_".join([folder_prefix, timestamp_str]))
            LOG.info(f"Setting log dir to: {self.base_path / folder_name}")
            self.log_dir: Path = self.base_path / folder_name

    def get_all_cases_from_ticket(self, ticket: str) -> list[Family]:
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
            analysis_type=AnalysisTypes.OTHER,
            config_path=self.trailblazer_config_path.as_posix(),
            out_dir=self.log_dir.as_posix(),
            slurm_quality_of_service=self.slurm_quality_of_service,
            email=self.mail_user,
            data_analysis=Pipeline.RSYNC,
            ticket=ticket,
        )

    def format_covid_report_path(self, case: Family, ticket: str) -> str:
        """Return a formatted of covid report path."""
        covid_report_options: list[str] = glob.glob(
            self.covid_report_path % (case.internal_id, ticket)
        )
        if not covid_report_options:
            LOG.error(
                f"No report file could be found with path"
                f" {self.covid_report_path % (case.internal_id, ticket)}!"
            )
            raise CgError()
        return covid_report_options[0]

    def create_log_dir(self, dry_run: bool) -> None:
        """Create log dir."""
        log_dir: Path = self.log_dir
        LOG.info("Creating folder: %s", log_dir)
        if log_dir.exists():
            LOG.warning("Could not create %s, this folder already exist", log_dir)
        elif dry_run:
            LOG.info("Would have created path %s, but this is a dry run", log_dir)
        else:
            log_dir.mkdir(parents=True, exist_ok=True)

    def get_folders_to_deliver(
        self, case_id: str, sample_files_present: bool, case_files_present: bool
    ) -> list[str]:
        """Returns a list of all the folder names depending if sample and/or case data is to be
        transferred."""
        if not sample_files_present and not case_files_present:
            raise CgError(
                "Since neither case or sample files are present, no files will be transferred"
            )
        folder_list: list[str] = []
        if sample_files_present:
            folder_list.extend(
                [sample.name for sample in self.status_db.get_samples_by_case_id(case_id=case_id)]
            )
        if case_files_present:
            folder_list.append(self.status_db.get_case_by_internal_id(internal_id=case_id).name)
        return folder_list

    def slurm_rsync_single_case(
        self,
        case: Family,
        dry_run: bool,
        sample_files_present: bool = False,
        case_files_present: bool = False,
    ) -> tuple[bool, int]:
        """Runs rsync of a single case to the delivery server, parameters depend on delivery type."""
        case_id: str = case.internal_id

        ticket: str = self.status_db.get_latest_ticket_from_case(case_id=case_id)
        source_and_destination_paths: dict[str, Path] = self.get_source_and_destination_paths(
            ticket=ticket, customer_internal_id=case.customer.internal_id
        )
        self.set_log_dir(folder_prefix=case_id)
        self.create_log_dir(dry_run=dry_run)

        folders: list[str] = self.get_folders_to_deliver(
            case_id=case_id,
            sample_files_present=sample_files_present,
            case_files_present=case_files_present,
        )
        existing_folders: list[str] = [
            folder
            for folder in folders
            if Path(source_and_destination_paths["delivery_source_path"], folder).exists()
        ]
        commands: str = RsyncAPI.concatenate_rsync_commands(
            folder_list=existing_folders,
            source_and_destination_paths=source_and_destination_paths,
            ticket=ticket,
        )
        is_complete_delivery: bool = folders == existing_folders
        return is_complete_delivery, self.sbatch_rsync_commands(
            commands=commands, job_prefix=case_id, dry_run=dry_run
        )

    def run_rsync_on_slurm(self, ticket: str, dry_run: bool) -> int:
        """Runs rsync of a whole ticket folder to the delivery server."""
        self.set_log_dir(folder_prefix=ticket)
        self.create_log_dir(dry_run=dry_run)
        cases: list[Family] = self.get_all_cases_from_ticket(ticket=ticket)
        if not cases:
            LOG.warning(f"Could not find any cases for ticket {ticket}")
            raise CgError()
        customer_internal_id: str = cases[0].customer.internal_id
        source_and_destination_paths: dict[str, Path] = self.get_source_and_destination_paths(
            ticket=ticket, customer_internal_id=customer_internal_id
        )
        if cases[0].data_analysis == Pipeline.SARS_COV_2:
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
        return self.sbatch_rsync_commands(commands=commands, job_prefix=ticket, dry_run=dry_run)

    def sbatch_rsync_commands(
        self,
        commands: str,
        job_prefix: str,
        account: str = None,
        email: str = None,
        log_dir: str = None,
        hours: int = 24,
        number_tasks: int = 1,
        memory: int = 1,
        dry_run: bool = False,
    ) -> int:
        """Instantiates a slurm api and sbatches the given commands. Default parameters can be
        overridden."""
        sbatch_parameters: Sbatch = Sbatch(
            job_name="_".join([job_prefix, "rsync"]),
            account=account or self.account,
            number_tasks=number_tasks,
            memory=memory,
            log_dir=log_dir or self.log_dir.as_posix(),
            email=email or self.mail_user,
            hours=hours,
            quality_of_service=self.slurm_quality_of_service,
            commands=commands,
            error=ERROR_RSYNC_FUNCTION.format(),
            exclude="--exclude=gpu-compute-0-[0-1],cg-dragen",
        )
        slurm_api = SlurmAPI()
        slurm_api.set_dry_run(dry_run=dry_run)
        sbatch_content: str = slurm_api.generate_sbatch_content(sbatch_parameters=sbatch_parameters)
        sbatch_path = self.log_dir / "_".join([job_prefix, "rsync.sh"])
        sbatch_number: int = slurm_api.submit_sbatch(
            sbatch_content=sbatch_content, sbatch_path=sbatch_path
        )
        return sbatch_number
