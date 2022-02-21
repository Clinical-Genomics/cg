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

        return MetadataModel(
            bait_set=sample.capture_kit,
            bait_set_version="",
            gender="",
            million_read_pairs=round(sample.reads / 2000000, 1) if sample.reads else None,
            duplicates=None,
            # PANEL: PERCENT_DUPLICATION
            # WGS: pct_duplication/percent_duplicates **???**
            target_bases_250X=None,
            # PANEL: PCT_TARGET_BASES_250X
            # WGS: not supported
            target_bases_500X=None,
            # PANEL: PCT_TARGET_BASES_500X
            # WGS: not supported
            median_coverage=None,
            # PANEL: MEDIAN_TARGET_COVERAGE
            # WGS: MEDIAN_COVERAGE
            mean_insert_size=None,
            # PANEL: MEAN_INSERT_SIZE
            # WGS: MEAN_INSERT_SIZE
            fold_80=None,
            # PANEL: FOLD_80_BASE_PENALTY
            # WGS: FOLD_80_BASE_PENALTY
        )

    def get_data_analysis_type(self, case: models.Family) -> str:
        """Retrieves the data analysis type carried out"""

        return self.analysis_api.get_bundle_deliverables_type(case.internal_id)

    def get_genome_build(self, case: models.Family) -> str:
        """Returns the build version of the genome reference of a specific case"""

        # TODO
        # config.json - "reference" - "reference_genome" –
        # "/home/proj/stage/cancer/balsamic_cache/8.2.5/hg19/genome/human_g1k_v37.fasta"
        pass
