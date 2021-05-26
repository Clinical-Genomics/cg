"""Interactions with the gisaid cli upload"""

import logging
from pathlib import Path
from typing import List, Optional

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
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
        self.lims_api: LimsAPI = config.lims_api
        self.status_db: Store = config.status_db
        self.gisaid_submitter: str = config.gisaid.submitter
        self.gisaid_binary: str = config.gisaid.binary_path
        self.process = Process(binary=self.gisaid_binary)

    def get_new_header(self, samples: List[GisaidSample], old_header: str) -> str:
        for sample in samples:
            sample_id = sample.covv_subm_sample_id
            if old_header.find(sample_id) != -1:
                return f">{sample.covv_virus_name}\n"
        raise FastaSequenceMissingError

    def get_gisaid_fasta(
        self, gsaid_samples: List[GisaidSample], family_id: str
    ) -> List[FastaFile]:
        """Fetch a fasta files form house keeper for batch upload to gisaid"""

        hk_version: hk_models.Version = self.housekeeper_api.last_version(bundle=family_id)
        if not hk_version:
            LOG.info("Family ID: %s not found in housekeeper", family_id)
            raise HousekeeperVersionMissingError
        fasta_file: str = self.housekeeper_api.files(
            version=hk_version.id, tags=["consensus"]
        ).first()
        gisaid_delivery_fasta = []
        with open("/Users/maya.brandi/opt/395698.consensus.fa") as handle:
            fasta_lines = handle.readlines()
            for line in fasta_lines:
                if line[0] == ">":
                    gisaid_delivery_fasta.append(
                        self.get_new_header(old_header=line, samples=gsaid_samples)
                    )
                else:
                    gisaid_delivery_fasta.append(line)

        return gisaid_delivery_fasta

    def build_gisaid_fasta(
        self, gsaid_samples: List[GisaidSample], file_name: str, family_id: str
    ) -> Path:
        """Concatenates a list of consensus fastq objects"""

        file: Path = Path(file_name)
        fasta_lines: List[str] = self.get_gisaid_fasta(
            gsaid_samples=gsaid_samples, family_id=family_id
        )
        with open(file, "w") as write_file_obj:
            write_file_obj.writelines(fasta_lines)
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
            sample_id: str = sample.internal_id
            gisaid_sample = GisaidSample(
                family_id=family_id,
                cg_lims_id=sample_id,
                covv_subm_sample_id=sample.name,
                submitter=self.gisaid_submitter,
                fn=f"{family_id}.fasta",
                covv_collection_date=self.lims_api.get_sample_attribute(
                    lims_id=sample_id, key="collection_date"
                ),
                region=self.lims_api.get_sample_attribute(lims_id=sample_id, key="region"),
                region_code=self.lims_api.get_sample_attribute(
                    lims_id=sample_id, key="region_code"
                ),
                covv_orig_lab=self.lims_api.get_sample_attribute(
                    lims_id=sample_id, key="original_lab"
                ),
                covv_orig_lab_addr=self.lims_api.get_sample_attribute(
                    lims_id=sample_id, key="original_lab_address"
                ),
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
