"""Module for deliver and rsync customer inbox on hasta to customer inbox on caesar"""
import logging
import os
import re
import subprocess
from pathlib import Path
import shutil
from typing import List

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.exc import CgError
from cg.meta.meta import MetaAPI
from cg.models.cg_config import CGConfig
from cg.store import models
from cg.store import Store


LOG = logging.getLogger(__name__)
PREFIX_TO_CONCATENATE = ["MWG", "MWL", "MWM", "MWR", "MWX"]


class DeliverTicketAPI(MetaAPI):
    def __init__(self, config: CGConfig, store: Store, hk_api: HousekeeperAPI):
        super().__init__(config)
        self.delivery_path: str = config.delivery_path
        self.hk_api = hk_api
        self.store = store

    def get_inbox_path(self, ticket_id: int) -> str:
        cases: List[models.Family] = self.status_db.get_cases_from_ticket(ticket_id=ticket_id).all()
        if not cases:
            LOG.warning("Could not find any cases for ticket_id %s", ticket_id)
            raise CgError()

        customer_id: str = cases[0].customer.internal_id
        customer_inbox: str = (
            Path(self.delivery_path, customer_id, "inbox", str(ticket_id)).as_posix() + "/"
        )
        return customer_inbox

    def check_if_upload_is_needed(self, ticket_id: int) -> bool:
        customer_inbox = self.get_inbox_path(ticket_id=ticket_id)
        return os.path.exists(customer_inbox)

    def generate_date_tag(self, ticket_id: int) -> str:
        cases: List[models.Family] = self.status_db.get_cases_from_ticket(ticket_id=ticket_id).all()
        date = str(cases[0].ordered_at)
        split_date = date.split(" ")
        return split_date[0]

    def concatenate(self, ticket_id: int) -> None:
        customer_inbox = self.get_inbox_path(ticket_id=ticket_id)
        for dir_name in os.listdir(customer_inbox):
            dir_path = os.path.join(customer_inbox, dir_name)
            if len(os.listdir(dir_path)) == 0:
                LOG.info("Empty folder found: %s" % (dir_path))
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
                with open(output, "wb") as write_file_obj:
                    for file in same_direction:
                        with open(file, "rb") as file_descriptor:
                            shutil.copyfileobj(file_descriptor, write_file_obj)
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

    def check_is_concatenation_is_needed(self, ticket_id: int) -> bool:
        cases: List[models.Family] = self.status_db.get_cases_from_ticket(ticket_id=ticket_id).all()
        case_id = cases[0].internal_id
        version_obj = self.hk_api.last_version(case_id)
        app_tag = version_obj.application.tag
        for prefix in PREFIX_TO_CONCATENATE:
            if app_tag.startswith(prefix):
                return True
        return False
