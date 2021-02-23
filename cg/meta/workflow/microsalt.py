""" API to manage Microsalt Analyses
    Organism - Fallback based on reference, ‘Other species’ and ‘Comment’. Default to “Unset”.
    Priority = Default to empty string. Weird response. Typically “standard” or “research”.
    Reference = Defaults to “None”
    Method: Outputted as “1273:23”. Defaults to “Not in LIMS”
    Date: Returns latest == most recent date. Outputted as DT object “YYYY MM DD”. Defaults to
    datetime.min"""

import logging
import os
import re
from datetime import datetime
from pathlib import Path
from subprocess import CalledProcessError
from typing import Any, Dict, List, Optional

import click

from cg.apps.balsamic.fastq import FastqHandler, MicrosaltFastqHandler
from cg.constants import Pipeline
from cg.exc import CgDataError
from cg.meta.workflow.analysis import AnalysisAPI
from cg.store import models
from cg.utils import Process

LOG = logging.getLogger(__name__)


class MicrosaltAnalysisAPI(AnalysisAPI):
    """API to manage Microsalt Analyses"""

    def __init__(self, config: dict, pipeline: Pipeline = Pipeline.MICROSALT):

        super().__init__(pipeline, config)
        self.root_dir = config["microsalt"]["root"]
        self.queries_path = config["microsalt"]["queries_path"]

    @property
    def threshold_reads(self):
        return False

    @property
    def fastq_handler(self):
        return MicrosaltFastqHandler

    def __configure_process_call(self, config: dict) -> Process:
        return Process(
            binary=config["microsalt"]["binary_path"], environment=config["microsalt"]["conda_env"]
        )

    def get_case_fastq_path(self, case_id: str) -> Path:
        return Path(self.root_dir, "fastq", case_id)

    def get_config_path(self, filename: str) -> Path:
        return Path(self.queries_path, filename).with_suffix(".json")

    def get_trailblazer_config_path(self, case_id: str) -> Path:
        case_obj: models.Family = self.status_db.family(case_id)
        order_id = case_obj.name
        return Path(
            self.root_dir, "results", "reports", "trailblazer", f"{order_id}_slurm_ids.yaml"
        )

    def get_deliverables_file_path(self, case_id: str) -> Path:
        """Returns a path where the microSALT deliverables file for the order_id should be
        located"""
        case_obj: models.Family = self.status_db.family(case_id)
        order_id = case_obj.name
        deliverables_file_path = Path(
            self.root_dir,
            "results",
            "reports",
            "deliverables",
            f"{order_id}_deliverables.yaml",
        )
        if deliverables_file_path.exists():
            LOG.info("Found deliverables file %s", deliverables_file_path)
        return deliverables_file_path

    def get_sample_fastq_destination_dir(self, case_obj: models.Family, sample_obj: models.Sample):
        fastq_dir = Path(self.get_case_fastq_path(case_id=case_obj.internal_id), sample_id)

    def link_fastq_files(
        self, case_id: str, sample_id: Optional[str], dry_run: bool = False
    ) -> None:
        case_obj = self.status_db.family(case_id)
        samples: List[models.Sample] = self.get_samples(case_id=case_id, sample_id=sample_id)
        for sample_obj in samples:
            self.link_fastq_files_for_sample(case_obj=case_obj, sample_obj=sample_obj)

    def link_samples(self, case_id: str, sample_id: Optional[str] = None) -> None:

        case_dir: Path = self.get_case_fastq_path(case_id=case_id)
        case_dir.mkdir(parents=True, exist_ok=True)

        samples: List[models.Sample] = self.get_samples(case_id=case_id, sample_id=sample_id)

        for sample in samples:
            LOG.info("%s: link FASTQ files", sample.internal_id)
            self.link_fastq(
                case_dir,
                sample_id=sample.internal_id,
            )

    def link_fastq(self, case_dir: Path, sample_id: str) -> None:
        """Link FASTQ files for a sample."""

        fastq_dir = Path(case_dir, sample_id)
        fastq_dir.mkdir(exist_ok=True, parents=True)

        file_objs = self.housekeeper_api.files(bundle=sample_id, tags=["fastq"])
        files = []

        for file_obj in file_objs:
            # figure out flowcell name from header
            data = FastqHandler.parse_file_data(file_obj.full_path)
            files.append(data)

        for fastq_data in files:
            original_fastq_path = Path(fastq_data["path"])
            linked_fastq_name = FastqHandler.create(
                lane=fastq_data["lane"],
                flowcell=fastq_data["flowcell"],
                sample=sample_id,
                read=fastq_data["read"],
                more={"undetermined": fastq_data["undetermined"]},
            )
            linked_fastq_path = Path(fastq_dir, linked_fastq_name)

            if not linked_fastq_path.exists():
                LOG.info("Linking: %s -> %s", original_fastq_path, linked_fastq_path)
                linked_fastq_path.symlink_to(original_fastq_path)
            else:
                LOG.debug("Destination path already exists: %s, skipping", linked_fastq_path)

    def get_samples(self, case_id: str, sample_id: Optional[str] = None) -> List[models.Sample]:
        """Returns a list of samples to configure
        If sample_id is specified, will return a list with only this sample_id.
        Otherwise, returns all samples in given case"""
        if sample_id:
            return [
                self.status_db.query(models.Sample)
                .filter(models.Sample.internal_id == sample_id)
                .first()
            ]

        case_obj: models.Family = self.status_db.family(case_id)
        return [link.sample for link in case_obj.links]

    def get_lims_comment(self, sample_id: str) -> str:
        """ Returns the comment associated with a sample stored in lims"""
        comment = self.lims_api.get_sample_comment(sample_id) or ""
        if re.match(r"\w{4}\d{2,3}", comment):
            return comment

        return ""

    def get_organism(self, sample_obj: models.Sample) -> str:
        """Organism
        - Fallback based on reference, ‘Other species’ and ‘Comment’.
        Default to "Unset"."""

        if not sample_obj.organism:
            raise CgDataError(f"Organism missing on Sample")

        organism = sample_obj.organism.internal_id.strip()
        comment = self.get_lims_comment(sample_id=sample_obj.internal_id)
        has_comment = bool(comment)

        if "gonorrhoeae" in organism:
            organism = "Neisseria spp."
        elif "Cutibacterium acnes" in organism:
            organism = "Propionibacterium acnes"

        if organism == "VRE":
            reference = sample_obj.organism.reference_genome
            if reference == "NC_017960.1":
                organism = "Enterococcus faecium"
            elif reference == "NC_004668.1":
                organism = "Enterococcus faecalis"
            elif has_comment:
                organism = comment

        return organism

    def get_parameters(self, sample_obj: models.Sample) -> Dict[str, str]:
        """Fill a dict with case config information for one sample """

        sample_id = sample_obj.internal_id
        method_library_prep = self.lims_api.get_prep_method(sample_id)
        if method_library_prep:
            method_library_prep, _ = method_library_prep.split(" ", 1)
        method_sequencing = self.lims_api.get_sequencing_method(sample_id)
        if method_sequencing:
            method_sequencing, _ = method_sequencing.split(" ", 1)
        priority = "research" if sample_obj.priority == 0 else "standard"

        return {
            "CG_ID_project": self.get_project(sample_id),
            "Customer_ID_project": sample_obj.ticket_number,
            "CG_ID_sample": sample_obj.internal_id,
            "Customer_ID_sample": sample_obj.name,
            "organism": self.get_organism(sample_obj),
            "priority": priority,
            "reference": sample_obj.reference_genome,
            "Customer_ID": sample_obj.customer.internal_id,
            "application_tag": sample_obj.application_version.application.tag,
            "date_arrival": str(sample_obj.received_at or datetime.min),
            "date_sequencing": str(sample_obj.sequenced_at or datetime.min),
            "date_libprep": str(sample_obj.prepared_at or datetime.min),
            "method_libprep": method_library_prep or "Not in LIMS",
            "method_sequencing": method_sequencing or "Not in LIMS",
        }

    def get_project(self, sample_id: str) -> str:
        """Get LIMS project for a sample"""
        return self.lims_api.get_sample_project(sample_id)

    def get_deliverables_to_store(self) -> list:
        """Retrieve a list of microbial deliverables files for orders where analysis finished
        successfully, and are ready to be stored in Housekeeper"""

        return self.status_db.cases_to_store(pipeline=self.pipeline)

    def resolve_case_sample_id(
        self, sample: bool, ticket: bool, unique_id: Any
    ) -> (str, Optional[str]):
        """Resolve case_id and sample_id w based on input arguments. """
        if ticket and sample:
            LOG.error("Flags -t and -s are mutually exclusive!")
            raise click.Abort

        if ticket:
            case_id, sample_id = self.get_case_id_from_ticket(unique_id)

        elif sample:
            case_id, sample_id = self.get_case_id_from_sample(unique_id)

        else:
            case_id, sample_id = self.get_case_id_from_case(unique_id)

        return case_id, sample_id

    def get_case_id_from_ticket(self, unique_id: str) -> (str, None):
        """If ticked is provided as argument, finds the corresponding case_id and returns it.
        Since sample_id is not specified, nothing is returned as sample_id"""
        case_obj: models.Family = self.status_db.find_family_by_name(unique_id)
        if not case_obj:
            LOG.error("No case found for ticket number:  %s", unique_id)
            raise click.Abort
        case_id = case_obj.internal_id
        return case_id, None

    def get_case_id_from_sample(self, unique_id: str) -> (str, str):
        """If sample is specified, finds the corresponding case_id to which this sample belongs.
        The case_id is to be used for identifying the appropriate path to link fastq files and store the analysis output
        """
        sample_obj: models.Sample = (
            self.status_db.query(models.Sample)
            .filter(models.Sample.internal_id == unique_id)
            .first()
        )
        if not sample_obj:
            LOG.error("No sample found with id: %s", unique_id)
            raise click.Abort
        case_id = sample_obj.links[0].family.internal_id
        sample_id = sample_obj.internal_id
        return case_id, sample_id

    def get_case_id_from_case(self, unique_id: str) -> (str, None):
        """If case_id is specified, validates the presence of case_id in database and returns it"""
        case_obj: models.Family = self.status_db.family(unique_id)
        if not case_obj:
            LOG.error("No case found with the id:  %s", unique_id)
            raise click.Abort
        case_id = case_obj.internal_id
        return case_id, None

    def get_bundle_created_date(self, case_id: str) -> datetime.date:
        """ Get date from deliverables path using date created metadata """
        return datetime.fromtimestamp(
            int(os.path.getctime(self.get_deliverables_file_path(case_id=case_id)))
        )

    def get_pipeline_version(self, case_id: str) -> str:
        try:
            self.process.run_command(["--version"])
            return list(self.process.stdout_lines())[0].split()[-1]
        except CalledProcessError:
            LOG.warning("Could not retrieve microsalt version!")
            return "0.0.0"
