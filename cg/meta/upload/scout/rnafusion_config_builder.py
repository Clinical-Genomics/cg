import logging

from housekeeper.store.models import Version

from cg.apps.lims import LimsAPI
from cg.constants.constants import PrepCategory
from cg.constants.scout_upload import RNAFUSION_CASE_TAGS, RNAFUSION_SAMPLE_TAGS, GenomeBuild
from cg.meta.upload.scout.hk_tags import CaseTags, SampleTags
from cg.meta.upload.scout.scout_config_builder import ScoutConfigBuilder
from cg.meta.workflow.rnafusion import RnafusionAnalysisAPI
from cg.models.scout.scout_load_config import RnafusionLoadConfig, ScoutRnafusionIndividual
from cg.store.models import Analysis, FamilySample

LOG = logging.getLogger(__name__)


class RnafusionConfigBuilder(ScoutConfigBuilder):
    """Class for handling rnafusion information and files to be included in Scout upload."""

    def __init__(self, hk_version_obj: Version, analysis_obj: Analysis, lims_api: LimsAPI):
        super().__init__(
            hk_version_obj=hk_version_obj, analysis_obj=analysis_obj, lims_api=lims_api
        )
        self.case_tags: CaseTags = CaseTags(**RNAFUSION_CASE_TAGS)
        self.sample_tags: SampleTags = SampleTags(**RNAFUSION_SAMPLE_TAGS)
        self.load_config: RnafusionLoadConfig = RnafusionLoadConfig(track="cancer")

    def build_load_config(self) -> None:
        """Build a rnafusion-specific load config for uploading a case to scout."""
        LOG.info("Build load config for rnafusion case")
        self.add_common_info_to_load_config()
        self.load_config.human_genome_build = GenomeBuild.hg38
        self.include_case_files()

        LOG.info("Building samples")
        db_sample: FamilySample

        for db_sample in self.analysis_obj.family.links:
            self.load_config.samples.append(self.build_config_sample(case_sample=db_sample))

    def include_case_files(self):
        """Include case level files for rnafusion case."""
        LOG.info("Including RNAFUSION specific case level files")
        self.load_config.multiqc_rna = self.fetch_file_from_hk(self.case_tags.multiqc_report)
        self.load_config.gene_fusion = self.fetch_file_from_hk(self.case_tags.genefusion_report)
        self.load_config.gene_fusion_research = self.fetch_file_from_hk(
            self.case_tags.genefusion_report_research
        )
        self.load_config.RNAfusion_inspector = self.fetch_file_from_hk(
            self.case_tags.rnafusion_inspector
        )
        self.load_config.RNAfusion_inspector_research = self.fetch_file_from_hk(
            self.case_tags.rnafusion_inspector_research
        )
        self.load_config.RNAfusion_report = self.fetch_file_from_hk(self.case_tags.rnafusion_report)
        self.load_config.RNAfusion_report_research = self.fetch_file_from_hk(
            self.case_tags.rnafusion_report_research
        )

    def build_config_sample(self, case_sample: FamilySample) -> ScoutRnafusionIndividual:
        """Build a sample with rnafusion specific information."""
        config_sample = ScoutRnafusionIndividual()

        self.add_common_sample_info(config_sample=config_sample, case_sample=case_sample)

        config_sample.analysis_type = PrepCategory.WHOLE_TRANSCRIPTOME_SEQUENCING.value

        return config_sample
