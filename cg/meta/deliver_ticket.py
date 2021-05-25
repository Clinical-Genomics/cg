"""Module for deliver and rsync customer inbox on hasta to customer inbox on caesar"""
import logging
import os
import re
import subprocess
from pathlib import Path
import shutil
from typing import List

from cg.exc import CgError
from cg.meta.meta import MetaAPI
from cg.models.cg_config import CGConfig
from cg.store import models


LOG = logging.getLogger(__name__)
PREFIX_TO_CONCATENATE = ["MWG", "MWL", "MWM", "MWR", "MWX"]


class DeliverTicketAPI(MetaAPI):
    def __init__(self, config: CGConfig):
        super().__init__(config)
        self.delivery_path: str = config.delivery_path

    def get_all_cases_from_ticket(self, ticket_id: int) -> List[models.Family]:
        cases: List[models.Family] = self.status_db.get_cases_from_ticket(ticket_id=ticket_id).all()
        return cases

    def get_inbox_path(self, ticket_id: int) -> Path:
        cases: List[models.Family] = self.get_all_cases_from_ticket(ticket_id=ticket_id)
        if not cases:
            LOG.warning("The customer id was not identified since no cases for ticket_id %s was found", ticket_id)
            raise CgError()

        customer_id: str = cases[0].customer.internal_id
        customer_inbox = Path(self.delivery_path, customer_id, "inbox", str(ticket_id))
        return customer_inbox

    def check_if_upload_is_needed(self, ticket_id: int) -> bool:
        is_upload_needed = True
        customer_inbox = self.get_inbox_path(ticket_id=ticket_id)
        LOG.info("Checking if path exist: %s", customer_inbox)
        if os.path.exists(customer_inbox):
            LOG.info("Could find path: %s", customer_inbox)
            is_upload_needed = False
        else:
            LOG.info("Could not find path: %s", customer_inbox)
        return is_upload_needed

    def generate_date_tag(self, ticket_id: int) -> str:
        cases = self.get_all_cases_from_ticket(ticket_id=ticket_id)
        date = str(cases[0].ordered_at)
        split_date = date.split(" ")
        return split_date[0]

    def generate_output_filename(self, dir_path: str, date: str, dir_name: str, read_direction: int) -> str:
        if date:
            output = (
                    dir_path
                    + "/"
                    + date
                    + "_"
                    + dir_name
                    + "_"
                    + str(read_direction)
                    + ".fastq.gz"
            )
        else:
            output = dir_path + "/" + dir_name + "_" + str(read_direction) + ".fastq.gz"
        return output

    def concatenate(self, ticket_id: int, dry_run: bool) -> None:
        customer_inbox = self.get_inbox_path(ticket_id=ticket_id)
        if not os.path.exists(customer_inbox) and dry_run:
            LOG.info("Dry run, nothing will be concatenated in: %s", customer_inbox)
            return
        if not os.path.exists(customer_inbox):
            LOG.info("Nothing to concatenate in: %s", customer_inbox)
            return
        for dir_name in os.listdir(customer_inbox):
            dir_path = os.path.join(customer_inbox, dir_name)
            if len(os.listdir(dir_path)) == 0:
                LOG.info("Empty folder found: %s", dir_path)
                continue
            if not os.path.isdir(dir_path):
                continue
            for read_direction in [1, 2]:
                same_direction = []
                total_size = 0
                for file in os.listdir(dir_path):
                    abs_path_file = os.path.join(dir_path, file)
                    direction_string = ".+_R" + str(read_direction) + "_[0-9]+.fastq.gz"
                    direction_pattern = re.compile(direction_string)
                    if direction_pattern.match(abs_path_file):
                        same_direction.append(os.path.abspath(abs_path_file))
                        total_size = total_size + Path(abs_path_file).stat().st_size
                same_direction.sort()
                date = self.generate_date_tag(ticket_id=ticket_id)
                output = self.generate_output_filename(dir_path=dir_path, date=date, dir_name=dir_name, read_direction=read_direction)
                if dry_run:
                    for file in same_direction:
                        LOG.info(
                            "Dry run activated, %s will not be appended to %s" % (file, output)
                        )
                else:
                    with open(output, "wb") as write_file_obj:
                        for file in same_direction:
                            with open(file, "rb") as file_descriptor:
                                shutil.copyfileobj(file_descriptor, write_file_obj)
                if not dry_run:
                    concatenated_size = Path(output).stat().st_size
                    if total_size == concatenated_size:
                        LOG.info(
                            "QC PASSED: Total size for files used in concatenation match the size of the concatenated file"
                        )
                        for file in same_direction:
                            inode_check_cmd = "stat -c %h " + file
                            n_inodes = subprocess.getoutput(inode_check_cmd)
                            if int(n_inodes) > 1:
                                LOG.info("Removing file: %s" % (file))
                                os.remove(file)
                            else:
                                LOG.warning(
                                    "WARNING %s only got 1 inode, file will not be removed" % (file)
                                )
                    else:
                        LOG.warning("WARNING data lost in concatenation")

    def get_app_tag(self, samples: list) -> str:
        app_tag = samples[0].application_version.application.tag
        return app_tag

    def check_if_concatenation_is_needed(self, ticket_id: int) -> bool:
        cases = self.get_all_cases_from_ticket(ticket_id=ticket_id)
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
