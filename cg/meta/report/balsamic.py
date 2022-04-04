import logging
from typing import List, Union

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
)
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.meta.report.api import ReportAPI
from cg.models.balsamic.analysis import BalsamicAnalysis
from cg.models.cg_config import CGConfig
from cg.models.report.metadata import (
    BalsamicTargetedSampleMetadataModel,
    BalsamicWGSSampleMetadataModel,
)
from cg.models.report.report import CaseModel
from cg.models.report.sample import SampleModel
from cg.store import models

LOG = logging.getLogger(__name__)


class BalsamicReportAPI(ReportAPI):
    """API to create BALSAMIC delivery reports"""

    def __init__(self, config: CGConfig, analysis_api: BalsamicAnalysisAPI):
        super().__init__(config=config, analysis_api=analysis_api)
        self.analysis_api = analysis_api

    def get_sample_metadata(
        self, case: models.Family, sample: models.Sample, analysis_metadata: BalsamicAnalysis
    ) -> Union[BalsamicTargetedSampleMetadataModel, BalsamicWGSSampleMetadataModel]:
        """Fetches the sample metadata to include in the report"""

        sample_metrics = (
            analysis_metadata.sample_metrics[sample.internal_id] if analysis_metadata else None
        )
        million_read_pairs = round(sample.reads / 2000000, 1) if sample.reads else None

        if "wgs" in self.get_data_analysis_type(case):
            return BalsamicWGSSampleMetadataModel(
                million_read_pairs=million_read_pairs,
                median_coverage=sample_metrics.median_coverage if sample_metrics else None,
                pct_15x=sample_metrics.pct_15x if sample_metrics else None,
                pct_60x=sample_metrics.pct_60x if sample_metrics else None,
                duplicates=sample_metrics.percent_duplication if sample_metrics else None,
                mean_insert_size=sample_metrics.mean_insert_size if sample_metrics else None,
                fold_80=sample_metrics.fold_80_base_penalty if sample_metrics else None,
            )
        else:
            return BalsamicTargetedSampleMetadataModel(
                bait_set=sample.capture_kit,
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

    def get_data_analysis_type(self, case: models.Family) -> str:
        """Retrieves the data analysis type carried out"""

        return self.analysis_api.get_bundle_deliverables_type(case.internal_id)

    def get_genome_build(self, analysis_metadata: BalsamicAnalysis) -> Union[None, str]:
        """Returns the build version of the genome reference of a specific case"""

        return (
            analysis_metadata.config.reference.reference_genome_version
            if analysis_metadata
            else None
        )

    def get_variant_callers(self, analysis_metadata: BalsamicAnalysis) -> Union[None, list]:
        """Extracts the list of BALSAMIC variant-calling filters from the config.json file"""

        if not analysis_metadata:
            return None

        sequencing_type = analysis_metadata.config.analysis.sequencing_type
        analysis_type = analysis_metadata.config.analysis.analysis_type
        var_callers = analysis_metadata.config.vcf

        analysis_var_callers = list()
        for var_caller, var_caller_attributes in var_callers.items():
            if (
                sequencing_type in var_caller_attributes.sequencing_type
                and analysis_type in var_caller_attributes.analysis_type
            ):
                analysis_var_callers.append(var_caller)

        return analysis_var_callers

    def get_report_accreditation(
        self, samples: List[SampleModel], analysis_metadata: BalsamicAnalysis
    ) -> Union[None, bool]:
        """Checks if the report is accredited or not"""

        if not analysis_metadata:
            return None

        if analysis_metadata.config.analysis.sequencing_type == "targeted" and next(
            (
                i
                for i in BALSAMIC_REPORT_ACCREDITED_PANELS
                if i in str(analysis_metadata.config.panel.capture_kit)
            ),
            None,
        ):
            return True

        return False

    def get_required_fields(self, case: CaseModel) -> dict:
        """Retrieves a dictionary with the delivery report required fields for BALSAMIC"""

        analysis_type = case.data_analysis.type
        required_sample_metadata_fields = list()

        if BALSAMIC_ANALYSIS_TYPE["tumor_wgs"] in analysis_type:
            required_sample_metadata_fields = REQUIRED_SAMPLE_METADATA_BALSAMIC_TO_WGS_FIELDS
        elif BALSAMIC_ANALYSIS_TYPE["tumor_normal_wgs"] in analysis_type:
            required_sample_metadata_fields = REQUIRED_SAMPLE_METADATA_BALSAMIC_TN_WGS_FIELDS
        elif (
            BALSAMIC_ANALYSIS_TYPE["tumor_panel"] in analysis_type
            or BALSAMIC_ANALYSIS_TYPE["tumor_normal_panel"] in analysis_type
        ):
            required_sample_metadata_fields = REQUIRED_SAMPLE_METADATA_BALSAMIC_TARGETED_FIELDS

        return {
            "report": REQUIRED_REPORT_FIELDS,
            "customer": REQUIRED_CUSTOMER_FIELDS,
            "case": REQUIRED_CASE_FIELDS,
            "applications": REQUIRED_APPLICATION_FIELDS,
            "data_analysis": REQUIRED_DATA_ANALYSIS_BALSAMIC_FIELDS,
            "samples": REQUIRED_SAMPLE_BALSAMIC_FIELDS,
            "methods": REQUIRED_SAMPLE_METHODS_FIELDS,
            "timestamp": REQUIRED_SAMPLE_TIMESTAMP_FIELDS,
            "metadata": required_sample_metadata_fields,
        }
