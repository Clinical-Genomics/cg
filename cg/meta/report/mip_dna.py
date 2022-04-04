import logging
from typing import List, Union

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
)
from cg.models.cg_config import CGConfig
from cg.meta.report.api import ReportAPI
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.models.mip.mip_analysis import MipAnalysis
from cg.models.report.metadata import MipDNASampleMetadataModel
from cg.models.report.sample import SampleModel
from cg.models.mip.mip_metrics_deliverables import get_sample_id_metric
from cg.store import models

LOG = logging.getLogger(__name__)


class MipDNAReportAPI(ReportAPI):
    """API to create Rare disease DNA delivery reports"""

    def __init__(self, config: CGConfig, analysis_api: MipDNAAnalysisAPI):
        super().__init__(config=config, analysis_api=analysis_api)
        self.analysis_api = analysis_api

    def get_sample_metadata(
        self, case: models.Family, sample: models.Sample, analysis_metadata: MipAnalysis
    ) -> MipDNASampleMetadataModel:
        """Fetches the MIP DNA sample metadata to include in the report"""

        parsed_metrics = (
            get_sample_id_metric(
                sample_id=sample.internal_id, sample_id_metrics=analysis_metadata.sample_id_metrics
            )
            if analysis_metadata
            else None
        )
        sample_coverage = self.get_sample_coverage(sample, case)

        return MipDNASampleMetadataModel(
            bait_set=sample.capture_kit,
            gender=parsed_metrics.predicted_sex if analysis_metadata else None,
            million_read_pairs=round(sample.reads / 2000000, 1) if sample.reads else None,
            mapped_reads=parsed_metrics.mapped_reads if analysis_metadata else None,
            mean_target_coverage=sample_coverage.get("mean_coverage"),
            pct_10x=sample_coverage.get("mean_completeness"),
            duplicates=parsed_metrics.duplicate_reads if analysis_metadata else None,
        )

    def get_sample_coverage(self, sample: models.Sample, case: models.Family) -> dict:
        """Calculates coverage values for a specific sample"""

        genes = self.get_genes_from_scout(case.panels)
        sample_coverage = self.chanjo_api.sample_coverage(sample.internal_id, genes)
        if sample_coverage:
            return sample_coverage

        LOG.warning("Could not calculate sample coverage for: %s", sample.internal_id)
        return dict()

    def get_genes_from_scout(self, panels: list) -> list:
        """Extracts panel gene IDs information from Scout"""

        panel_genes = list()
        for panel in panels:
            panel_genes.extend(self.scout_api.get_genes(panel))

        panel_gene_ids = [gene.get("hgnc_id") for gene in panel_genes]
        return panel_gene_ids

    def get_data_analysis_type(self, case: models.Family) -> str:
        """Retrieves the data analysis type carried out"""

        case_sample = self.status_db.family_samples(case.internal_id)[0].sample
        lims_sample = self.get_lims_sample(case_sample.internal_id)
        application = self.status_db.application(tag=lims_sample.get("application"))

        return application.analysis_type

    def get_genome_build(self, analysis_metadata: MipAnalysis) -> Union[None, str]:
        """Returns the build version of the genome reference of a specific case"""

        return analysis_metadata.genome_build if analysis_metadata else None

    def get_report_accreditation(self, samples: List[SampleModel]) -> Union[None, bool]:
        """Checks if the report is accredited or not by evaluating each of the sample process accreditations"""

        for sample in samples:
            if not sample.application.accredited:
                return False

        return True

    def get_required_fields(self) -> dict:
        """Retrieves a dictionary with the delivery report required fields for MIP DNA"""

        return {
            "report": REQUIRED_REPORT_FIELDS,
            "customer": REQUIRED_CUSTOMER_FIELDS,
            "case": REQUIRED_CASE_FIELDS,
            "applications": REQUIRED_APPLICATION_FIELDS,
            "data_analysis": REQUIRED_DATA_ANALYSIS_MIP_DNA_FIELDS,
            "samples": REQUIRED_SAMPLE_MIP_DNA_FIELDS,
            "methods": REQUIRED_SAMPLE_METHODS_FIELDS,
            "timestamps": REQUIRED_SAMPLE_TIMESTAMP_FIELDS,
            "metadata": REQUIRED_SAMPLE_METADATA_MIP_DNA_FIELDS,
        }
