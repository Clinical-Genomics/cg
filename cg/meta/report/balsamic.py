import logging
from typing import List

from cg.constants import REPORT_ACCREDITED_PANELS
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.meta.report.api import ReportAPI
from cg.models.balsamic.analysis import BalsamicAnalysis
from cg.models.cg_config import CGConfig
from cg.models.report.sample import SampleMetadataModel, SampleModel
from cg.store import models

LOG = logging.getLogger(__name__)


class BalsamicReportAPI(ReportAPI):
    """API to create BALSAMIC delivery reports"""

    def __init__(self, config: CGConfig, analysis_api: BalsamicAnalysisAPI):
        super().__init__(config=config, analysis_api=analysis_api)
        self.analysis_api = analysis_api

    def get_sample_metadata(
        self, case: models.Family, sample: models.Sample, analysis_metadata: BalsamicAnalysis
    ) -> SampleMetadataModel:
        """Fetches the sample metadata to include in the report"""

        return SampleMetadataModel(
            bait_set=sample.capture_kit,
            bait_set_version=analysis_metadata.config.panel.capture_kit_version,
            million_read_pairs=round(sample.reads / 2000000, 1) if sample.reads else None,
            duplicates=analysis_metadata.sample_metrics[sample.internal_id].percent_duplication,
            median_coverage=analysis_metadata.sample_metrics[
                sample.internal_id
            ].median_target_coverage,
            mean_insert_size=analysis_metadata.sample_metrics[sample.internal_id].mean_insert_size,
            fold_80=analysis_metadata.sample_metrics[sample.internal_id].fold_80_base_penalty,
        )

    def get_data_analysis_type(self, case: models.Family) -> str:
        """Retrieves the data analysis type carried out"""

        return self.analysis_api.get_bundle_deliverables_type(case.internal_id)

    def get_genome_build(self, analysis_metadata: BalsamicAnalysis) -> str:
        """Returns the build version of the genome reference of a specific case"""

        return analysis_metadata.config.reference.reference_genome_version

    def get_variant_callers(self, analysis_metadata: BalsamicAnalysis) -> list:
        """Extracts the list of BALSAMIC variant-calling filters from the config.json file"""

        return analysis_metadata.config.vcf.keys()

    def get_report_accreditation(
        self, analysis_metadata: BalsamicAnalysis, samples: List[SampleModel]
    ) -> bool:
        """Checks if the report is accredited or not"""

        if analysis_metadata.config.analysis.sequencing_type == "targeted" and next(
            (
                i
                for i in REPORT_ACCREDITED_PANELS
                if i in analysis_metadata.config.panel.capture_kit
            ),
            None,
        ):
            return True

        return False
