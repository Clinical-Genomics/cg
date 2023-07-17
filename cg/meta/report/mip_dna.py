import logging
from typing import List, Optional, Iterable

from housekeeper.store.models import Version, File

from cg.constants import (
    REQUIRED_REPORT_FIELDS,
    REQUIRED_CUSTOMER_FIELDS,
    REQUIRED_CASE_FIELDS,
    REQUIRED_APPLICATION_FIELDS,
    REQUIRED_DATA_ANALYSIS_MIP_DNA_FIELDS,
    REQUIRED_SAMPLE_MIP_DNA_FIELDS,
    REQUIRED_SAMPLE_METHODS_FIELDS,
    REQUIRED_SAMPLE_TIMESTAMP_FIELDS,
    REQUIRED_SAMPLE_METADATA_MIP_DNA_FIELDS,
    REQUIRED_SAMPLE_METADATA_MIP_DNA_WGS_FIELDS,
    Pipeline,
)
from cg.constants.scout_upload import MIP_CASE_TAGS
from cg.meta.report.field_validators import get_million_read_pairs
from cg.meta.report.report_api import ReportAPI
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.models.mip.mip_analysis import MipAnalysis
from cg.models.mip.mip_metrics_deliverables import get_sample_id_metric
from cg.models.report.metadata import MipDNASampleMetadataModel
from cg.models.report.report import CaseModel
from cg.models.report.sample import SampleModel
from cg.store.models import Family, Sample

LOG = logging.getLogger(__name__)


class MipDNAReportAPI(ReportAPI):
    """API to create Rare disease DNA delivery reports."""

    def __init__(self, config: CGConfig, analysis_api: MipDNAAnalysisAPI):
        super().__init__(config=config, analysis_api=analysis_api)
        self.analysis_api: MipDNAAnalysisAPI = analysis_api

    def get_sample_metadata(
        self, case: Family, sample: Sample, analysis_metadata: MipAnalysis
    ) -> MipDNASampleMetadataModel:
        """Fetches the MIP DNA sample metadata to include in the report."""
        parsed_metrics = get_sample_id_metric(
            sample_id=sample.internal_id, sample_id_metrics=analysis_metadata.sample_id_metrics
        )
        sample_coverage: dict = self.get_sample_coverage(sample=sample, case=case)
        return MipDNASampleMetadataModel(
            bait_set=self.lims_api.capture_kit(lims_id=sample.internal_id),
            gender=parsed_metrics.predicted_sex,
            million_read_pairs=get_million_read_pairs(reads=sample.reads),
            mapped_reads=parsed_metrics.mapped_reads,
            mean_target_coverage=sample_coverage.get("mean_coverage"),
            pct_10x=sample_coverage.get("mean_completeness"),
            duplicates=parsed_metrics.duplicate_reads,
        )

    def get_sample_coverage(self, sample: Sample, case: Family) -> dict:
        """Calculates coverage values for a specific sample."""
        genes = self.get_genes_from_scout(panels=case.panels)
        sample_coverage = self.chanjo_api.sample_coverage(
            sample_id=sample.internal_id, panel_genes=genes
        )
        if sample_coverage:
            return sample_coverage
        LOG.warning("Could not calculate sample coverage for: %s", sample.internal_id)
        return dict()

    def get_genes_from_scout(self, panels: list) -> list:
        """Extracts panel gene IDs information from Scout."""
        panel_genes = list()
        for panel in panels:
            panel_genes.extend(self.scout_api.get_genes(panel))
        panel_gene_ids = [gene.get("hgnc_id") for gene in panel_genes]
        return panel_gene_ids

    def get_genome_build(self, analysis_metadata: MipAnalysis) -> str:
        """Returns the build version of the genome reference of a specific case."""
        return analysis_metadata.genome_build

    def get_report_accreditation(
        self, samples: List[SampleModel], analysis_metadata: MipAnalysis = None
    ) -> bool:
        """Checks if the report is accredited or not by evaluating each of the sample process accreditations."""
        for sample in samples:
            if not sample.application.accredited:
                return False
        return True

    def get_required_fields(self, case: CaseModel) -> dict:
        """Retrieves a dictionary with the delivery report required fields for MIP DNA."""
        return {
            "report": REQUIRED_REPORT_FIELDS,
            "customer": REQUIRED_CUSTOMER_FIELDS,
            "case": REQUIRED_CASE_FIELDS,
            "applications": self.get_application_required_fields(
                case=case, required_fields=REQUIRED_APPLICATION_FIELDS
            ),
            "data_analysis": REQUIRED_DATA_ANALYSIS_MIP_DNA_FIELDS,
            "samples": self.get_sample_required_fields(
                case=case, required_fields=REQUIRED_SAMPLE_MIP_DNA_FIELDS
            ),
            "methods": self.get_sample_required_fields(
                case=case, required_fields=REQUIRED_SAMPLE_METHODS_FIELDS
            ),
            "timestamps": self.get_timestamp_required_fields(
                case=case, required_fields=REQUIRED_SAMPLE_TIMESTAMP_FIELDS
            ),
            "metadata": self.get_sample_metadata_required_fields(case=case),
        }

    @staticmethod
    def get_sample_metadata_required_fields(case: CaseModel) -> dict:
        """Retrieves sample metadata required fields associated to a specific sample ID."""
        required_sample_metadata_fields = dict()
        for sample in case.samples:
            required_fields = (
                REQUIRED_SAMPLE_METADATA_MIP_DNA_WGS_FIELDS
                if "wgs" in sample.application.prep_category.lower()
                else REQUIRED_SAMPLE_METADATA_MIP_DNA_FIELDS
            )
            required_sample_metadata_fields.update({sample.id: required_fields})
        return required_sample_metadata_fields

    def get_template_name(self) -> str:
        """Retrieves the template name to render the delivery report."""
        return Pipeline.MIP_DNA + "_report.html"

    def get_upload_case_tags(self) -> dict:
        """Retrieves MIP DNA upload case tags."""
        return MIP_CASE_TAGS

    def get_scout_uploaded_file_from_hk(self, case_id: str, scout_tag: str) -> Optional[str]:
        """Returns the file path of the uploaded to Scout file given its tag."""
        version: Version = self.housekeeper_api.last_version(bundle=case_id)
        tags: list = self.get_hk_scout_file_tags(scout_tag=scout_tag)
        uploaded_files: Iterable[File] = self.housekeeper_api.get_files(
            bundle=case_id, tags=tags, version=version.id
        )
        if not tags or not any(uploaded_files):
            LOG.info(
                f"No files were found for the following Scout Housekeeper tag: {scout_tag} (case: {case_id})"
            )
            return None
        return uploaded_files[0].full_path
