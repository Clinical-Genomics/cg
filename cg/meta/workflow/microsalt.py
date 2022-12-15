""" API to manage Microsalt Analyses
    Organism - Fallback based on reference, ‘Other species’ and ‘Comment’. Default to “Unset”.
    Priority = Default to empty string. Weird response. Typically “standard” or “research”.
    Reference = Defaults to “None”
    Method: Outputted as “1273:23”. Defaults to “Not in LIMS”
    Date: Returns latest == most recent date. Outputted as DT object “YYYY MM DD”. Defaults to
    datetime.min"""
import json
import logging
import os
import re
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from subprocess import CalledProcessError
from typing import Any, Dict, List, Optional, Tuple, Union
import glob

import click
from cg.constants import Pipeline
from cg.constants.constants import MicrosaltQC, MicrosaltAppTags
from cg.exc import CgDataError, CgError
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.fastq import MicrosaltFastqHandler
from cg.models.cg_config import CGConfig
from cg.store import models
from cg.store.models import Sample
from cg.utils import Process
from cg.constants import EXIT_FAIL, EXIT_SUCCESS
from cg.io.json import read_json, write_json

from cg.constants import Priority

LOG = logging.getLogger(__name__)


class MicrosaltAnalysisAPI(AnalysisAPI):
    """API to manage Microsalt Analyses"""

    def __init__(self, config: CGConfig, pipeline: Pipeline = Pipeline.MICROSALT):

        super().__init__(pipeline, config)
        self.root_dir = config.microsalt.root
        self.queries_path = config.microsalt.queries_path

    @property
    def threshold_reads(self):
        return False

    @property
    def fastq_handler(self):
        return MicrosaltFastqHandler

    @property
    def conda_binary(self) -> str:
        return self.config.microsalt.conda_binary

    @property
    def process(self) -> Process:
        if not self._process:
            self._process = Process(
                binary=self.config.microsalt.binary_path,
                conda_binary=f"{self.conda_binary}" if self.conda_binary else None,
                environment=self.config.microsalt.conda_env,
            )
        return self._process

    def get_case_path(self, case_id: str, cleaning: bool = True) -> List[Path]:
        """Returns all paths associated with the case."""
        case_obj: models.Family = self.status_db.family(case_id)
        lims_project: str = self.get_project(case_obj.links[0].sample.internal_id)

        if cleaning:
            # Get case and single sample analysis folders
            case_paths: List[Path] = [
                Path(path)
                for path in glob.glob(f"{self.root_dir}/results/{lims_project}*", recursive=True)
            ]
            self.verify_case_paths_age(case_paths, case_id)
        else:
            # Only get case folders
            case_paths: List[Path] = [
                Path(path)
                for path in glob.glob(f"{self.root_dir}/results/{lims_project}_*", recursive=True)
            ]

        return sorted(case_paths, key=os.path.getctime, reverse=True)

    def verify_case_paths_age(
        self, case_paths: List[Path], case_id: str, analysis_due_date: int = 21
    ) -> None:
        """Check file age for a microsalt case."""
        due_date: datetime = datetime.now() - timedelta(days=analysis_due_date)
        for case_path in case_paths:
            creation_date: datetime = datetime.fromtimestamp(os.path.getmtime(case_path))
            if creation_date > due_date:
                LOG.info(
                    f"All paths in {case_id} are not older than 21 days, skipping and moving on to the next case!"
                )
                raise FileNotFoundError(
                    f"All paths in {case_id} are not older than 21 days, skipping and moving on to the next case!"
                )

    def clean_run_dir(self, case_id: str, yes: bool, case_path: Union[List[Path], Path]) -> int:
        """Remove workflow run directories for a MicroSALT case."""

        if not case_path:
            LOG.info(
                f"There is no case paths for case {case_id}. Setting cleaned at to {datetime.now()}"
            )
            self.clean_analyses(case_id=case_id)
            return EXIT_SUCCESS

        for analysis_path in case_path:
            if yes or click.confirm(
                f"Are you sure you want to remove all files in {analysis_path}?"
            ):
                if analysis_path.is_symlink():
                    LOG.warning(
                        f"Will not automatically delete symlink: {analysis_path}, delete it manually",
                    )
                    return EXIT_FAIL

                shutil.rmtree(analysis_path, ignore_errors=True)
                LOG.info(f"Cleaned {analysis_path}")

        self.clean_analyses(case_id=case_id)
        return EXIT_SUCCESS

    def get_case_fastq_path(self, case_id: str) -> Path:
        """Get fastq paths for a case."""
        return Path(self.root_dir, "fastq", case_id)

    def get_config_path(self, filename: str) -> Path:
        return Path(self.queries_path, filename).with_suffix(".json")

    def get_trailblazer_config_path(self, case_id: str) -> Path:
        """Get trailblazer config path."""
        case_obj: models.Family = self.status_db.family(case_id)
        sample_obj: models.Sample = case_obj.links[0].sample
        project_id: str = self.get_project(sample_obj.internal_id)
        return Path(
            self.root_dir, "results", "reports", "trailblazer", f"{project_id}_slurm_ids.yaml"
        )

    def get_deliverables_file_path(self, case_id: str) -> Path:
        """Returns a path where the microSALT deliverables file for the order_id should be
        located"""
        case_obj: models.Family = self.status_db.family(case_id)
        order_id: str = case_obj.name
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

    def get_sample_fastq_destination_dir(
        self, case_obj: models.Family, sample_obj: models.Sample
    ) -> Path:
        return Path(self.get_case_fastq_path(case_id=case_obj.internal_id), sample_obj.internal_id)

    def link_fastq_files(
        self, case_id: str, sample_id: Optional[str], dry_run: bool = False
    ) -> None:
        case_obj: models.Family = self.status_db.family(case_id)
        samples: List[models.Sample] = self.get_samples(case_id=case_id, sample_id=sample_id)
        for sample_obj in samples:
            self.link_fastq_files_for_sample(case_obj=case_obj, sample_obj=sample_obj)

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
        """Returns the comment associated with a sample stored in lims"""
        comment: str = self.lims_api.get_sample_comment(sample_id) or ""
        if re.match(r"\w{4}\d{2,3}", comment):
            return comment

        return ""

    def get_organism(self, sample_obj: models.Sample) -> str:
        """Organism
        - Fallback based on reference, ‘Other species’ and ‘Comment’.
        Default to "Unset"."""

        if not sample_obj.organism:
            raise CgDataError(f"Organism missing on Sample")

        organism: str = sample_obj.organism.internal_id.strip()
        comment: str = self.get_lims_comment(sample_id=sample_obj.internal_id)

        if "gonorrhoeae" in organism:
            organism = "Neisseria spp."
        elif "Cutibacterium acnes" in organism:
            organism = "Propionibacterium acnes"

        if organism == "VRE":
            reference = sample_obj.organism.reference_genome
            has_comment = bool(comment)
            if reference == "NC_017960.1":
                organism = "Enterococcus faecium"
            elif reference == "NC_004668.1":
                organism = "Enterococcus faecalis"
            elif has_comment:
                organism = comment

        return organism

    def get_parameters(self, sample_obj: models.Sample) -> Dict[str, str]:
        """Fill a dict with case config information for one sample"""

        sample_id = sample_obj.internal_id
        method_library_prep = self.lims_api.get_prep_method(sample_id)
        method_sequencing = self.lims_api.get_sequencing_method(sample_id)
        priority = (
            Priority.research.name if sample_obj.priority_int == 0 else Priority.standard.name
        )

        return {
            "CG_ID_project": self.get_project(sample_id),
            "Customer_ID_project": sample_obj.original_ticket,
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
            "sequencing_qc_passed": sample_obj.sequencing_qc,
        }

    def get_project(self, sample_id: str) -> str:
        """Get LIMS project for a sample"""
        return self.lims_api.get_sample_project(sample_id)

    def get_cases_to_store(self) -> List[models.Family]:
        """Retrieve a list of cases where analysis finished successfully,
        and is ready to be stored in Housekeeper."""

        cases_qc_ready: List[models.Family] = self.get_qc_ready_cases()
        cases_to_store: List[models.Family] = []

        for case in cases_qc_ready:
            try:
                case_run_dir: Path = self.get_case_path(case_id=case.internal_id, cleaning=False)[0]
                if not os.path.exists(os.path.join(case_run_dir, "QC_done.txt")):
                    if self.microsalt_qc(
                        case_id=case.internal_id,
                        run_dir_path=case_run_dir,
                        lims_project=self.get_project(case.samples[0].internal_id),
                    ):
                        cases_to_store.append(case)
                    else:
                        self.trailblazer_api.set_analysis_failed(case_id=case.internal_id)
                else:
                    LOG.info(f"QC already performed for case {case.internal_id}, storing case.")
                    cases_to_store.append(case)
            except IndexError:
                self.trailblazer_api.set_analysis_failed(case_id=case.internal_id)
                LOG.error(f"There are no running directories for case {case.internal_id}.")

        return cases_to_store

    def get_qc_ready_cases(self) -> List[models.Family]:
        """Retrieve a list of QC ready cases."""
        return [
            case_object
            for case_object in self.get_running_cases()
            if self.trailblazer_api.is_latest_analysis_completed(case_id=case_object.internal_id)
        ]

    def resolve_case_sample_id(
        self, sample: bool, ticket: bool, unique_id: Any
    ) -> Tuple[str, Optional[str]]:
        """Resolve case_id and sample_id w based on input arguments."""
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

    def get_case_id_from_ticket(self, unique_id: str) -> Tuple[str, None]:
        """If ticked is provided as argument, finds the corresponding case_id and returns it.
        Since sample_id is not specified, nothing is returned as sample_id"""
        case_obj: models.Family = self.status_db.find_family_by_name(unique_id)
        if not case_obj:
            LOG.error("No case found for ticket number:  %s", unique_id)
            raise click.Abort
        case_id = case_obj.internal_id
        return case_id, None

    def get_case_id_from_sample(self, unique_id: str) -> Tuple[str, str]:
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

    def get_case_id_from_case(self, unique_id: str) -> Tuple[str, None]:
        """If case_id is specified, validates the presence of case_id in database and returns it"""
        case_obj: models.Family = self.status_db.family(unique_id)
        if not case_obj:
            LOG.error("No case found with the id:  %s", unique_id)
            raise click.Abort
        case_id = case_obj.internal_id
        return case_id, None

    def microsalt_qc(self, case_id: str, run_dir_path: Path, lims_project: str) -> bool:
        """Check if Microsalt case passes QC check."""
        samples: List[Sample] = self.get_samples(case_id=case_id)
        failed_samples: Dict = {}
        qc_file: Dict = read_json(file_path=Path(run_dir_path, f"{lims_project}.json"))

        for sample in samples:
            if not sample.sequenced_at:
                continue
            self.qc_sample_check(sample=sample, failed_samples=failed_samples, qc_file=qc_file)

        return self.qc_case_check(
            case_id=case_id,
            failed_samples=failed_samples,
            samples=samples,
            run_dir_path=run_dir_path,
        )

    def qc_case_check(
        self, case_id: str, samples: List[Sample], failed_samples: Dict, run_dir_path: Path
    ) -> bool:
        """Perform the final QC check for a microbial case based on failed samples."""
        qc_pass: bool = True

        for sample in failed_samples:
            # Check if negative control failed
            if sample.control == "negative":
                qc_pass = False
            # Check if MWR sample failed
            if sample.application_version.application.tag == MicrosaltAppTags.MWRNXTR003:
                qc_pass = False

        # Check if more than 10% of MWX samples failed
        if len(failed_samples) / len(samples) > MicrosaltQC.QC_PERCENT_THRESHOLD_MWX:
            qc_pass = False

        if not qc_pass:
            LOG.warning(
                f"Case {case_id} failed QC, see {run_dir_path}/QC_done.txt for more information."
            )
        else:
            LOG.info(f"Case {case_id} passed QC.")

        self.create_qc_done_file(
            run_dir_path=run_dir_path,
            failed_samples=failed_samples,
        )
        return qc_pass

    def create_qc_done_file(self, run_dir_path: Path, failed_samples: Dict) -> None:
        """Creates a QC_done when a QC check is performed."""
        with open(os.path.join(run_dir_path, "QC_done.txt"), "w") as file:
            for sample_dict in failed_samples.items():
                file.write(f"{sample_dict[0].internal_id}: {json.dumps(sample_dict[1])} \n")

    def qc_sample_check(self, sample: Sample, failed_samples: Dict, qc_file: Dict) -> None:
        """Perform a QC on a sample."""

        if sample.control == "negative":
            if not self.check_external_negative_control_sample(sample):
                failed_samples[sample] = {
                    "Passed QC Reads": self.check_external_negative_control_sample(sample)
                }
                LOG.warning(f"Negative control sample {sample.internal_id} failed QC.")
        else:
            reads_pass: bool = sample.sequencing_qc
            coverage_10x_pass: bool = self.check_coverage_10x(sample.internal_id, qc_file)
            if not reads_pass or not coverage_10x_pass:
                failed_samples[sample] = {"Passed QC Reads": reads_pass}
                failed_samples[sample]["Passed Coverage 10X"] = coverage_10x_pass
                LOG.warning(f"Sample {sample.internal_id} failed QC.")

    def check_coverage_10x(self, sample_name: str, qc_file: Dict) -> bool:
        """Check if a sample passed the coverage_10x criteria."""
        try:
            return (
                qc_file[sample_name]["microsalt_samtools_stats"]["coverage_10x"]
                >= MicrosaltQC.COVERAGE_10X_THRESHOLD
            )
        except Exception as e:
            LOG.error(
                f"Coverage 10X couldn't be checked for sample {sample_name}, setting to fail."
            )
            LOG.error(f"see error: {e}")
            return False

    def check_external_negative_control_sample(self, sample: Sample) -> bool:
        """Check if external negative control passed read check"""
        return sample.reads < (
            sample.application_version.application.target_reads
            * MicrosaltQC.NEGATIVE_CONTROL_READS_THRESHOLD
        )
