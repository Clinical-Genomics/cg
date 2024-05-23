from cg.meta.report.field_validators import get_million_read_pairs
from cg.meta.report.report_api import ReportAPI
from cg.models.analysis import NextflowAnalysis
from cg.models.cg_config import CGConfig
from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI
from cg.models.mip.mip_metrics_deliverables import get_sample_id_metric
from cg.models.raredisease.raredisease import RarediseaseQCMetrics
from cg.models.report.metadata import RarediseaseSampleMetadataModel
from cg.store.models import Case, Sample


class RarediseaseReportAPI(ReportAPI):
    """API to create Rare disease DNA delivery reports."""

    def __init__(self, config: CGConfig, analysis_api: RarediseaseAnalysisAPI):
        super().__init__(config=config, analysis_api=analysis_api)

    def get_sample_metadata(
        self, case: Case, sample: Sample, analysis_metadata: NextflowAnalysis
    ) -> RarediseaseSampleMetadataModel:
        """Return sample metadata to include in the report."""
        sample_metrics: RarediseaseQCMetrics = analysis_metadata.sample_metrics[sample.internal_id]

        sample_coverage: dict = self.get_sample_coverage(sample=sample, case=case)
        return RarediseaseSampleMetadataModel(
            bait_set=self.lims_api.capture_kit(lims_id=sample.internal_id),
            gender=sample_metrics.predicted_sex,
            million_read_pairs=get_million_read_pairs(reads=sample.reads),
            mapped_reads=sample_metrics.percentage_mapped_reads,
            mean_target_coverage=sample_coverage.get("mean_coverage"),
            pct_10x=sample_coverage.get("mean_completeness"),
            duplicates=sample_metrics.fraction_duplicates,
        )

    ##TODO #here it looks for chanjo API, need to add chanjo2 instead
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
        self, samples: list[SampleModel], analysis_metadata: NextflowAnalysis = None
    ) -> bool:
        """
        Return whether the delivery report is accredited by evaluating each of the sample
        process accreditations.
        """
        for sample in samples:
            if not sample.application.accredited:
                return False
        return True

    def get_scout_uploaded_files(self, case_id: str) -> ScoutReportFiles:
        """Return files that will be uploaded to Scout."""
        return ScoutReportFiles(
            snv_vcf=self.get_scout_uploaded_file_from_hk(case_id=case_id, scout_tag="snv_vcf"),
            sv_vcf=self.get_scout_uploaded_file_from_hk(case_id=case_id, scout_tag="sv_vcf"),
            vcf_str=self.get_scout_uploaded_file_from_hk(case_id=case_id, scout_tag="vcf_str"),
            smn_tsv=self.get_scout_uploaded_file_from_hk(case_id=case_id, scout_tag="smn_tsv"),
        )

    def get_required_fields(self, case: CaseModel) -> dict:
        """Return dictionary with the delivery report required fields for MIP DNA."""
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

    def get_upload_case_tags(self) -> dict:
        """Return MIP DNA upload case tags."""
        return MIP_CASE_TAGS

    def get_scout_uploaded_file_from_hk(self, case_id: str, scout_tag: str) -> str | None:
        """Return file path of the uploaded to Scout file given its tag."""
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
