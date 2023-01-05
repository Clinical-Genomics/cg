"""Contains API to communicate with LIMS"""
import datetime as dt
import logging
from typing import Generator, Optional, Union, Dict, List, Tuple

# fixes https://github.com/Clinical-Genomics/servers/issues/30
import requests_cache
from dateutil.parser import parse as parse_date
from genologics.entities import Process, Project, Sample, Artifact
from genologics.lims import Lims
from requests.exceptions import HTTPError

from cg.constants.lims import MASTER_STEPS_UDFS, PROP2UDF, DocumentationMethod
from cg.exc import LimsDataError

from .order import OrderHandler
from ...constants import Priority

requests_cache.install_cache(backend="memory")

SEX_MAP = {"F": "female", "M": "male", "Unknown": "unknown", "unknown": "unknown"}
REV_SEX_MAP = {value: key for key, value in SEX_MAP.items()}
AM_METHODS = {
    "1464": "Automated TruSeq DNA PCR-free library preparation method",
    "1317": "HiSeq X Sequencing method at Clinical Genomics",
    "1383": "MIP analysis for Whole genome and Exome",
    "1717": "NxSeq® AmpFREE Low DNA Library Kit (Lucigen)",
    "1060": "Raw data delivery",
    "1036": "HiSeq 2500 Rapid Run sequencing",
    "1314": "Automated SureSelect XT Target Enrichment for Illumina sequencing",
    "1518": "200 ng input Manual SureSelect XT Target Enrichment",
    "1079": "Manuel SureSelect XT Target Enrichment for Illumina sequencing",
    "1879": "Method - Manual Twist Target Enrichment",
    "2182": "Manual SARS-CoV-2 library preparation using Illumina COVIDseq Test",
    "2175": "Manual SARS-CoV-2 library preparation using Illumina DNA Prep",
    "1830": "NovaSeq 6000 Sequencing method",
    "2234": "Method - Illumina Stranded mRNA Library Preparation",
}
METHOD_INDEX, METHOD_DOCUMENT_INDEX, METHOD_VERSION_INDEX, METHOD_TYPE_INDEX = 0, 1, 2, 3

LOG = logging.getLogger(__name__)


class LimsAPI(Lims, OrderHandler):
    """API to communicate with LIMS"""

    def __init__(self, config):
        lconf = config["lims"]
        super(LimsAPI, self).__init__(lconf["host"], lconf["username"], lconf["password"])

    def sample(self, lims_id: str):
        """Fetch a sample from the LIMS database."""
        lims_sample = Sample(self, id=lims_id)
        return self._export_sample(lims_sample)

    def samples_in_pools(self, pool_name, projectname):
        """Fetch all samples from a pool"""
        return self.get_samples(udf={"pool name": str(pool_name)}, projectname=projectname)

    @staticmethod
    def _export_project(lims_project) -> dict:
        """Fetch relevant information from a lims project object"""
        return {
            "id": lims_project.id,
            "name": lims_project.name,
            "date": parse_date(lims_project.open_date) if lims_project.open_date else None,
        }

    def _export_sample(self, lims_sample):
        """Get data from a LIMS sample."""
        udfs = lims_sample.udf
        return {
            "id": lims_sample.id,
            "name": lims_sample.name,
            "project": self._export_project(lims_sample.project),
            "family": udfs.get("familyID"),
            "customer": udfs.get("customer"),
            "sex": SEX_MAP.get(udfs.get("Gender"), None),
            "father": udfs.get("fatherID"),
            "mother": udfs.get("motherID"),
            "source": udfs.get("Source"),
            "status": udfs.get("Status"),
            "panels": udfs.get("Gene List").split(";") if udfs.get("Gene List") else None,
            "priority": udfs.get("priority"),
            "received": self.get_received_date(lims_sample.id),
            "application": udfs.get("Sequencing Analysis"),
            "application_version": (
                int(udfs["Application Tag Version"])
                if udfs.get("Application Tag Version")
                else None
            ),
            "comment": udfs.get("comment"),
        }

    @staticmethod
    def _export_artifact(lims_artifact):
        """Get data from a LIMS artifact."""
        return {"id": lims_artifact.id, "name": lims_artifact.name}

    def get_received_date(self, lims_id: str) -> dt.date:
        """Get the date when a sample was received."""

        sample = Sample(self, id=lims_id)
        try:
            date = sample.udf.get("Received at")
        except HTTPError:
            date = None
        return date

    def get_prepared_date(self, lims_id: str) -> dt.date:
        """Get the date when a sample was prepared in the lab."""

        sample = Sample(self, id=lims_id)
        try:
            date = sample.udf.get("Library Prep Finished")
        except HTTPError:
            date = None
        return date

    def get_delivery_date(self, lims_id: str) -> dt.date:
        """Get delivery date for a sample."""

        sample = Sample(self, id=lims_id)
        try:
            date = sample.udf.get("Delivered at")
        except HTTPError:
            date = None
        return date

    def get_sequenced_date(self, lims_id: str) -> dt.date:
        """Get the date when a sample was sequenced."""

        sample = Sample(self, id=lims_id)
        try:
            date = sample.udf.get("Sequencing Finished")
        except HTTPError:
            date = None
        return date

    def capture_kit(self, lims_id: str) -> str:
        """Get capture kit for a LIMS sample."""

        step_names_udfs = MASTER_STEPS_UDFS["capture_kit_step"]
        capture_kits = set()

        lims_sample = Sample(self, id=lims_id)
        capture_kit = lims_sample.udf.get("Bait Set")

        if capture_kit and capture_kit != "NA":
            return capture_kit

        for process_type in step_names_udfs:
            artifacts = self.get_artifacts(
                samplelimsid=lims_id, process_type=process_type, type="Analyte"
            )
            udf_key = step_names_udfs[process_type]
            capture_kits = capture_kits.union(
                self._find_capture_kits(artifacts, udf_key)
                or self._find_twist_capture_kits(artifacts, udf_key)
            )

        if len(capture_kits) > 1:
            message = f"Capture kit error: {lims_sample.id} | {capture_kits}"
            raise LimsDataError(message)

        if len(capture_kits) == 1:
            return capture_kits.pop()

        return None

    def get_samples(self, *args, map_ids=False, **kwargs) -> Union[Dict[str, str], List[Sample]]:
        """Bypass to original method."""
        lims_samples = super(LimsAPI, self).get_samples(*args, **kwargs)
        if map_ids:
            return {lims_sample.name: lims_sample.id for lims_sample in lims_samples}

        return lims_samples

    def family(self, customer: str, family: str):
        """Fetch information about a family of samples."""
        filters = {"customer": customer, "familyID": family}
        lims_samples = self.get_samples(udf=filters)
        samples_data = [self._export_sample(lims_sample) for lims_sample in lims_samples]
        # get family level data
        family_data = {"family": family, "customer": customer, "samples": []}
        priorities = set()
        panels = set()

        for sample_data in samples_data:
            priorities.add(sample_data["priority"])
            if sample_data["panels"]:
                panels.update(sample_data["panels"])
            family_data["samples"].append(sample_data)

        if len(priorities) == 1:
            family_data["priority"] = priorities.pop()
        elif len(priorities) < 1:
            raise LimsDataError(f"unable to determine family priority: {priorities}")
        else:
            for prio in [
                Priority.express,
                Priority.priority,
                Priority.standard,
                Priority.clinical_trials,
            ]:
                if prio in priorities:
                    family_data["priority"] = prio.name
                    break

        family_data["panels"] = list(panels)
        return family_data

    def process(self, process_id: str) -> Process:
        """Get LIMS process."""
        return Process(self, id=process_id)

    @staticmethod
    def process_samples(lims_process: Process) -> Generator[str, None, None]:
        """Retrieve LIMS input samples from a process."""
        for lims_artifact in lims_process.all_inputs():
            for lims_sample in lims_artifact.samples:
                yield lims_sample.id

    def update_sample(
        self, lims_id: str, sex=None, target_reads: int = None, name: str = None, **kwargs
    ):
        """Update information about a sample."""
        lims_sample = Sample(self, id=lims_id)

        if sex:
            lims_gender = REV_SEX_MAP.get(sex)
            if lims_gender:
                lims_sample.udf[PROP2UDF["sex"]] = lims_gender
        if name:
            lims_sample.name = name
        if isinstance(target_reads, int):
            lims_sample.udf[PROP2UDF["target_reads"]] = target_reads

        for key, value in kwargs.items():
            if not PROP2UDF.get(key):
                raise LimsDataError(
                    f"Unknown how to set {key} in LIMS since it is not defined in {PROP2UDF}"
                )
            lims_sample.udf[PROP2UDF[key]] = value

        lims_sample.put()

    def get_sample_attribute(self, lims_id: str, key: str) -> str:
        """Get data from a sample."""

        sample = Sample(self, id=lims_id)
        if not PROP2UDF.get(key):
            raise LimsDataError(
                f"Unknown how to get {key} from LIMS since it is not defined in " f"{PROP2UDF}"
            )
        return sample.udf[PROP2UDF[key]]

    def update_project(self, lims_id: str, name: str = None) -> None:
        """Update information about a project."""
        lims_project = Project(self, id=lims_id)
        if name:
            lims_project.name = name
            lims_project.put()

    def get_prep_method(self, lims_id: str) -> str:
        """Get the library preparation method."""

        step_names_udfs = MASTER_STEPS_UDFS["prep_method_step"]

        return self._get_methods(step_names_udfs, lims_id)

    def get_sequencing_method(self, lims_id: str) -> str:
        """Get the sequencing method."""

        step_names_udfs = MASTER_STEPS_UDFS["sequencing_method_step"]

        return self._get_methods(step_names_udfs, lims_id)

    def get_delivery_method(self, lims_id: str) -> str:
        """Get the delivery method."""

        step_names_udfs = MASTER_STEPS_UDFS["delivery_method_step"]

        return self._get_methods(step_names_udfs, lims_id)

    def get_processing_time(self, lims_id: str) -> Optional[dt.timedelta]:
        """Get the time it takes to process a sample"""
        received_at = self.get_received_date(lims_id)
        delivery_date = self.get_delivery_date(lims_id)
        if received_at and delivery_date:
            return delivery_date - received_at
        return None

    @staticmethod
    def _sort_by_date_run(sort_list: list):
        """
        Sort list of tuples by parent process attribute date_run in descending order.

        Parameters:
            sort_list (list): a list of tuples in the format (date_run, elem1, elem2, ...)

        Returns:
            sorted list of tuples
        """
        return sorted(sort_list, key=lambda sort_tuple: sort_tuple[0], reverse=True)

    def _most_recent_date(self, dates: list):
        """
        Gets the most recent date from a list of dates sorted by date_run

        Parameters:
            dates (list): a list of tuples in the format (date_run, date), sorted by date_run
                descending

        Returns:
            The date in the first tuple in dates
        """
        sorted_dates = self._sort_by_date_run(dates)
        date_run_index = 0
        date_index = 1

        return sorted_dates[date_run_index][date_index] if dates else None

    def _get_methods(self, step_names_udfs, lims_id):
        """
        Gets the method, method number and method version for a given list of step names for AM documents.
        Only method name and Atlas version is returned if Atlas documentation instead has been used.
        """
        methods = []

        for process_name in step_names_udfs:
            artifacts = self.get_artifacts(process_type=process_name, samplelimsid=lims_id)
            if not artifacts:
                continue
            # Get a list of parent processes for the artifacts
            processes: List[Process] = self.get_processes_from_artifacts(artifacts=artifacts)
            for process in processes:
                # Check which type of method document has been used
                method_type: str = self.get_method_type(process, step_names_udfs[process_name])
                udf_key_method_doc, udf_key_version = self.get_method_udf_values(
                    step_names_udfs[process_name], method_type
                )
                methods.append(
                    (
                        process.date_run,
                        self.get_method_document(process, udf_key_method_doc),
                        self.get_method_version(process, udf_key_version),
                        method_type,
                    )
                )

        sorted_methods = self._sort_by_date_run(methods)

        if sorted_methods:
            method = sorted_methods[METHOD_INDEX]

            if (
                method[METHOD_TYPE_INDEX] == DocumentationMethod.AM
                and method[METHOD_DOCUMENT_INDEX] is not None
            ):
                method_name = AM_METHODS.get(method[METHOD_DOCUMENT_INDEX])
                return (
                    f"{method[METHOD_DOCUMENT_INDEX]}:{method[METHOD_VERSION_INDEX]} - "
                    f"{method_name}"
                )
            elif (
                method[METHOD_TYPE_INDEX] == DocumentationMethod.ATLAS
                and method[METHOD_DOCUMENT_INDEX] is not None
            ):
                return f"{method[METHOD_DOCUMENT_INDEX]} ({method[METHOD_VERSION_INDEX]})"

        return None

    @staticmethod
    def get_processes_from_artifacts(artifacts: List[Artifact]) -> List[Process]:
        """
        Get a list of parent processes from a set of given artifacts.
        """
        processes: List = []
        for artifact in artifacts:
            parent_process: Process = artifact.parent_process
            if parent_process not in processes:
                processes.append(parent_process)
        return processes

    @staticmethod
    def get_method_type(process: Process, method_udfs: Dict) -> str:
        """
        Return which type of method documentation has been used, AM or Atlas.
        """
        if "atlas_version" in method_udfs and process.udf.get(method_udfs["atlas_version"]):
            return DocumentationMethod.ATLAS
        return DocumentationMethod.AM

    @staticmethod
    def get_method_udf_values(method_udfs: Dict, method_type: str) -> Tuple[str, str]:
        """
        Return UDF values for Method and Method version depending on which method type.
        """
        if method_type == DocumentationMethod.ATLAS:
            udf_key_method_doc = method_udfs["atlas_document"]
            udf_key_version = method_udfs["atlas_version"]
        else:
            udf_key_method_doc = method_udfs["method_number"]
            udf_key_version = method_udfs["method_version"]
        return udf_key_method_doc, udf_key_version

    @staticmethod
    def get_method_document(process: Process, udf_key_method_doc: str) -> str:
        """
        Return method number for artifact.
        """
        return process.udf.get(udf_key_method_doc)

    @staticmethod
    def get_method_version(process: Process, udf_key_version: str) -> str:
        """
        Return method version for artifact.
        """
        return process.udf.get(udf_key_version)

    @staticmethod
    def _find_capture_kits(artifacts, udf_key):
        """
        get capture kit from parent process for non-TWIST samples
        """
        return {
            artifact.parent_process.udf.get(udf_key)
            for artifact in artifacts
            if artifact.parent_process.udf.get(udf_key) is not None
        }

    @staticmethod
    def _find_twist_capture_kits(artifacts, udf_key):
        """
        get capture kit from parent process for TWIST samples
        """
        return {
            artifact.udf.get(udf_key)
            for artifact in artifacts
            if artifact.udf.get(udf_key) is not None
        }

    def get_sample_comment(self, sample_id: str) -> str:
        """Get the comment of the sample"""
        lims_sample = self.sample(sample_id)
        return lims_sample.get("comment")

    def get_sample_project(self, sample_id: str) -> str:
        """Get the lims-id for the project of the sample"""
        return self.sample(sample_id).get("project").get("id")
