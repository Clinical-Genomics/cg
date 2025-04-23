import logging
from typing import Iterable

from housekeeper.store.models import File, Version

from cg.constants import (
    REQUIRED_APPLICATION_FIELDS,
    REQUIRED_CASE_FIELDS,
    REQUIRED_CUSTOMER_FIELDS,
    REQUIRED_DATA_ANALYSIS_MIP_DNA_FIELDS,
    REQUIRED_REPORT_FIELDS,
    REQUIRED_SAMPLE_METADATA_MIP_DNA_FIELDS,
    REQUIRED_SAMPLE_METADATA_MIP_DNA_WGS_FIELDS,
    REQUIRED_SAMPLE_METHODS_FIELDS,
    REQUIRED_SAMPLE_MIP_DNA_FIELDS,
    REQUIRED_SAMPLE_TIMESTAMP_FIELDS,
)
from cg.constants.scout import ScoutUploadKey
from cg.meta.delivery_report.data_validators import get_million_read_pairs
from cg.meta.delivery_report.delivery_report_api import DeliveryReportAPI
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.models.delivery_report.metadata import MipDNASampleMetadataModel
from cg.models.delivery_report.report import CaseModel, ReportRequiredFields, ScoutVariantsFiles
from cg.models.delivery_report.sample import SampleModel
from cg.models.mip.mip_analysis import MipAnalysis
from cg.models.mip.mip_metrics_deliverables import get_sample_id_metric
from cg.store.models import Case, Sample

LOG = logging.getLogger(__name__)


class MipDNADeliveryReportAPI(DeliveryReportAPI):
    """API to create Rare disease DNA delivery reports."""

    def __init__(self, analysis_api: MipDNAAnalysisAPI):
        super().__init__(analysis_api=analysis_api)

    def get_sample_metadata(
        self, case: Case, sample: Sample, analysis_metadata: MipAnalysis
    ) -> MipDNASampleMetadataModel:
        """Return MIP DNA sample metadata to include in the report."""
        parsed_metrics = get_sample_id_metric(
            sample_id=sample.internal_id, sample_id_metrics=analysis_metadata.sample_id_metrics
        )
        sample_coverage: dict = self.get_sample_coverage(sample=sample, case=case)
        return MipDNASampleMetadataModel(
            bait_set=self.lims_api.capture_kit(sample.internal_id),
            duplicates=parsed_metrics.duplicate_reads,
            sex=parsed_metrics.predicted_sex,
            initial_qc=self.lims_api.has_sample_passed_initial_qc(sample.internal_id),
            mapped_reads=parsed_metrics.mapped_reads,
            mean_target_coverage=sample_coverage.get("mean_coverage"),
            million_read_pairs=get_million_read_pairs(sample.reads),
            pct_10x=sample_coverage.get("mean_completeness"),
        )

    def get_sample_coverage(self, sample: Sample, case: Case) -> dict:
        """Return coverage values for a specific sample."""
        genes = self.get_genes_from_scout(panels=case.panels)
        sample_coverage = self.chanjo_api.sample_coverage(
            sample_id=sample.internal_id, panel_genes=genes
        )
        if sample_coverage:
            return sample_coverage
        LOG.warning(f"Could not calculate sample coverage for: {sample.internal_id}")
        return dict()

    def get_genes_from_scout(self, panels: list) -> list:
        """Return panel gene IDs information from Scout."""
        panel_genes = list()
        for panel in panels:
            panel_genes.extend(self.scout_api.get_genes(panel))
        panel_gene_ids = [gene.get("hgnc_id") for gene in panel_genes]
        return panel_gene_ids

    def is_report_accredited(
        self, samples: list[SampleModel], analysis_metadata: MipAnalysis = None
    ) -> bool:
        """
        Return whether the MIP-DNA delivery report is accredited by evaluating each of the sample
        process accreditations.
        """
        for sample in samples:
            if not sample.application.accredited:
                return False
        return True

    def get_scout_variants_files(self, case_id: str) -> ScoutVariantsFiles:
        """Return files that will be uploaded to Scout."""
        return ScoutVariantsFiles(
            snv_vcf=self.get_scout_uploaded_file_from_hk(
                case_id=case_id, scout_key=ScoutUploadKey.SNV_VCF
            ),
            sv_vcf=self.get_scout_uploaded_file_from_hk(
                case_id=case_id, scout_key=ScoutUploadKey.SV_VCF
            ),
            vcf_str=self.get_scout_uploaded_file_from_hk(
                case_id=case_id, scout_key=ScoutUploadKey.VCF_STR
            ),
            smn_tsv=self.get_scout_uploaded_file_from_hk(
                case_id=case_id, scout_key=ScoutUploadKey.SMN_TSV
            ),
        )

    def get_required_fields(self, case: CaseModel) -> dict:
        """Return dictionary with the delivery report required fields for MIP DNA."""
        report_required_fields = ReportRequiredFields(
            applications=self.get_application_required_fields(
                case=case, required_fields=REQUIRED_APPLICATION_FIELDS
            ),
            case=REQUIRED_CASE_FIELDS,
            customer=REQUIRED_CUSTOMER_FIELDS,
            data_analysis=REQUIRED_DATA_ANALYSIS_MIP_DNA_FIELDS,
            metadata=self.get_sample_metadata_required_fields(case=case),
            methods=self.get_sample_required_fields(
                case=case, required_fields=REQUIRED_SAMPLE_METHODS_FIELDS
            ),
            report=REQUIRED_REPORT_FIELDS,
            samples=self.get_sample_required_fields(
                case=case, required_fields=REQUIRED_SAMPLE_MIP_DNA_FIELDS
            ),
            timestamps=self.get_timestamp_required_fields(
                case=case, required_fields=REQUIRED_SAMPLE_TIMESTAMP_FIELDS
            ),
        )
        return report_required_fields.model_dump()

    @staticmethod
    def get_sample_metadata_required_fields(case: CaseModel) -> dict:
        """Return sample metadata required fields associated to a specific sample ID."""
        required_sample_metadata_fields = dict()
        for sample in case.samples:
            required_fields = (
                REQUIRED_SAMPLE_METADATA_MIP_DNA_WGS_FIELDS
                if "wgs" in sample.application.prep_category.lower()
                else REQUIRED_SAMPLE_METADATA_MIP_DNA_FIELDS
            )
            required_sample_metadata_fields.update({sample.id: required_fields})
        return required_sample_metadata_fields

    def get_scout_uploaded_file_from_hk(
        self, case_id: str, scout_key: ScoutUploadKey
    ) -> str | None:
        """Return file path of the uploaded to Scout file given its tag."""
        version: Version = self.housekeeper_api.last_version(bundle=case_id)
        tags: list = self.get_hk_scout_file_tags(scout_key=scout_key)
        uploaded_files: Iterable[File] = self.housekeeper_api.get_files(
            bundle=case_id, tags=tags, version=version.id
        )
        if not tags or not any(uploaded_files):
            LOG.info(f"No files were found for the following Scout key: {scout_key}")
            return None
        return uploaded_files[0].full_path
