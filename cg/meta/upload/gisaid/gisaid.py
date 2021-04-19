"""Interactions with the gisaid cli upload"""

import logging
from pathlib import Path
from typing import List

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.models.cg_config import CGConfig
from cg.store import models, Store
from cg.utils import Process
from .constants import HEADERS
from .models import GisaidSample, FastaFile
from housekeeper.store import models as hk_models
import csv

from cg.exc import HousekeeperVersionMissingError, FastaSequenceMissingError

LOG = logging.getLogger(__name__)


class GisaidAPI:
    """Interface with Gisaid cli uppload"""

    def __init__(self, config: CGConfig):
        self.housekeeper_api: HousekeeperAPI = config.housekeeper_api
        self.status_db: Store = config.status_db
        self.gisaid_submitter: str = config.gisaid.submitter
        self.gisaid_binary: str = config.gisaid.binary_path
        self.process = Process(binary=self.gisaid_binary)

    def get_fasta_sequence(self, fastq_path: str) -> str:
        """Get header from fasta file. Assuming un zipped file"""

        with open(fastq_path) as handle:
            fasta_lines = handle.readlines()
            try:
                return fasta_lines[1].rstrip("\n")
            except:
                raise FastaSequenceMissingError

    def get_gisaid_fasta_objects(self, gsaid_samples: List[GisaidSample]) -> List[FastaFile]:
        """Fetch a fasta files form house keeper for batch upload to gisaid"""

        fasta_objects = []
        for sample in gsaid_samples:
            hk_version: hk_models.Version = self.housekeeper_api.last_version(
                bundle=sample.family_id
            )
            if not hk_version:
                LOG.info("Family ID: %s not found in hose keeper", sample.family_id)
                raise HousekeeperVersionMissingError
            fasta_file: str = self.housekeeper_api.files(
                version=hk_version.id, tags=["consensus", sample.cg_lims_id]
            ).first()
            fasta_sequence: str = self.get_fasta_sequence(fastq_path=fasta_file.full_path)
            fasta_obj = FastaFile(header=sample.covv_virus_name, sequence=fasta_sequence)
            fasta_objects.append(fasta_obj)
        return fasta_objects

    def build_gisaid_fasta(self, gsaid_samples: List[GisaidSample], file_name: str) -> Path:
        """Concatenates a list of consensus fastq objects"""

        file: Path = Path(file_name)
        fasta_objects: List[FastaFile] = self.get_gisaid_fasta_objects(gsaid_samples=gsaid_samples)
        with open(file, "w") as write_file_obj:
            for fasta_object in fasta_objects:
                write_file_obj.write(f">{fasta_object.header}\n")
                write_file_obj.write(f"{fasta_object.sequence}\n")
        return file

    def get_sample_row(self, gisaid_sample: GisaidSample) -> List[str]:
        """Build row for a sample in the batch upload csv."""

        sample_dict = gisaid_sample.dict()
        return [sample_dict.get(header, "") for header in HEADERS]

    def get_sample_rows(self, gsaid_samples: List[GisaidSample]) -> List[List[str]]:
        """Build sample row list for gisad csv file"""

        sample_rows = []
        for sample in gsaid_samples:
            sample_row: List[str] = self.get_sample_row(gisaid_sample=sample)
            sample_rows.append(sample_row)
        return sample_rows

    def build_gisaid_csv(self, gsaid_samples: List[GisaidSample], file_name: str) -> Path:
        """Build batch upload csv."""

        file: Path = Path(file_name)
        with open(file_name, "w", newline="\n") as gisaid_csv:
            wr = csv.writer(gisaid_csv, delimiter=",")
            wr.writerow(HEADERS)
            sample_rows: List[List[str]] = self.get_sample_rows(gsaid_samples=gsaid_samples)
            wr.writerows(sample_rows)

        return file

    def get_gsaid_samples(self, family_id: str) -> List[GisaidSample]:
        """Get list of Gisaid sample objects."""

        samples: List[models.Sample] = self.status_db.get_sequenced_samples(family_id=family_id)
        gisaid_samples = []
        for sample in samples:
            gisaid_sample = GisaidSample(
                family_id=family_id,
                cg_lims_id=sample.internal_id,
                covv_subm_sample_id=sample.name,
                submitter=self.gisaid_submitter,
                fn=f"{family_id}.fasta",
                covv_collection_date="2020-11-22",  # sample.collection_date
                lab="Stockholm",  # sample.originating_lab,
            )
            gisaid_samples.append(gisaid_sample)
        return gisaid_samples

    def upload(self, csv_file: Path, fasta_file: Path) -> None:
        """Load batch data to GISAID using the gisiad cli."""

        load_call: list = [
            "CoV",
            "upload",
            "--csv",
            str(csv_file.absolute()),
            "--fasta",
            str(fasta_file.absolute()),
        ]
        self.process.run_command(parameters=load_call)

        if self.process.stderr:
            LOG.info(f"gisaid stderr:\n{self.process.stderr}")
        if self.process.stdout:
            LOG.info(f"gisaid stdout:\n{self.process.stdout}")

    def __str__(self):
        return f"GisaidAPI(dry_run: {self.dry_run})"
