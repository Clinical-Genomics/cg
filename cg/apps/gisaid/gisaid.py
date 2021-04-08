"""Interactions with the gisaid cli upload"""

import logging
from pathlib import Path
from typing import List

from cg.store import models
from .constants import HEADERS
from ...utils import Process
from .models import GisaidSample

LOG = logging.getLogger(__name__)

import csv


class GisaidAPI:
    """Interface with Gisaid cli uppload"""

    def __init__(self, config: dict):
        self.dry_run = False
        self.gisaid_config = config["gisaid"]["config_path"]
        self.gisaid_binary = config["gisaid"]["binary_path"]
        self.process = Process(binary=self.gisaid_binary, config=self.gisaid_config)

    def set_dry_run(self, dry_run: bool) -> None:
        """Set the dry run state"""
        self.dry_run = dry_run

    def get_sample_row(self, sample: models.Sample, family_id: str):
        """Build row for a sample in the batch upload csv."""

        orig_lab = "Stockholm"  # sample.originating_lab
        collection_cate = "201122"  # sample.collection_date
        gisaid_sample = GisaidSample(
            covv_subm_sample_id=sample.name,
            submitter="maya",
            fn=family_id,
            covv_collection_date=collection_cate,
            lab=orig_lab,
        )
        print(gisaid_sample)
        return [gisaid_sample.dict().get(header) for header in HEADERS]

    def build_batch_csv(self, samples: List[models.Sample], family_id: str) -> str:
        """Build batch upload csv."""

        file_name = family_id
        file = Path(file_name)
        with open(file_name, "w", newline="\n") as gisaid_csv:
            wr = csv.writer(gisaid_csv, delimiter=",")
            wr.writerow(HEADERS)
            for sample in samples:
                sample_row: list = self.get_sample_row(sample, family_id)
                if sample_row:
                    wr.writerow(sample_row)

        return str(file.absolute())

    def upload(self, csv_file_path: str, fasta_file_path: str) -> None:
        """Load batch data to GISAID using the gisiad cli."""

        load_call = ["CoV", "upload", "--csv", csv_file_path, "--fasta", fasta_file_path]
        self.process.run_command(parameters=load_call)

        # Execute command and print its stdout+stderr as it executes
        for line in self.process.stderr_lines():
            LOG.info("gisaid output: %s", line)

    def __str__(self):
        return f"GisaidAPI(dry_run: {self.dry_run})"
