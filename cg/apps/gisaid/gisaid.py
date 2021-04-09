"""Interactions with the gisaid cli upload"""

import logging
from pathlib import Path
from typing import List

from sqlalchemy.orm import Query

from cg.store import models
from .constants import HEADERS
from ...meta.workflow.fastq import FastqHandler
from ...utils import Process
from .models import GisaidSample, UpploadFiles

from cg.meta.meta import MetaAPI

LOG = logging.getLogger(__name__)

import csv


class GisaidAPI(MetaAPI):
    """Interface with Gisaid cli uppload"""

    def __init__(self, config: dict):
        super().__init__(config)
        # self.gisaid_config = config["gisaid"]["config_path"]
        self.gisaid_binary = config["gisaid"]["binary_path"]
        self.process = Process(binary=self.gisaid_binary)

    def get_sample_row(self, sample: models.Sample, family_id: str):
        """Build row for a sample in the batch upload csv."""

        orig_lab = "Stockholm"  # sample.originating_lab
        collection_date = "201122"  # sample.collection_date
        gisaid_sample = GisaidSample(
            covv_subm_sample_id=sample.name,
            submitter="i.sylvin",
            fn=f"{family_id}.fasta",
            covv_collection_date=collection_date,
            lab=orig_lab,
        )
        return [gisaid_sample.dict().get(header) for header in HEADERS]

    def build_batch_csv(self, samples: List[models.Sample], family_id: str) -> str:
        """Build batch upload csv."""

        file_name = f"{family_id}.csv"
        file = Path(file_name)
        with open(file_name, "w", newline="\n") as gisaid_csv:
            wr = csv.writer(gisaid_csv, delimiter=",")
            wr.writerow(HEADERS)
            for sample in samples:
                sample_row: list = self.get_sample_row(sample, family_id)
                if sample_row:
                    wr.writerow(sample_row)

        return str(file.absolute())

    def get_fasta_file(self, family_id: str) -> Path:
        """Fetch a fasta file form house keeper for batch upload to gisaid"""

        hk_version = self.housekeeper_api.last_version(bundle=family_id)
        hk_files: list = self.housekeeper_api.files(version=hk_version.id, tags=["consensus"]).all()
        fasta_files = [file.full_path for file in hk_files]
        #        fasta_files = [
        #            "/Users/maya.brandi/opt/cg/f1.fasta",
        #            "/Users/maya.brandi/opt/cg/f3.fasta",
        #            "/Users/maya.brandi/opt/cg/f2.fasta",
        #        ]

        fastq_handler = FastqHandler()
        file_name = f"{family_id}.fasta"
        fastq_handler.concatenate(files=fasta_files, concat_file=file_name)
        return file_name

    def files(self, samples: List[models.Sample], family_id: str) -> UpploadFiles:
        """Fetch csv file and fasta file for batch upload to GISAID."""

        return UpploadFiles(
            csv_file=self.build_batch_csv(samples=samples, family_id=family_id),
            fasta_file=self.get_fasta_file(family_id),
        )

    def upload(self, csv_file: str, fasta_file: str) -> None:
        """Load batch data to GISAID using the gisiad cli."""

        load_call = ["CoV", "upload", "--csv", csv_file, "--fasta", fasta_file]
        self.process.run_command(parameters=load_call)

        # Execute command and print its stdout+stderr as it executes
        for line in self.process.stderr_lines():
            LOG.info("gisaid output: %s", line)

    def __str__(self):
        return f"GisaidAPI(dry_run: {self.dry_run})"
