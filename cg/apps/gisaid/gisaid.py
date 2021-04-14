"""Interactions with the gisaid cli upload"""

import logging
from pathlib import Path
from typing import List

from cg.store import models
from cg.meta.workflow.fastq import FastqHandler
from cg.utils import Process
from .models import GisaidSample, UpploadFiles
from housekeeper.store import models as hk_models
from cg.meta.meta import MetaAPI
import csv


LOG = logging.getLogger(__name__)


class GisaidAPI(MetaAPI):
    """Interface with Gisaid cli uppload"""

    def __init__(self, config: dict):
        super().__init__(config)
        self.gisaid_submitter = config["gisaid"]["submitter"]
        self.gisaid_binary = config["gisaid"]["binary_path"]
        self.process = Process(binary=self.gisaid_binary)
        self.fastq_handler = FastqHandler()

    def get_headers(self) -> list:
        """Get GisaidSample keys as list."""

        return list(GisaidSample.schema().get("properties").keys())

    def get_sample_row(self, sample: models.Sample, family_id: str, fasta_header: str) -> List[str]:
        """Build row for a sample in the batch upload csv."""

        orig_lab: str = "Stockholm"  # sample.originating_lab
        collection_date: str = "2020-11-22"  # sample.collection_date str or date, we dont know yet
        gisaid_sample = GisaidSample(
            covv_virus_name=fasta_header,
            covv_subm_sample_id=sample.name,
            submitter=self.gisaid_submitter,
            fn=f"{family_id}.fasta",
            covv_collection_date=collection_date,
            lab=orig_lab,
        )
        return [gisaid_sample.dict().get(header) for header in self.get_headers()]

    def build_batch_csv(self, family_id: str) -> str:
        """Build batch upload csv."""

        file_name: str = f"{family_id}.csv"
        file: Path = Path(file_name)
        with open(file_name, "w", newline="\n") as gisaid_csv:
            wr = csv.writer(gisaid_csv, delimiter=",")
            headers: List[str] = self.get_headers()
            wr.writerow(headers)
            sample_rows: List[List[str]] = self.get_sample_rows(family_id=family_id)
            wr.writerows(sample_rows)

        return str(file.absolute())

    def get_fasta_file(self, sample_id: str, hk_version_id: str) -> str:

        fasta_file: hk_models.File = self.housekeeper_api.files(  # not sure about this type!!!
            version=hk_version_id, tags=["consensus", sample_id]
        ).first()
        return fasta_file.full_path

    def get_sample_rows(self, family_id: str) -> List[List[str]]:
        """Build sample row list for gisad csv file"""

        samples: List[models.Sample] = self.status_db.get_sequenced_samples(family_id=family_id)
        hk_version: hk_models.Version = self.housekeeper_api.last_version(bundle=family_id)

        sample_rows = []
        for sample in samples:
            fasta_file: str = self.get_fasta_file(
                sample_id=sample.internal_id, hk_version_id=hk_version.id
            )
            header: str = self.fastq_handler.get_header(fasta_file)
            sample_row: List[str] = self.get_sample_row(
                sample=sample, family_id=family_id, fasta_header=header
            )
            sample_rows.append(sample_row)

        return sample_rows

    def build_batch_fasta(self, family_id: str) -> str:
        """Fetch a fasta files form house keeper for batch upload to gisaid"""

        samples: List[models.Sample] = self.status_db.get_sequenced_samples(family_id=family_id)
        hk_version: hk_models.Version = self.housekeeper_api.last_version(bundle=family_id)

        fasta_files = []
        for sample in samples:
            fasta_file: str = self.get_fasta_file(
                sample_id=sample.internal_id, hk_version_id=hk_version.id
            )
            fasta_files.append(fasta_file)

        file_name: str = f"{family_id}.fasta"
        self.fastq_handler.concatenate(files=fasta_files, concat_file=file_name)
        return file_name

    def upload(self, csv_file: str, fasta_file: str) -> None:
        """Load batch data to GISAID using the gisiad cli."""

        load_call: list = ["CoV", "upload", "--csv", csv_file, "--fasta", fasta_file]
        self.process.run_command(parameters=load_call)

        # Execute command and print its stdout+stderr as it executes
        for line in self.process.stderr_lines():
            LOG.info("gisaid output: %s", line)

    def __str__(self):
        return f"GisaidAPI(dry_run: {self.dry_run})"
