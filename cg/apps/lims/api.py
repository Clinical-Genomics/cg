# -*- coding: utf-8 -*-
import datetime as dt
import logging

from genologics.entities import Sample, Process, Project
from genologics.lims import Lims
from dateutil.parser import parse as parse_date

from cg.exc import LimsDataError
from .constants import PROP2UDF, MASTER_STEPS_UDFS, PROCESSES
from .order import OrderHandler

# fixes https://github.com/Clinical-Genomics/servers/issues/30
import requests_cache

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
    "1830": "NovaSeq 6000 Sequencing method",
}
METHOD_INDEX, METHOD_NUMBER_INDEX, METHOD_VERSION_INDEX = 0, 1, 2

log = logging.getLogger(__name__)


class LimsAPI(Lims, OrderHandler):
    def __init__(self, config):
        lconf = config["lims"]
        super(LimsAPI, self).__init__(
            lconf["host"], lconf["username"], lconf["password"]
        )

    def sample(self, lims_id: str):
        """Fetch a sample from the LIMS database."""
        lims_sample = Sample(self, id=lims_id)
        data = self._export_sample(lims_sample)
        return data

    def samples_in_pools(self, pool_name, projectname):
        return self.get_samples(
            udf={"pool name": str(pool_name)}, projectname=projectname
        )

    def _export_project(self, lims_project):
        return {
            "id": lims_project.id,
            "name": lims_project.name,
            "date": parse_date(lims_project.open_date)
            if lims_project.open_date
            else None,
        }

    def _export_sample(self, lims_sample):
        """Get data from a LIMS sample."""
        udfs = lims_sample.udf
        data = {
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
            "panels": udfs.get("Gene List").split(";")
            if udfs.get("Gene List")
            else None,
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
        return data

    def _export_artifact(self, lims_artifact):
        """Get data from a LIMS artifact."""
        return {"id": lims_artifact.id, "name": lims_artifact.name}

    def get_received_date(self, lims_id: str) -> str:
        """Get the date when a sample was received."""

        step_names_udfs = MASTER_STEPS_UDFS["received_step"]

        received_dates = self._get_all_step_dates(step_names_udfs, lims_id)
        received_date = self._most_recent_date(received_dates)

        return received_date

    def get_prepared_date(self, lims_id: str) -> dt.datetime:
        """Get the date when a sample was prepared in the lab."""

        step_names_udfs = MASTER_STEPS_UDFS["prepared_step"]
        prepared_dates = []

        for process_type in step_names_udfs:
            artifacts = self.get_artifacts(
                process_type=process_type, samplelimsid=lims_id
            )

            for artifact in artifacts:
                prepared_dates.append(parse_date(artifact.parent_process.date_run))

        if prepared_dates:
            sorted_dates = sorted(prepared_dates, reverse=True)
            prepared_date = sorted_dates[0]

        return prepared_date if prepared_dates else None

    def get_delivery_date(self, lims_id: str) -> dt.date:
        """Get delivery date for a sample."""

        step_names_udfs = MASTER_STEPS_UDFS["delivery_step"]

        delivered_dates = self._get_all_step_dates(
            step_names_udfs, lims_id, artifact_type="Analyte"
        )

        if len(delivered_dates) > 1:
            log.warning("multiple delivery artifacts found for: %s", lims_id)

        delivered_date = self._most_recent_date(delivered_dates)

        return delivered_date

    def get_sequenced_date(self, lims_id: str) -> dt.date:
        """Get the date when a sample was sequenced."""
        novaseq_process = PROCESSES["sequenced_date"]

        step_names_udfs = MASTER_STEPS_UDFS["sequenced_step"]

        sequenced_dates = self._get_all_step_dates(step_names_udfs, lims_id)

        novaseq_artifacts = self.get_artifacts(
            process_type=novaseq_process, samplelimsid=lims_id
        )

        if novaseq_artifacts and novaseq_artifacts[0].parent_process.date_run:
            sequenced_dates.append(
                (
                    novaseq_artifacts[0].parent_process.date_run,
                    parse_date(novaseq_artifacts[0].parent_process.date_run),
                )
            )

        if len(sequenced_dates) > 1:
            log.warning("multiple sequence artifacts found for: %s", lims_id)

        sequenced_date = self._most_recent_date(sequenced_dates)

        return sequenced_date

    def capture_kit(self, lims_id: str) -> str:
        """Get capture kit for a LIMS sample."""

        step_names_udfs = MASTER_STEPS_UDFS["capture_kit_step"]
        capture_kits = set()

        lims_sample = Sample(self, id=lims_id)
        capture_kit = lims_sample.udf.get("Capture Library version")
        if capture_kit and capture_kit != "NA":
            return capture_kit
        else:
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

    def get_samples(self, *args, map_ids=False, **kwargs):
        """Bypass to original method."""
        lims_samples = super(LimsAPI, self).get_samples(*args, **kwargs)
        if map_ids:
            lims_map = {
                lims_sample.name: lims_sample.id for lims_sample in lims_samples
            }
            return lims_map
        else:
            return lims_samples

    def family(self, customer: str, family: str):
        """Fetch information about a family of samples."""
        filters = {"customer": customer, "familyID": family}
        lims_samples = self.get_samples(udf=filters)
        samples_data = [
            self._export_sample(lims_sample) for lims_sample in lims_samples
        ]
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
        elif "express" in priorities:
            family_data["priority"] = "express"
        elif "priority" in priorities:
            family_data["priority"] = "priority"
        elif "standard" in priorities:
            family_data["priority"] = "standard"
        else:
            raise LimsDataError(f"unable to determine family priority: {priorities}")

        family_data["panels"] = list(panels)
        return family_data

    def process(self, process_id: str) -> Process:
        """Get LIMS process."""
        return Process(self, id=process_id)

    def process_samples(self, lims_process: Process):
        """Retrieve LIMS input samples from a process."""
        for lims_artifact in lims_process.all_inputs():
            for lims_sample in lims_artifact.samples:
                yield lims_sample.id

    def update_sample(
        self,
        lims_id: str,
        sex=None,
        application: str = None,
        target_reads: int = None,
        priority=None,
        data_analysis=None,
        name: str = None,
    ):
        """Update information about a sample."""
        lims_sample = Sample(self, id=lims_id)
        if sex:
            lims_gender = REV_SEX_MAP.get(sex)
            if lims_gender:
                lims_sample.udf[PROP2UDF["sex"]] = lims_gender
        if application:
            lims_sample.udf[PROP2UDF["application"]] = application
        if isinstance(target_reads, int):
            lims_sample.udf[PROP2UDF["target_reads"]] = target_reads
        if priority:
            lims_sample.udf[PROP2UDF["priority"]] = priority
        if data_analysis:
            lims_sample.udf[PROP2UDF["data_analysis"]] = data_analysis
        if name:
            lims_sample.name = name

        lims_sample.put()

    def update_project(self, lims_id: str, name=None):
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

    def get_processing_time(self, lims_id):
        received_at = self.get_received_date(lims_id)
        delivery_date = self.get_delivery_date(lims_id)
        if received_at and delivery_date:
            return delivery_date - received_at

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
        Gets the method, method number and method version for a given list of stop names
        """
        methods = []

        for process_name in step_names_udfs:
            artifacts = self.get_artifacts(
                process_type=process_name, samplelimsid=lims_id
            )
            if artifacts:
                udf_key_number = step_names_udfs[process_name]["method_number"]
                udf_key_version = step_names_udfs[process_name]["method_version"]
                methods.append(
                    (
                        artifacts[0].parent_process.date_run,
                        self.get_method_number(artifacts[0], udf_key_number),
                        self.get_method_version(artifacts[0], udf_key_version),
                    )
                )

        sorted_methods = self._sort_by_date_run(methods)

        if sorted_methods:
            method = sorted_methods[METHOD_INDEX]

            if method[METHOD_NUMBER_INDEX] is not None:
                method_name = AM_METHODS.get(method[METHOD_NUMBER_INDEX])
                return (
                    f"{method[METHOD_NUMBER_INDEX]}:{method[METHOD_VERSION_INDEX]} - "
                    f"{method_name}"
                )

        return None

    def _get_all_step_dates(self, step_names_udfs, lims_id, artifact_type=None):
        """
        Gets all the dates from artifact bases on process type and associated udfs, sample lims id
        and optionally the type
        """
        dates = []

        for process_type in step_names_udfs:
            artifacts = self.get_artifacts(
                process_type=process_type, samplelimsid=lims_id, type=artifact_type
            )

            for artifact in artifacts:
                udf_key = step_names_udfs[process_type]
                if artifact.parent_process and artifact.parent_process.udf.get(udf_key):
                    dates.append(
                        (
                            artifact.parent_process.date_run,
                            artifact.parent_process.udf.get(udf_key),
                        )
                    )

        return dates

    @staticmethod
    def get_method_number(artifact, udf_key_number):
        """
        get method number for artifact
        """
        return artifact.parent_process.udf.get(udf_key_number)

    @staticmethod
    def get_method_version(artifact, udf_key_version):
        """
        get method version for artifact
        """
        return artifact.parent_process.udf.get(udf_key_version)

    @staticmethod
    def _find_capture_kits(artifacts, udf_key):
        """
        get capture kit from parent process for non-TWIST samples
        """
        capture_kits = set(
            artifact.parent_process.udf.get(udf_key)
            for artifact in artifacts
            if artifact.parent_process.udf.get(udf_key) is not None
        )
        return capture_kits

    @staticmethod
    def _find_twist_capture_kits(artifacts, udf_key):
        """
        get capture kit from parent process for TWIST samples
        """
        capture_kits = set(
            artifact.udf.get(udf_key)
            for artifact in artifacts
            if artifact.udf.get(udf_key) is not None
        )
        return capture_kits
