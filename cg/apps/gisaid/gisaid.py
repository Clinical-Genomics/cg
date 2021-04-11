"""Interactions with the gisaid cli upload"""

import logging
from pathlib import Path
from typing import List

from cg.store import models
from .constants import HEADERS
from ...meta.workflow.fastq import FastqHandler
from ...store.models import Family
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
        self.fastq_handler = FastqHandler()

    def get_sample_row(self, sample: models.Sample, family_id: str, fasta_header: str):
        """Build row for a sample in the batch upload csv."""

        orig_lab = "Stockholm"  # sample.originating_lab
        collection_date = "201122"  # sample.collection_date
        gisaid_sample = GisaidSample(
            covv_virus_name=fasta_header,
            covv_subm_sample_id=sample.name,
            submitter="i.sylvin",
            fn=f"{family_id}.fasta",
            covv_collection_date=collection_date,
            lab=orig_lab,
        )
        return [gisaid_sample.dict().get(header) for header in HEADERS]

    def get_sample_rows(self, family_id: str) -> List[List[str]]:
        """"""

        samples: List[models.Sample] = self.status_db.get_samples_by_family_id(family_id)
        ## Add filer to get only samples that have been seuenced.
        hk_version = self.housekeeper_api.last_version(bundle=family_id)
        sample_rows = []
        for sample in samples:
            if not sample.sequenced_at:
                continue
            # fasta_file = Path("/Users/maya.brandi/opt/cg/f1.fasta")
            fasta_file = self.housekeeper_api.files(
                version=hk_version.id, tags=["consensus", sample.internal_id]
            ).first()
            header = self.fastq_handler.get_header(fasta_file)
            sample_row: list = self.get_sample_row(
                sample=sample, family_id=family_id, fasta_header=header
            )
            if sample_row:
                sample_rows.append(sample_row)
        return sample_rows

    def build_batch_csv(self, family_id: str) -> str:
        # validate that family id fins i status
        """Build batch upload csv."""

        file_name = f"{family_id}.csv"
        file = Path(file_name)
        with open(file_name, "w", newline="\n") as gisaid_csv:
            wr = csv.writer(gisaid_csv, delimiter=",")
            wr.writerow(HEADERS)
            sample_rows: List[List[str]] = self.get_sample_rows(family_id=family_id)
            wr.writerows(sample_rows)

        return str(file.absolute())

    def build_batch_fasta(self, family_id: str) -> Path:
        """Fetch a fasta file form house keeper for batch upload to gisaid"""

        hk_version = self.housekeeper_api.last_version(bundle=family_id)
        # should get files per sample only with sequenced at
        hk_files: list = self.housekeeper_api.files(version=hk_version.id, tags=["consensus"]).all()
        fasta_files = [file.full_path for file in hk_files]

        file_name = f"{family_id}.fasta"
        self.fastq_handler.concatenate(files=fasta_files, concat_file=file_name)
        return file_name

    def files(self, family_id: str) -> UpploadFiles:
        """get csv file and fasta file for batch upload to GISAID."""

        return UpploadFiles(
            csv_file=self.build_batch_csv(family_id=family_id),
            fasta_file=self.build_batch_fasta(family_id=family_id),
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
