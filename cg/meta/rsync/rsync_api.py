"""Module for building the rsync command to send files to customer inbox on caesar"""
import datetime as dt
import glob
import logging
import yaml
from pathlib import Path
from typing import List, Dict, Iterable

from cg.apps.slurm.slurm_api import SlurmAPI
from cg.apps.tb import TrailblazerAPI
from cg.constants.priority import SlurmQos
from cg.exc import CgError
from cg.meta.meta import MetaAPI
from cg.meta.rsync.sbatch import RSYNC_COMMAND, ERROR_RSYNC_FUNCTION, COVID_RSYNC
from cg.models.cg_config import CGConfig
from cg.models.slurm.sbatch import Sbatch
from cg.store import models
from cg.constants import Pipeline
from cg.constants.priority import SLURM_ACCOUNT_TO_QOS

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
        self.priority: str = SlurmQos.LOW
        self.pipeline: str = Pipeline.RSYNC

    @property
    def trailblazer_config_path(self) -> Path:
        """Return Path to trailblazer config"""
        return self.log_dir / "slurm_job_ids.yaml"

    @property
    def rsync_processes(self) -> Iterable[Path]:
        """Yield existing rsync processes"""
        yield from self.base_path.iterdir()

    @staticmethod
    def format_covid_destination_path(covid_destination_path: str, customer_id: str) -> str:
        """Return destination path of covid report"""
        return covid_destination_path % customer_id

    @staticmethod
    def get_trailblazer_config(slurm_job_id: int) -> Dict[str, List[str]]:
        """Return dictionary of slurm job IDs"""
        return {"jobs": [str(slurm_job_id)]}

    @staticmethod
    def write_trailblazer_config(content: dict, config_path: Path) -> None:
        """Write slurm job IDs to a .YAML file used as the trailblazer config"""
        LOG.info(f"Writing slurm jobs to {config_path.as_posix()}")
        with config_path.open("w") as yaml_file:
            yaml.safe_dump(content, yaml_file, indent=4, explicit_start=True)

    @staticmethod
    def process_ready_to_clean(before: dt.datetime, process: Path) -> bool:
        """Return True if analysis is old enough to be cleaned"""

        ctime: dt.datetime = dt.datetime.fromtimestamp(process.stat().st_ctime)

        return before > ctime

    def set_log_dir(self, ticket_id: int) -> None:
        if self.log_dir.as_posix() == self.base_path.as_posix():
            timestamp = dt.datetime.now()
            timestamp_str = timestamp.strftime("%y%m%d_%H_%M_%S_%f")
            folder_name = Path("_".join([str(ticket_id), timestamp_str]))
            LOG.info(f"Setting log dir to: {self.base_path / folder_name}")
            self.log_dir: Path = self.base_path / folder_name

    def get_all_cases_from_ticket(self, ticket_id: int) -> List[models.Family]:
        cases: List[models.Family] = self.status_db.get_cases_from_ticket(ticket_id=ticket_id).all()
        return cases

    def get_source_and_destination_paths(self, ticket_id: int) -> Dict[str, str]:
        cases: List[models.Family] = self.get_all_cases_from_ticket(ticket_id=ticket_id)
        source_and_destination_paths = {}
        if not cases:
            LOG.warning("Could not find any cases for ticket_id %s", ticket_id)
            raise CgError()
        customer_id: str = cases[0].customer.internal_id
        source_and_destination_paths["delivery_source_path"]: Path = (
            Path(self.delivery_path, customer_id, "inbox", str(ticket_id)).as_posix() + "/"
        )
        source_and_destination_paths["rsync_destination_path"]: Path = (
            Path(self.destination_path, customer_id, "inbox", str(ticket_id)).as_posix() + "/"
        )
        return source_and_destination_paths

    def add_to_trailblazer_api(
        self, tb_api: TrailblazerAPI, slurm_job_id: int, ticket_id: int, dry_run: bool
    ) -> None:
        """Add rsync process to trailblazer"""
        if dry_run:
            return
        self.write_trailblazer_config(
            content=self.get_trailblazer_config(slurm_job_id),
            config_path=self.trailblazer_config_path,
        )
        tb_api.add_pending_analysis(
            case_id=str(ticket_id),
            analysis_type="other",
            config_path=self.trailblazer_config_path.as_posix(),
            out_dir=self.log_dir.as_posix(),
            priority=self.priority,
            email=self.mail_user,
            data_analysis=Pipeline.RSYNC,
        )

    def format_covid_report_path(self, case: models.Family, ticket_id: int) -> str:
        """Return a formatted of covid report path"""
        covid_report_options: List[str] = glob.glob(
            self.covid_report_path % (str(case.internal_id), ticket_id)
        )
        if not covid_report_options:
            LOG.error(
                f"No report file could be found with path"
                f" {self.covid_report_path % (str(case.internal_id), ticket_id)}!"
            )
            raise CgError()
        return covid_report_options[0]

    def create_log_dir(self, dry_run: bool) -> None:
        """Create log dir"""
        log_dir: Path = self.log_dir
        LOG.info("Creating folder: %s", log_dir)
        if log_dir.exists():
            LOG.warning("Could not create %s, this folder already exist", log_dir)
        elif dry_run:
            LOG.info("Would have created path %s, but this is a dry run", log_dir)
        else:
            log_dir.mkdir(parents=True, exist_ok=True)

    def run_rsync_on_slurm(self, ticket_id: int, dry_run: bool) -> int:
        self.set_log_dir(ticket_id=ticket_id)
        self.create_log_dir(dry_run=dry_run)
        source_and_destination_paths: Dict[str, str] = self.get_source_and_destination_paths(
            ticket_id=ticket_id
        )
        cases: List[models.Family] = self.get_all_cases_from_ticket(ticket_id=ticket_id)
        customer_id: str = cases[0].customer.internal_id
        if cases[0].data_analysis == Pipeline.SARS_COV_2:
            LOG.info("Delivering report for SARS-COV-2 analysis")
            commands = COVID_RSYNC.format(
                source_path=source_and_destination_paths["delivery_source_path"],
                destination_path=source_and_destination_paths["rsync_destination_path"],
                covid_report_path=self.format_covid_report_path(case=cases[0], ticket_id=ticket_id),
                covid_destination_path=self.format_covid_destination_path(
                    self.covid_destination_path, customer_id=customer_id
                ),
                log_dir=self.log_dir,
            )
        else:
            commands = RSYNC_COMMAND.format(
                source_path=source_and_destination_paths["delivery_source_path"],
                destination_path=source_and_destination_paths["rsync_destination_path"],
            )
        if self.account in SLURM_ACCOUNT_TO_QOS.keys():
            priority = SLURM_ACCOUNT_TO_QOS[self.account]
        else:
            priority = "low"
        sbatch_info = {
            "job_name": "_".join([str(ticket_id), "rsync"]),
            "account": self.account,
            "number_tasks": 1,
            "memory": 1,
            "log_dir": self.log_dir.as_posix(),
            "email": self.mail_user,
            "hours": 24,
            "priority": priority,
            "commands": commands,
            "error": ERROR_RSYNC_FUNCTION.format(),
            "exclude": "--exclude=gpu-compute-0-[0-1],cg-dragen",
        }
        slurm_api = SlurmAPI()
        slurm_api.set_dry_run(dry_run=dry_run)
        sbatch_content: str = slurm_api.generate_sbatch_content(Sbatch.parse_obj(sbatch_info))
        sbatch_path = self.log_dir / "_".join([str(ticket_id), "rsync.sh"])
        sbatch_number: int = slurm_api.submit_sbatch(
            sbatch_content=sbatch_content, sbatch_path=sbatch_path
        )
        return sbatch_number
