import logging
from typing import List, Union, Optional, Dict

from housekeeper.store.models import Version, File

from cg.constants import (
    BALSAMIC_REPORT_ACCREDITED_PANELS,
    REQUIRED_REPORT_FIELDS,
    REQUIRED_CUSTOMER_FIELDS,
    REQUIRED_CASE_FIELDS,
    REQUIRED_APPLICATION_FIELDS,
    REQUIRED_DATA_ANALYSIS_BALSAMIC_FIELDS,
    REQUIRED_SAMPLE_BALSAMIC_FIELDS,
    REQUIRED_SAMPLE_METHODS_FIELDS,
    REQUIRED_SAMPLE_TIMESTAMP_FIELDS,
    REQUIRED_SAMPLE_METADATA_BALSAMIC_TARGETED_FIELDS,
    REQUIRED_SAMPLE_METADATA_BALSAMIC_TN_WGS_FIELDS,
    BALSAMIC_ANALYSIS_TYPE,
    REQUIRED_SAMPLE_METADATA_BALSAMIC_TO_WGS_FIELDS,
    Pipeline,
)
from cg.constants.scout_upload import BALSAMIC_CASE_TAGS
from cg.meta.report.field_validators import get_million_read_pairs
from cg.meta.report.report_api import ReportAPI
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.models.balsamic.analysis import BalsamicAnalysis
from cg.models.balsamic.config import BalsamicVarCaller
from cg.models.balsamic.metrics import (
    BalsamicTargetedQCMetrics,
    BalsamicWGSQCMetrics,
    BalsamicQCMetrics,
)
from cg.models.cg_config import CGConfig
from cg.models.report.metadata import (
    BalsamicTargetedSampleMetadataModel,
    BalsamicWGSSampleMetadataModel,
)
from cg.models.report.report import CaseModel
from cg.models.report.sample import SampleModel
from cg.store.models import Family, Sample, BedVersion, Bed

LOG = logging.getLogger(__name__)


class BalsamicReportAPI(ReportAPI):
    """API to create BALSAMIC delivery reports."""

    def __init__(self, config: CGConfig, analysis_api: BalsamicAnalysisAPI):
        super().__init__(config=config, analysis_api=analysis_api)
        self.analysis_api: BalsamicAnalysisAPI = analysis_api

    def get_sample_metadata(
        self, case: Family, sample: Sample, analysis_metadata: BalsamicAnalysis
    ) -> Union[BalsamicTargetedSampleMetadataModel, BalsamicWGSSampleMetadataModel]:
        """Return the sample metadata to include in the report."""
        sample_metrics: Dict[str, BalsamicQCMetrics] = analysis_metadata.sample_metrics[
            sample.internal_id
        ]
        million_read_pairs: float = get_million_read_pairs(reads=sample.reads)
        if "wgs" in self.get_data_analysis_type(case=case):
            return self.get_wgs_metadata(
                million_read_pairs=million_read_pairs, sample_metrics=sample_metrics
            )
        return self.get_panel_metadata(
            million_read_pairs=million_read_pairs,
            sample_metrics=sample_metrics,
            analysis_metadata=analysis_metadata,
        )

    def get_panel_metadata(
        self,
        million_read_pairs: float,
        sample_metrics: BalsamicTargetedQCMetrics,
        analysis_metadata: BalsamicAnalysis,
    ) -> BalsamicTargetedSampleMetadataModel:
        """Returns a report metadata for BALSAMIC TGS analysis."""
        bed_version: BedVersion = self.status_db.get_bed_version_by_file_name(
            analysis_metadata.config.panel.capture_kit
        )
        bed: Bed = self.status_db.get_bed_by_entry_id(bed_version.bed_id) if bed_version else None
        return BalsamicTargetedSampleMetadataModel(
            bait_set=bed.name if bed else None,
            bait_set_version=analysis_metadata.config.panel.capture_kit_version,
            million_read_pairs=million_read_pairs,
            median_target_coverage=sample_metrics.median_target_coverage
            if sample_metrics
            else None,
            pct_250x=sample_metrics.pct_target_bases_250x if sample_metrics else None,
            pct_500x=sample_metrics.pct_target_bases_500x if sample_metrics else None,
            duplicates=sample_metrics.percent_duplication if sample_metrics else None,
            mean_insert_size=sample_metrics.mean_insert_size if sample_metrics else None,
            fold_80=sample_metrics.fold_80_base_penalty if sample_metrics else None,
        )

    def get_wgs_metadata(
        self, million_read_pairs: float, sample_metrics: BalsamicWGSQCMetrics
    ) -> BalsamicWGSSampleMetadataModel:
        """Returns a report metadata for BALSAMIC WGS analysis."""
        return BalsamicWGSSampleMetadataModel(
            million_read_pairs=million_read_pairs,
            median_coverage=sample_metrics.median_coverage if sample_metrics else None,
            pct_15x=sample_metrics.pct_15x if sample_metrics else None,
            pct_60x=sample_metrics.pct_60x if sample_metrics else None,
            duplicates=self.get_wgs_percent_duplication(sample_metrics=sample_metrics),
            mean_insert_size=sample_metrics.mean_insert_size if sample_metrics else None,
            fold_80=sample_metrics.fold_80_base_penalty if sample_metrics else None,
        )

    @staticmethod
    def get_wgs_percent_duplication(sample_metrics: BalsamicWGSQCMetrics):
        """Returns the duplication percentage taking into account both reads."""
        return (
            (sample_metrics.percent_duplication_r1 + sample_metrics.percent_duplication_r2) / 2
            if sample_metrics
            else None
        )

    def get_data_analysis_type(self, case: Family) -> Optional[str]:
        """Retrieves the data analysis type carried out."""
        return self.analysis_api.get_bundle_deliverables_type(case_id=case.internal_id)

    def get_genome_build(self, analysis_metadata: BalsamicAnalysis) -> str:
        """Returns the build version of the genome reference of a specific case."""
        return analysis_metadata.config.reference.reference_genome_version

    def get_variant_callers(self, _analysis_metadata: BalsamicAnalysis) -> list:
        """
        Extracts the list of BALSAMIC variant-calling filters and their versions (if available) from the
        config.json file.
        """
        sequencing_type: str = _analysis_metadata.config.analysis.sequencing_type
        analysis_type: str = _analysis_metadata.config.analysis.analysis_type
        var_callers: Dict[str, BalsamicVarCaller] = _analysis_metadata.config.vcf
        tool_versions: Dict[str, list] = _analysis_metadata.config.bioinfo_tools_version
        analysis_var_callers = list()
        for var_caller_name, var_caller_attributes in var_callers.items():
            if (
                sequencing_type in var_caller_attributes.sequencing_type
                and analysis_type in var_caller_attributes.analysis_type
            ):
                version: str = self.get_variant_caller_version(
                    var_caller_name=var_caller_name, var_caller_versions=tool_versions
                )
                analysis_var_callers.append(
                    f"{var_caller_name} (v{version})" if version else var_caller_name
                )
        return analysis_var_callers

    @staticmethod
    def get_variant_caller_version(
        var_caller_name: str, var_caller_versions: dict
    ) -> Optional[str]:
        """Returns the version of a specific BALSAMIC tool."""
        for tool_name, versions in var_caller_versions.items():
            if tool_name in var_caller_name:
                return versions[0]
        return None

    def get_report_accreditation(
        self, samples: List[SampleModel], analysis_metadata: BalsamicAnalysis
    ) -> bool:
        """Checks if the report is accredited or not."""
        if analysis_metadata.config.analysis.sequencing_type == "targeted" and next(
            (
                panel
                for panel in BALSAMIC_REPORT_ACCREDITED_PANELS
                if panel in str(analysis_metadata.config.panel.capture_kit)
            ),
            None,
        ):
            return True
        return False

    def get_required_fields(self, case: CaseModel) -> dict:
        """Retrieves a dictionary with the delivery report required fields for BALSAMIC."""
        analysis_type: str = case.data_analysis.type
        required_sample_metadata_fields: List[str] = []
        if BALSAMIC_ANALYSIS_TYPE["tumor_wgs"] in analysis_type:
            required_sample_metadata_fields: List[
                str
            ] = REQUIRED_SAMPLE_METADATA_BALSAMIC_TO_WGS_FIELDS
        elif BALSAMIC_ANALYSIS_TYPE["tumor_normal_wgs"] in analysis_type:
            required_sample_metadata_fields: List[
                str
            ] = REQUIRED_SAMPLE_METADATA_BALSAMIC_TN_WGS_FIELDS
        elif (
            BALSAMIC_ANALYSIS_TYPE["tumor_panel"] in analysis_type
            or BALSAMIC_ANALYSIS_TYPE["tumor_normal_panel"] in analysis_type
        ):
            required_sample_metadata_fields: List[
                str
            ] = REQUIRED_SAMPLE_METADATA_BALSAMIC_TARGETED_FIELDS
        return {
            "report": REQUIRED_REPORT_FIELDS,
            "customer": REQUIRED_CUSTOMER_FIELDS,
            "case": REQUIRED_CASE_FIELDS,
            "applications": self.get_application_required_fields(
                case=case, required_fields=REQUIRED_APPLICATION_FIELDS
            ),
            "data_analysis": REQUIRED_DATA_ANALYSIS_BALSAMIC_FIELDS,
            "samples": self.get_sample_required_fields(
                case=case, required_fields=REQUIRED_SAMPLE_BALSAMIC_FIELDS
            ),
            "methods": self.get_sample_required_fields(
                case=case, required_fields=REQUIRED_SAMPLE_METHODS_FIELDS
            ),
            "timestamps": self.get_timestamp_required_fields(
                case=case, required_fields=REQUIRED_SAMPLE_TIMESTAMP_FIELDS
            ),
            "metadata": self.get_sample_required_fields(
                case=case, required_fields=required_sample_metadata_fields
            ),
        }

    def get_template_name(self) -> str:
        """Retrieves the template name to render the delivery report."""
        return Pipeline.BALSAMIC + "_report.html"

    def get_upload_case_tags(self) -> dict:
        """Retrieves BALSAMIC upload case tags."""
        return BALSAMIC_CASE_TAGS

    def get_scout_uploaded_file_from_hk(self, case_id: str, scout_tag: str) -> Optional[str]:
        """Return the file path of the uploaded to Scout file given its tag."""
        version: Version = self.housekeeper_api.last_version(bundle=case_id)
        tags: list = self.get_hk_scout_file_tags(scout_tag=scout_tag)
        uploaded_file: File = self.housekeeper_api.get_latest_file(
            bundle=case_id, tags=tags, version=version.id
        )
        if not tags or not uploaded_file:
            LOG.warning(
                f"No files were found for the following Scout Housekeeper tag: {scout_tag} (case: {case_id})"
            )
            return None
        return uploaded_file.full_path
