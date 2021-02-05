""" API to manage Microsalt Analyses
    Organism - Fallback based on reference, ‘Other species’ and ‘Comment’. Default to “Unset”.
    Priority = Default to empty string. Weird response. Typically “standard” or “research”.
    Reference = Defaults to “None”
    Method: Outputted as “1273:23”. Defaults to “Not in LIMS”
    Date: Returns latest == most recent date. Outputted as DT object “YYYY MM DD”. Defaults to
    datetime.min"""
import gzip
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from subprocess import CalledProcessError
from typing import Any, Dict, List, Optional

import click

from cg.apps.environ import environ_email
from cg.apps.hermes.hermes_api import HermesApi
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.tb import TrailblazerAPI
from cg.constants import CASE_ACTIONS, Pipeline
from cg.exc import BundleAlreadyAddedError, CgDataError
from cg.store import Store, models
from cg.utils import Process

LOG = logging.getLogger(__name__)


class MicrosaltAnalysisAPI:
    """API to manage Microsalt Analyses"""

    def __init__(
        self,
        db: Store,
        hk_api: HousekeeperAPI,
        lims_api: LimsAPI,
        hermes_api: HermesApi,
        trailblazer_api: TrailblazerAPI,
        config: Optional[dict] = {},
    ):
        self.db = db
        self.hk = hk_api
        self.lims = lims_api
        self.hermes_api = hermes_api
        self.trailblazer_api = trailblazer_api
        self.root_dir = config["root"]
        self.queries_path = config["queries_path"]
        self.process = Process(binary=config["binary_path"], environment=config["conda_env"])

    def check_flowcells_on_disk(self, case_id: str, sample_id: Optional[str] = None) -> bool:
        """Check if flowcells are on disk for sample before starting the analysis.
        Flowcells not on disk will be requested
        """

        flowcells = self.get_flowcells(case_id=case_id, sample_id=sample_id)
        statuses = []
        for flowcell_obj in flowcells:
            LOG.debug(f"{flowcell_obj.name}: checking if flowcell is on disk")
            statuses.append(flowcell_obj.status)
            if flowcell_obj.status == "removed":
                LOG.info(f"{flowcell_obj.name}: flowcell not on disk, requesting")
                flowcell_obj.status = "requested"
            elif flowcell_obj.status != "ondisk":
                LOG.warning(f"{flowcell_obj.name}: {flowcell_obj.status}")
        self.db.commit()
        return all(status == "ondisk" for status in statuses)

    def get_flowcells(self, case_id: str, sample_id: Optional[str] = None) -> List[models.Flowcell]:
        """Get all flowcells for all samples in a ticket"""
        flowcells = set()
        for sample in self.get_samples(case_id=case_id, sample_id=sample_id):
            for flowcell in sample.flowcells:
                flowcells.add(flowcell)

        return list(flowcells)

    def get_case_fastq_path(self, case_id: str) -> Path:
        return Path(self.root_dir, "fastq", case_id)

    def get_config_path(self, filename: str) -> Path:
        return Path(self.queries_path, filename).with_suffix(".json")

    def get_trailblazer_config_path(self, case_id: str) -> Path:
        case_obj: models.Family = self.db.family(case_id)
        order_id = case_obj.name
        return Path(
            self.root_dir, "results", "reports", "trailblazer", f"{order_id}_slurm_ids.yaml"
        )

    def get_deliverables_file_path(self, case_id: str) -> Path:
        """Returns a path where the microSALT deliverables file for the order_id should be
        located"""
        case_obj: models.Family = self.db.family(case_id)
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

    @staticmethod
    def generate_fastq_name(
        lane: str, flowcell: str, sample: str, read: str, more: dict = None
    ) -> str:
        """Name a FASTQ file following usalt conventions. Naming must be
        xxx_R_1.fastq.gz and xxx_R_2.fastq.gz"""

        undetermined = more.get("undetermined", None)
        # ACC1234A1_FCAB1ABC2_L1_1.fastq.gz sample_flowcell_lane_read.fastq.gz
        flowcell = f"{flowcell}-undetermined" if undetermined else flowcell
        return f"{sample}_{flowcell}_L{lane}_{read}.fastq.gz"

    @staticmethod
    def fastq_header(line: str) -> dict:
        """handle illumina's two different header formats
        @see https://en.wikipedia.org/wiki/FASTQ_format

        @HWUSI-EAS100R:6:73:941:1973#0/1

            HWUSI-EAS100R   the unique instrument name
            6   flowcell lane
            73  tile number within the flowcell lane
            941     'x'-coordinate of the cluster within the tile
            1973    'y'-coordinate of the cluster within the tile
            #0  index number for a multiplexed sample (0 for no indexing)
            /1  the member of a pair, /1 or /2 (paired-end or mate-pair reads only)

        Versions of the Illumina pipeline since 1.4 appear to use #NNNNNN
        instead of #0 for the multiplex ID, where NNNNNN is the sequence of the
        multiplex tag.

        With Casava 1.8 the format of the '@' line has changed:

        @EAS139:136:FC706VJ:2:2104:15343:197393 1:Y:18:ATCACG

            EAS139  the unique instrument name
            136     the run id
            FC706VJ     the flowcell id
            2   flowcell lane
            2104    tile number within the flowcell lane
            15343   'x'-coordinate of the cluster within the tile
            197393  'y'-coordinate of the cluster within the tile
            1   the member of a pair, 1 or 2 (paired-end or mate-pair reads only)
            Y   Y if the read is filtered, N otherwise
            18  0 when none of the control bits are on, otherwise it is an even number
            ATCACG  index sequence
        """

        rs = {"lane": None, "flowcell": None, "readnumber": None}

        parts = line.split(":")
        if len(parts) == 5:  # @HWUSI-EAS100R:6:73:941:1973#0/1
            rs["lane"] = parts[1]
            rs["flowcell"] = "XXXXXX"
            rs["readnumber"] = parts[-1].split("/")[-1]
        if len(parts) == 10:  # @EAS139:136:FC706VJ:2:2104:15343:197393 1:Y:18:ATCACG
            rs["lane"] = parts[3]
            rs["flowcell"] = parts[2]
            rs["readnumber"] = parts[6].split(" ")[-1]
        if len(parts) == 7:  # @ST-E00201:173:HCLCGALXX:1:2106:22516:34834/1
            rs["lane"] = parts[3]
            rs["flowcell"] = parts[2]
            rs["readnumber"] = parts[-1].split("/")[-1]

        return rs

    def link_samples(self, case_id: str, sample_id: Optional[str] = None) -> None:

        case_dir: Path = self.get_case_fastq_path(case_id=case_id)
        case_dir.mkdir(parents=True, exist_ok=True)

        samples = self.get_samples(case_id=case_id, sample_id=sample_id)

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

        file_objs = self.hk.files(bundle=sample_id, tags=["fastq"])
        files = []

        for file_obj in file_objs:
            # figure out flowcell name from header
            with gzip.open(file_obj.full_path) as handle:
                header_line = handle.readline().decode()
                header_info = self.fastq_header(header_line)

            data = {
                "path": file_obj.full_path,
                "lane": int(header_info["lane"]),
                "flowcell": header_info["flowcell"],
                "read": int(header_info["readnumber"]),
                "undetermined": ("_Undetermined_" in file_obj.path),
            }
            # look for tile identifier (HiSeq X runs)
            matches = re.findall(r"-l[1-9]t([1-9]{2})_", file_obj.path)
            if len(matches) > 0:
                data["flowcell"] = f"{data['flowcell']}-{matches[0]}"
            files.append(data)

        for fastq_data in files:
            original_fastq_path = Path(fastq_data["path"])
            linked_fastq_name = self.generate_fastq_name(
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
                self.db.query(models.Sample).filter(models.Sample.internal_id == sample_id).first()
            ]

        case_obj: models.Family = self.db.family(case_id)
        return [link.sample for link in case_obj.links]

    def get_lims_comment(self, sample_id: str) -> str:
        """ Returns the comment associated with a sample stored in lims"""
        comment = self.lims.get_sample_comment(sample_id) or ""
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
        method_library_prep = self.lims.get_prep_method(sample_id)
        if method_library_prep:
            method_library_prep, _ = method_library_prep.split(" ", 1)
        method_sequencing = self.lims.get_sequencing_method(sample_id)
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
        return self.lims.get_sample_project(sample_id)

    def get_deliverables_to_store(self) -> list:
        """Retrieve a list of microbial deliverables files for orders where analysis finished
        successfully, and are ready to be stored in Housekeeper"""

        return self.db.cases_to_store(pipeline=Pipeline.MICROSALT)

    def set_statusdb_action(self, case_id: str, action: Optional[str]) -> None:
        """Sets action on case based on ticket number"""
        if action in [None, *CASE_ACTIONS]:
            case_object: models.Family = self.db.family(case_id)
            case_object.action = action
            self.db.commit()
            LOG.info("Action %s set for case %s", action, case_id)
            return
        LOG.warning(
            f"Action '{action}' not permitted by StatusDB and will not be set for case {case_id}"
        )

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
        case_obj: models.Family = self.db.find_family_by_name(unique_id)
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
            self.db.query(models.Sample).filter(models.Sample.internal_id == unique_id).first()
        )
        if not sample_obj:
            LOG.error("No sample found with id: %s", unique_id)
            raise click.Abort
        case_id = sample_obj.links[0].family.internal_id
        sample_id = sample_obj.internal_id
        return case_id, sample_id

    def get_case_id_from_case(self, unique_id: str) -> (str, None):
        """If case_id is specified, validates the presence of case_id in database and returns it"""
        case_obj: models.Family = self.db.family(unique_id)
        if not case_obj:
            LOG.error("No case found with the id:  %s", unique_id)
            raise click.Abort
        case_id = case_obj.internal_id
        return case_id, None

    def store_microbial_analysis_housekeeper(self, case_id: str) -> None:
        """Gather information from microSALT analysis to store."""

        deliverables_path = self.get_deliverables_file_path(case_id=case_id)
        if not deliverables_path.exists():
            LOG.warning(
                "Deliverables file not found for %s, analysis may not be finished yet", case_id
            )
            raise click.Abort

        analysis_date = self.get_date_from_deliverables_path(deliverables_path=deliverables_path)

        bundle_data = self.hermes_api.create_housekeeper_bundle(
            deliverables=deliverables_path,
            pipeline="microsalt",
            created=analysis_date,
            analysis_type=None,
            bundle_name=case_id,
        ).dict()
        bundle_data["name"] = case_id

        bundle_result = self.hk.add_bundle(bundle_data=bundle_data)
        if not bundle_result:
            raise BundleAlreadyAddedError("Bundle already added to Housekeeper!")
        bundle_object, bundle_version = bundle_result
        self.hk.include(bundle_version)
        self.hk.add_commit(bundle_object, bundle_version)
        LOG.info(
            f"Analysis successfully stored in Housekeeper: {case_id} : {bundle_version.created_at}"
        )

    def store_microbial_analysis_statusdb(self, case_id: str) -> None:
        """Creates an analysis object in StatusDB"""
        deliverables_path = self.get_deliverables_file_path(case_id=case_id)
        analysis_date = self.get_date_from_deliverables_path(deliverables_path=deliverables_path)
        case_obj: models.Family = self.db.family(case_id)

        new_analysis: models.Analysis = self.db.add_analysis(
            pipeline=Pipeline.MICROSALT,
            version=self.get_microsalt_version(),
            started_at=analysis_date,
            completed_at=datetime.now(),
            primary=(len(case_obj.analyses) == 0),
        )
        new_analysis.family = case_obj
        self.db.add_commit(new_analysis)
        LOG.info(f"Analysis successfully stored in StatusDB: {case_id} : {analysis_date}")

    @staticmethod
    def get_date_from_deliverables_path(deliverables_path: Path) -> datetime.date:
        """ Get date from deliverables path using date created metadata """
        return datetime.fromtimestamp(int(os.path.getctime(deliverables_path)))

    def get_priority(self, case_id: str) -> str:
        """Returns priority for the case in clinical-db as text"""
        case_object = self.db.family(case_id)
        if case_object.high_priority:
            return "high"
        if case_object.low_priority:
            return "low"
        return "normal"

    def submit_trailblazer_analysis(self, case_id: str) -> None:
        self.trailblazer_api.mark_analyses_deleted(case_id=case_id)
        self.trailblazer_api.add_pending_analysis(
            case_id=case_id,
            email=environ_email(),
            type="other",
            out_dir=self.get_deliverables_file_path(case_id).parent.as_posix(),
            config_path=self.get_trailblazer_config_path(case_id=case_id).as_posix(),
            priority=self.get_priority(case_id),
            data_analysis=Pipeline.MICROSALT,
        )

    def get_microsalt_version(self) -> str:
        try:
            self.process.run_command(["--version"])
            return list(self.process.stdout_lines())[0].split()[-1]
        except CalledProcessError:
            LOG.warning("Could not retrieve microsalt version!")
            return "0.0.0"
