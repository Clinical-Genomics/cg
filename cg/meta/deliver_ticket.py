"""Module for deliver and rsync customer inbox on hasta to customer inbox on caesar"""
import logging
import os
import re
import subprocess
from pathlib import Path
from typing import List

from cg.exc import CgError
from cg.meta.meta import MetaAPI
from cg.models.cg_config import CGConfig
from cg.store import models
from cg.store import Store
from cg.utils import Process


LOG = logging.getLogger(__name__)


class DeliverTicketAPI(MetaAPI):
    def __init__(self, config: CGConfig, store: Store):
        super().__init__(config)
        self.delivery_path: str = config.delivery_path
        self.store = store
        self._process = None

    @property
    def process(self):
        if not self._process:
            self._process = Process("cat")
        return self._process

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

    def generate_date_tag(self, ticket_id: int) -> int:
        cases: List[models.Family] = self.status_db.get_cases_from_ticket(ticket_id=ticket_id).all()
        date = cases[0].ordered_at
        return date

    def concatenate(self, ticket_id: int, dry_run: bool) -> None:
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
                input_files = ""
                for i in range(len(same_direction)):
                    if input_files == "":
                        input_files = same_direction[i]
                    else:
                        input_files = input_files + " " + same_direction[i]
                date = self.generate_date_tag(ticket_id=ticket_id)
                if date:
                    output = (
                        dir_path
                        + "/"
                        + str(date)
                        + "_"
                        + dir_name
                        + "_"
                        + str(read_direction)
                        + ".fastq.gz"
                    )
                else:
                    output = dir_path + "/" + dir_name + "_" + str(read_direction) + ".fastq.gz"
                parameters: List[str] = [input_files, ">", output]
                self.process.run_command(parameters=parameters, dry_run=dry_run)
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
