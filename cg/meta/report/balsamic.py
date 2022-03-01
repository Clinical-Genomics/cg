import logging

from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.meta.report.api import ReportAPI
from cg.models.cg_config import CGConfig
from cg.models.report.sample import MetadataModel
from cg.store import models

LOG = logging.getLogger(__name__)


class BalsamicReportAPI(ReportAPI):
    """API to create BALSAMIC delivery reports"""

    def __init__(self, config: CGConfig, analysis_api: BalsamicAnalysisAPI):
        super().__init__(config=config, analysis_api=analysis_api)
        self.analysis_api = analysis_api

    def get_metadata(self, sample: models.Sample, case: models.Family) -> MetadataModel:
        """Fetches the sample metadata to include in the report"""

        metadata = self.analysis_api.get_latest_metadata(case.internal_id)

        return MetadataModel(
            bait_set=sample.capture_kit,
            bait_set_version=metadata.config.panel.capture_kit_version,
            million_read_pairs=round(sample.reads / 2000000, 1) if sample.reads else None,
            duplicates=metadata.sample_metrics[sample.internal_id].percent_duplication,
            median_coverage=metadata.sample_metrics[sample.internal_id].median_target_coverage,
            mean_insert_size=metadata.sample_metrics[sample.internal_id].mean_insert_size,
            fold_80=metadata.sample_metrics[sample.internal_id].fold_80_base_penalty,
        )

    def get_data_analysis_type(self, case: models.Family) -> str:
        """Retrieves the data analysis type carried out"""

        return self.analysis_api.get_bundle_deliverables_type(case.internal_id)

    def get_genome_build(self, case: models.Family) -> str:
        """Returns the build version of the genome reference of a specific case"""

        return self.analysis_api.get_latest_metadata(
            case.internal_id
        ).config.reference.reference_genome_version

    def get_variant_callers(self, case: models.Family) -> list:
        """Extracts the list of BALSAMIC variant-calling filters from the config.json file"""

        return self.analysis_api.get_latest_metadata(case.internal_id).config.vcf.keys()
