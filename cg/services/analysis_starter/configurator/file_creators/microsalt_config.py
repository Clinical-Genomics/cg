import re
from datetime import datetime
from pathlib import Path

from cg.apps.lims import LimsAPI
from cg.constants import Priority
from cg.constants.constants import FileFormat
from cg.exc import CgDataError
from cg.io.controller import WriteFile
from cg.services.sequencing_qc_service import SequencingQCService
from cg.store.models import Case, Sample
from cg.store.store import Store


class MicrosaltConfigFileCreator:

    def __init__(self, lims_api: LimsAPI, queries_path: str, store: Store):
        self.lims_api = lims_api
        self.queries_path = queries_path
        self.store = store

    def create(self, case_id: str):
        content: list[dict] = self._get_content(case_id)
        config_case_path: Path = self.get_config_path(case_id)
        WriteFile.write_file_from_content(
            content=content, file_format=FileFormat.JSON, file_path=config_case_path
        )

    def _get_content(self, case_id: str) -> list[dict]:
        case: Case = self.store.get_case_by_internal_id(case_id)

        return [self._get_content_for_sample(sample) for sample in case.samples]

    def _get_content_for_sample(self, sample: Sample) -> dict[str, str]:
        """Fill a dict with case config information for one sample"""

        sample_id: str = sample.internal_id
        method_library_prep: str | None = self.lims_api.get_prep_method(sample_id)
        method_sequencing: str | None = self.lims_api.get_sequencing_method(sample_id)
        priority = Priority.research.name if sample.priority == 0 else Priority.standard.name
        passes_sequencing_qc: bool = SequencingQCService.sample_pass_sequencing_qc(sample)

        return {
            "CG_ID_project": self.lims_api.get_sample_project(sample_id),
            "Customer_ID_project": sample.original_ticket,
            "CG_ID_sample": sample.internal_id,
            "Customer_ID_sample": sample.name,
            "organism": self._get_organism(sample),
            "priority": priority,
            "reference": sample.reference_genome,
            "Customer_ID": sample.customer.internal_id,
            "application_tag": sample.application_version.application.tag,
            "date_arrival": str(sample.received_at or datetime.min),
            "date_sequencing": str(sample.last_sequenced_at or datetime.min),
            "date_libprep": str(sample.prepared_at or datetime.min),
            "method_libprep": method_library_prep or "Not in LIMS",
            "method_sequencing": method_sequencing or "Not in LIMS",
            "sequencing_qc_passed": passes_sequencing_qc,
        }

    def _get_organism(self, sample: Sample) -> str:
        """Organism
        - Fallback based on reference, ‘Other species’ and ‘Comment’.
        Default to "Unset"."""

        if not sample.organism:
            raise CgDataError("Organism missing on Sample")

        organism: str = sample.organism.internal_id.strip()
        comment: str = self._get_lims_comment(sample.internal_id)

        if "gonorrhoeae" in organism:
            organism = "Neisseria spp."
        elif "Cutibacterium acnes" in organism:
            organism = "Propionibacterium acnes"

        if organism == "VRE":
            reference = sample.organism.reference_genome
            has_comment = bool(comment)
            if reference == "NC_017960.1":
                organism = "Enterococcus faecium"
            elif reference == "NC_004668.1":
                organism = "Enterococcus faecalis"
            elif has_comment:
                organism = comment

        return organism

    def _get_lims_comment(self, sample_id: str) -> str:
        """Returns the comment associated with a sample stored in lims"""
        comment: str = self.lims_api.get_sample_comment(sample_id) or ""
        return comment if re.match(r"\w{4}\d{2,3}", comment) else ""

    def get_config_path(self, case_id: str) -> Path:
        return Path(self.queries_path, case_id).with_suffix(".json")
