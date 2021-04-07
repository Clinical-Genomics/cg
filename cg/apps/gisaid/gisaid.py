"""Interactions with the gisaid cli upload"""

import logging
from pathlib import Path
from typing import List

from cg.store import models
from .constants import HEADERS
from ...utils import Process

LOG = logging.getLogger(__name__)

import csv


class GisaidAPI:
    """Interface with Gisaid cli uppload"""

    def __init__(self, case_obj: models.Family, config:dict):
        self.case_obj = case_obj
        self.dry_run = False
        self.gisaid_config = config["gisaid"]["config_path"]
        self.gisaid_binary = config["gisaid"]["binary_path"]
        self.process = Process(binary=self.vogue_binary, config=self.vogue_config)

    def set_dry_run(self, dry_run: bool) -> None:
        """Set the dry run state"""
        self.dry_run = dry_run

    def get_sample_row(self, sample: models.Sample):
        sample_row = []
        return sample_row

    def build_batch_csv(self, samples: List[models.Sample], family_id: str) -> Path:
        samples =
        file_name = "jkhkj"
        file = Path(file_name)
        with open(file_name, "w", newline="\n") as gisaid_csv:
            wr = csv.writer(gisaid_csv, delimiter=",")
            wr.writerow(HEADERS)
            for sample in samples:
                sample_row: list = self.get_sample_row(sample)
                if sample_row:
                    wr.writerow(sample_row)
        return file

    def uppload(self, csv_file_path: str, fasta_file_path: str) -> None:
        """Load genotype data from a dict."""

        load_call = ["CoV", "upload", "--csv",csv_file_path,"--fasta", fasta_file_path]
        self.process.run_command(parameters=load_call)

        # Execute command and print its stdout+stderr as it executes
        for line in self.process.stderr_lines():
            LOG.info("gisaid output: %s", line)

    def __str__(self):
        return f"GisaidAPI(dry_run: {self.dry_run})"
