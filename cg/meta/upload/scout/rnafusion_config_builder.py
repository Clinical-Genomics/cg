import logging

from housekeeper.store.models import Version

from cg.apps.lims import LimsAPI
from cg.constants.constants import PrepCategory
from cg.constants.scout_upload import RNAFUSION_CASE_TAGS, RNAFUSION_SAMPLE_TAGS, GenomeBuild
from cg.meta.upload.scout.hk_tags import CaseTags, SampleTags
from cg.meta.upload.scout.scout_config_builder import ScoutConfigBuilder
from cg.models.scout.scout_load_config import RnafusionLoadConfig, ScoutCancerIndividual
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

    def include_case_files(self) -> None:
        """Include case level files for rnafusion case."""
        LOG.info("Including RNAFUSION specific case level files")
        for scout_key in RNAFUSION_CASE_TAGS.keys():
            self._include_file(scout_key)

    def _include_file(self, scout_key) -> None:
        """Include the file path associated to a scout configuration parameter if the corresponding housekeeper tags
        are found. Otherwise return None."""
        setattr(
            self.load_config,
            scout_key,
            self.get_file_from_hk(getattr(self.case_tags, scout_key)),
        )

    def build_config_sample(self, case_sample: FamilySample) -> ScoutCancerIndividual:
        """Build a sample with rnafusion specific information."""
        config_sample = ScoutCancerIndividual()

        self.add_common_sample_info(config_sample=config_sample, case_sample=case_sample)

        config_sample.analysis_type = PrepCategory.WHOLE_TRANSCRIPTOME_SEQUENCING.value

        return config_sample
