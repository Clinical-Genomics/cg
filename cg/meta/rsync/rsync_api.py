"""Module for building the rsync command to send files to customer inbox on caesar"""
import datetime
import glob
import logging
import yaml
from pathlib import Path
from typing import List, Dict, Iterable

from cg.apps.slurm.slurm_api import SlurmAPI
from cg.apps.tb import TrailblazerAPI
from cg.exc import CgError
from cg.meta.meta import MetaAPI
from cg.meta.rsync.sbatch import RSYNC_COMMAND, ERROR_RSYNC_FUNCTION, COVID_RSYNC
from cg.models.cg_config import CGConfig
from cg.models.slurm.sbatch import Sbatch
from cg.store import models
from cgmodels.cg.constants import Pipeline

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
        self.priority: str = "low"
        self.pipeline: str = str(Pipeline.RSYNC)

    @property
    def trailblazer_config_path(self) -> Path:
        """Return Path to trailblazer config"""
        return self.log_dir / "slurm_job_ids.yaml"

    @property
    def rsync_processes(self) -> Iterable[Path]:
        """Yield existing rsync processes"""
        for process in self.base_path.iterdir():
            yield process

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

    def set_log_dir(self, ticket_id: int) -> None:
        if self.log_dir.as_posix() == self.base_path.as_posix():
            timestamp = datetime.datetime.now()
            timestamp_str = timestamp.strftime("%y%m%d_%H_%M_%S_%f")
            folder_name = Path("_".join([str(ticket_id), timestamp_str]))
            LOG.info(f"Setting log dir to: {self.base_path / folder_name}")
            self.log_dir: Path = self.base_path / folder_name

    def get_all_cases_from_ticket(self, ticket_id: int) -> List[models.Family]:
        cases: List[models.Family] = self.status_db.get_cases_from_ticket(ticket_id=ticket_id).all()
        return cases

    def get_source_path(self, ticket_id: int) -> str:
        cases: List[models.Family] = self.get_all_cases_from_ticket(ticket_id=ticket_id)
        if not cases:
            LOG.warning("Could not find any cases for ticket_id %s", ticket_id)
            raise CgError()
        customer_id: str = cases[0].customer.internal_id
        delivery_source_path: str = (
            Path(self.delivery_path, customer_id, "inbox", str(ticket_id)).as_posix() + "/"
        )
        return delivery_source_path

    def get_destination_path(self, ticket_id: int) -> str:
        cases: List[models.Family] = self.get_all_cases_from_ticket(ticket_id=ticket_id)
        customer_id: str = cases[0].customer.internal_id
        rsync_destination_path: str = (
            Path(self.destination_path, customer_id, "inbox", str(ticket_id)).as_posix() + "/"
        )
        return rsync_destination_path

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
        source_path: str = self.get_source_path(ticket_id=ticket_id)
        destination_path: str = self.get_destination_path(ticket_id=ticket_id)
        cases: List[models.Family] = self.get_all_cases_from_ticket(ticket_id=ticket_id)
        customer_id: str = cases[0].customer.internal_id
        if cases[0].data_analysis == Pipeline.SARS_COV_2:
            LOG.info("Delivering report for SARS-COV-2 analysis")
            covid_report_options: List[str] = glob.glob(
                self.covid_report_path % (str(cases[0].internal_id), ticket_id)
            )
            if not covid_report_options:
                LOG.error(
                    f"No report file could be found with path"
                    f" {self.covid_report_path % (str(cases[0].internal_id), ticket_id)}!"
                )
                raise CgError()
            covid_report_path: str = covid_report_options[0]
            covid_destination_path: str = self.covid_destination_path % customer_id
            commands = COVID_RSYNC.format(
                source_path=source_path,
                destination_path=destination_path,
                covid_report_path=covid_report_path,
                covid_destination_path=covid_destination_path,
                log_dir=self.log_dir,
            )
        else:
            commands = RSYNC_COMMAND.format(
                source_path=source_path, destination_path=destination_path
            )
        error_function = ERROR_RSYNC_FUNCTION.format()
        sbatch_info = {
            "job_name": "_".join([str(ticket_id), "rsync"]),
            "account": self.account,
            "number_tasks": 1,
            "memory": 1,
            "log_dir": self.log_dir.as_posix(),
            "email": self.mail_user,
            "hours": 24,
            "priority": self.priority,
            "commands": commands,
            "error": error_function,
        }
        slurm_api = SlurmAPI()
        slurm_api.set_dry_run(dry_run=dry_run)
        sbatch_content: str = slurm_api.generate_sbatch_content(Sbatch.parse_obj(sbatch_info))
        sbatch_path = self.log_dir / "_".join([str(ticket_id), "rsync.sh"])
        sbatch_number: int = slurm_api.submit_sbatch(
            sbatch_content=sbatch_content, sbatch_path=sbatch_path
        )
        return sbatch_number
