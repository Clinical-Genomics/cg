"""Module for deliver and rsync customer inbox on the HPC to customer inbox on the delivery
server """
import logging
import os
import re
import datetime
from pathlib import Path
import shutil
from typing import List

from cg.constants.delivery import INBOX_NAME
from cg.exc import CgError
from cg.meta.meta import MetaAPI
from cg.models.cg_config import CGConfig
from cg.store import models


LOG = logging.getLogger(__name__)
PREFIX_TO_CONCATENATE = ["MWG", "MWL", "MWM", "MWR", "MWX"]


class DeliverTicketAPI(MetaAPI):
    def __init__(self, config: CGConfig):
        super().__init__(config)
        self.delivery_path: Path = Path(config.delivery_path)

    def get_all_cases_from_ticket(self, ticket: str) -> List[models.Family]:
        return self.status_db.get_cases_from_ticket(ticket=ticket).all()

    def get_inbox_path(self, ticket: str) -> Path:
        cases: List[models.Family] = self.get_all_cases_from_ticket(ticket=ticket)
        if not cases:
            raise CgError(
                f"The customer id was not identified since no cases for ticket {ticket} was found"
            )
        customer_id: str = cases[0].customer.internal_id
        return Path(self.delivery_path, customer_id, INBOX_NAME, ticket)

    def check_if_upload_is_needed(self, ticket: str) -> bool:
        customer_inbox: Path = self.get_inbox_path(ticket=ticket)
        LOG.info("Checking if path exist: %s", customer_inbox)
        if customer_inbox.exists():
            LOG.info("Could find path: %s", customer_inbox)
            return False
        LOG.info("Could not find path: %s", customer_inbox)
        return True

    def generate_date_tag(self, ticket: str) -> datetime.datetime:
        cases: List[models.Family] = self.get_all_cases_from_ticket(ticket=ticket)
        return cases[0].ordered_at

    def generate_output_filename(
        self, date: datetime.datetime, dir_path: Path, read_direction: int
    ) -> Path:
        base_name = Path("_".join([dir_path.name, str(read_direction)]))
        if date:
            base_name = Path("_".join([str(date.strftime("%y%m%d")), str(base_name)]))
        fastq_file_name = base_name.with_suffix(".fastq.gz")
        return Path(dir_path, fastq_file_name)

    @staticmethod
    def sort_files(files: List[Path]) -> List[Path]:
        files_map = {file_path.name: file_path for file_path in files}
        sorted_names = sorted(list(files_map.keys()))
        return [files_map[file_name] for file_name in sorted_names]

    def get_current_read_direction(self, dir_path: Path, read_direction: int) -> List[Path]:
        same_direction = []
        direction_string = ".+_R" + str(read_direction) + "_[0-9]+.fastq.gz"
        direction_pattern = re.compile(direction_string)
        file_path: Path
        for file_path in dir_path.iterdir():
            if direction_pattern.match(str(file_path)):
                same_direction.append(file_path)
        return self.sort_files(files=same_direction)

    def get_total_size(self, files: List[Path]) -> int:
        total_size = 0
        for file in files:
            total_size += file.stat().st_size
        return total_size

    def concatenate_same_read_direction(self, reads: List[Path], output: Path) -> None:
        with open(output, "wb") as write_file_obj:
            for file in reads:
                with open(file, "rb") as file_descriptor:
                    shutil.copyfileobj(file_descriptor, write_file_obj)

    def remove_files(self, reads: List[Path]) -> None:
        for file in reads:
            LOG.info("Removing file: %s", file)
            file.unlink()

    def get_all_samples_from_ticket(self, ticket: str) -> list:
        all_samples = []
        cases: List[models.Family] = self.get_all_cases_from_ticket(ticket=ticket)
        for case in cases:
            for link_obj in case.links:
                all_samples.append(link_obj.sample.name)
        return all_samples

    def report_missing_samples(self, ticket: str, dry_run: bool) -> None:
        customer_inbox: Path = self.get_inbox_path(ticket=ticket)
        missing_samples = []
        all_samples: list = self.get_all_samples_from_ticket(ticket=ticket)
        if not customer_inbox.exists() and dry_run:
            LOG.info("Dry run, will not search for missing data in: %s", customer_inbox)
            return
        if not customer_inbox.exists():
            LOG.info(
                "The path %s do not exist, no search for missing data will be done", customer_inbox
            )
            return
        for dir_path in customer_inbox.iterdir():
            if len(os.listdir(dir_path)) == 0 and os.path.basename(dir_path) in all_samples:
                missing_samples.append(os.path.basename(dir_path))
        if len(missing_samples) > 0:
            LOG.info("No data delivered for sample(s):")
            for sample in missing_samples:
                LOG.info(sample)
        else:
            LOG.info("Data has been delivered for all samples")

    def concatenate(self, ticket: str, dry_run: bool) -> None:
        customer_inbox: Path = self.get_inbox_path(ticket=ticket)
        date: datetime.datetime = self.generate_date_tag(ticket=ticket)
        if not customer_inbox.exists() and dry_run:
            LOG.info("Dry run, nothing will be concatenated in: %s", customer_inbox)
            return
        if not customer_inbox.exists():
            LOG.info("The path %s do not exist, nothing will be concatenated", customer_inbox)
            return
        for dir_path in customer_inbox.iterdir():
            if len(os.listdir(dir_path)) == 0:
                LOG.info("Empty folder found: %s", dir_path)
                continue
            if not dir_path.is_dir():
                continue
            for read_direction in [1, 2]:
                same_direction: List[Path] = self.get_current_read_direction(
                    dir_path=dir_path, read_direction=read_direction
                )
                total_size: int = self.get_total_size(files=same_direction)
                output: Path = self.generate_output_filename(
                    date=date, dir_path=dir_path, read_direction=read_direction
                )
                if dry_run:
                    for file in same_direction:
                        LOG.info(
                            "Dry run activated, %s will not be appended to %s" % (file, output)
                        )
                else:
                    LOG.info("Concatenating sample: %s", dir_path.name)
                    self.concatenate_same_read_direction(reads=same_direction, output=output)
                if dry_run:
                    continue
                concatenated_size = output.stat().st_size
                if total_size != concatenated_size:
                    raise CgError("WARNING data lost in concatenation")

                LOG.info(
                    "QC PASSED: Total size for files used in concatenation match the size of the concatenated file"
                )
                self.remove_files(reads=same_direction)

    def get_app_tag(self, samples: list) -> str:
        app_tag = samples[0].application_version.application.tag
        return app_tag

    def check_if_concatenation_is_needed(self, ticket: str) -> bool:
        cases: List[models.Family] = self.get_all_cases_from_ticket(ticket=ticket)
        case_id = cases[0].internal_id
        case_obj = self.status_db.family(case_id)
        samples: List[models.Sample] = [link.sample for link in case_obj.links]
        app_tag = self.get_app_tag(samples=samples)
        for prefix in PREFIX_TO_CONCATENATE:
            if app_tag.startswith(prefix):
                LOG.info(
                    "Identified %s as application tag, i.e. the fastqs should be concatenated",
                    app_tag,
                )
                return True
        LOG.info(
            "The following application tag was identified: %s, concatenation will be skipped",
            app_tag,
        )
        return False
