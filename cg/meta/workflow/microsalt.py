""" API to manage Microsalt Analyses
    Organism - Fallback based on reference, ‘Other species’ and ‘Comment’. Default to “Unset”.
    Priority = Default to empty string. Weird response. Typically “standard” or “research”.
    Reference = Defaults to “None”
    Method: Outputted as “1273:23”. Defaults to “Not in LIMS”
    Date: Returns latest == most recent date. Outputted as DT object “YYYY MM DD”. Defaults to
    datetime.min"""
import gzip
import logging
from pathlib import Path
import re
from datetime import datetime
from typing import Dict, List

from cg.apps.microsalt.fastq import FastqHandler
from cg.constants import FAMILY_ACTIONS
from cg.exc import CgDataError
from cg.store.models import Sample

from cg.apps.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.store import models, Store

LOG = logging.getLogger(__name__)


class MicrosaltAnalysisAPI:
    """API to manage Microsalt Analyses"""

    def __init__(
        self,
        db: Store,
        hk_api: HousekeeperAPI,
        lims_api: LimsAPI,
        fastq_handler: FastqHandler,
        config: dict = None,
    ):
        self.db = db
        self.hk = hk_api
        self.lims = lims_api
        self.fastq_handler = fastq_handler
        self.root_dir = config.get("root") if config else None

    def has_flowcells_on_disk(self, ticket: int) -> bool:
        """Check stuff before starting the analysis."""

        flowcells = self.get_flowcells(ticket=ticket)
        statuses = []
        for flowcell_obj in flowcells:
            LOG.debug(f"{flowcell_obj.name}: checking if flowcell is on disk")
            statuses.append(flowcell_obj.status)
            if flowcell_obj.status == "removed":
                LOG.info(f"{flowcell_obj.name}: flowcell not on disk")
            elif flowcell_obj.status != "ondisk":
                LOG.warning(f"{flowcell_obj.name}: {flowcell_obj.status}")
        return all(status == "ondisk" for status in statuses)

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

    def link_samples(self, ticket: int, sample_id: str):

        sample_objs = self.get_samples(ticket, sample_id)

        if not sample_objs:
            raise Exception("Could not find any samples to link")

        for sample_obj in sample_objs:
            LOG.info("%s: link FASTQ files", sample_obj.internal_id)
            self.link_sample(
                ticket=ticket,
                sample=sample_obj.internal_id,
            )

    def link_sample(self, sample: str, ticket: int) -> None:
        """Link FASTQ files for a sample."""
        file_objs = self.hk.files(bundle=sample, tags=["fastq"])
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

        self.fastq_handler.link(ticket=ticket, sample=sample, files=files)

    def get_samples(self, ticket: int = None, sample_id: str = None) -> [models.Sample]:
        ids = {}
        if ticket:
            ids["ticket_number"] = ticket
            samples = self.db.samples_by_ids(**ids).all()
        if sample_id:
            sample = self.db.sample(internal_id=sample_id)
            samples = [sample] if sample else []
        return samples

    def get_lims_comment(self, sample_id: str) -> str:
        """ returns the comment associated with a sample stored in lims"""
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

    def get_parameters(self, sample_obj: Sample) -> Dict[str, str]:
        """Fill a dict with case config information for one sample """

        sample_id = sample_obj.internal_id
        method_library_prep = self.lims.get_prep_method(sample_id)
        if method_library_prep:
            method_library_prep, _ = method_library_prep.split(" ", 1)
        method_sequencing = self.lims.get_sequencing_method(sample_id)
        if method_sequencing:
            method_sequencing, _ = method_sequencing.split(" ", 1)
        priority = "research" if sample_obj.priority == 0 else "standard"

        parameter_dict = {
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

        return parameter_dict

    def get_project(self, sample_id: str) -> str:
        """Get LIMS project for a sample"""
        return self.lims.get_sample_project(sample_id)

    def get_flowcells(self, ticket: int) -> [models.Flowcell]:
        """Get all flowcells for all samples in a ticket"""

        flowcells = set()

        for sample in self.get_samples(ticket=ticket):
            for flowcell in sample.flowcells:
                flowcells.add(flowcell)

        return list(flowcells)

    def request_removed_flowcells(self, ticket):
        """Check stuff before starting the analysis."""

        flowcells = self.get_flowcells(ticket=ticket)
        for flowcell_obj in flowcells:
            LOG.debug(f"{flowcell_obj.name}: checking if flowcell should be requested")
            if flowcell_obj.status == "removed":
                LOG.info(f"{flowcell_obj.name}: requesting removed flowcell")
                flowcell_obj.status = "requested"
            elif flowcell_obj.status != "ondisk":
                LOG.warning(f"{flowcell_obj.name}: {flowcell_obj.status}")
        self.db.commit()

    def get_deliverables_to_store(self) -> List[Path]:
        """Retrieve a list of microbial deliverables files for orders where analysis finished
        successfully, and are ready to be stored in Housekeeper"""
        deliverables_to_store = []
        for case_object in self.db.cases_to_store(pipeline="microbial"):
            deliverables_file = self.get_deliverables_file_path(order_id=case_object.name)
            if not deliverables_file.exists():
                continue
            deliverables_to_store.append(deliverables_file)
        return deliverables_to_store

    def get_deliverables_file_path(self, order_id: str) -> Path:
        """Returns a path where the microSALT deliverables file for the order_id should be
        located"""
        deliverables_file_path = Path(
            self.root_dir,
            "results/reports/deliverables",
            order_id + "_deliverables.yaml",
        )
        return deliverables_file_path

    def set_statusdb_action(self, name: str, action: str) -> None:
        """Sets action on case based on ticket number"""
        if action in [None, *FAMILY_ACTIONS]:
            case_object = self.db.find_family(name)
            case_object.action = action
            self.db.commit()
            return
        LOG.warning(
            f"Action '{action}' not permitted by StatusDB and will not be set for case {name}"
        )
