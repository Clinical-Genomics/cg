import logging

from housekeeper.store.models import Version

from cg.apps.lims import LimsAPI
from cg.constants.housekeeper_tags import HK_DELIVERY_REPORT_TAG
from cg.constants.scout import RNAFUSION_CASE_TAGS, RNAFUSION_SAMPLE_TAGS, GenomeBuild, UploadTrack
from cg.meta.upload.scout.hk_tags import CaseTags, SampleTags
from cg.meta.upload.scout.scout_config_builder import ScoutConfigBuilder
from cg.models.scout.scout_load_config import (
    RnafusionLoadConfig,
    ScoutCancerIndividual,
)
from cg.store.models import Analysis, CaseSample

LOG = logging.getLogger(__name__)


class RnafusionConfigBuilder(ScoutConfigBuilder):
    """Class for handling rnafusion information and files to be included in Scout upload."""

    def __init__(self, hk_version_obj: Version, analysis_obj: Analysis, lims_api: LimsAPI):
        super().__init__(
            hk_version_obj=hk_version_obj,
            analysis_obj=analysis_obj,
            lims_api=lims_api,
        )
        self.case_tags: CaseTags = CaseTags(**RNAFUSION_CASE_TAGS)
        self.sample_tags: SampleTags = SampleTags(**RNAFUSION_SAMPLE_TAGS)

    def build_load_config(self) -> RnafusionLoadConfig:
        """Build a rnafusion-specific load config for uploading a case to scout."""
        LOG.info("Build load config for rnafusion case")
        load_config: RnafusionLoadConfig = RnafusionLoadConfig(
            track=UploadTrack.CANCER.value,
            delivery_report=self.get_file_from_hk({HK_DELIVERY_REPORT_TAG}),
        )
        self.add_common_info_to_load_config(load_config)
        load_config.human_genome_build = GenomeBuild.hg38
        self.include_case_files(load_config)
        LOG.info("Building samples")
        db_sample: CaseSample
        for db_sample in self.analysis_obj.case.links:
            load_config.samples.append(self.build_config_sample(case_sample=db_sample))
        return load_config

    def include_case_files(self, load_config: RnafusionLoadConfig) -> None:
        """Include case level files for rnafusion case."""
        LOG.info("Including RNAFUSION specific case level files")
        for scout_key in RNAFUSION_CASE_TAGS.keys():
            self._include_file(load_config, scout_key)

    def include_sample_alignment_file(self, config_sample: ScoutCancerIndividual) -> None:
        """Include the alignment file for a sample
        Try if cram file is found, if not: load bam file
        """
        sample_id: str = config_sample.sample_id
        config_sample.rna_alignment_path = self.get_sample_file(
            hk_tags=self.sample_tags.alignment_file, sample_id=sample_id
        )

    def _include_file(self, load_config: RnafusionLoadConfig, scout_key: str) -> None:
        """Include the file path associated to a scout configuration parameter if the corresponding housekeeper tags
        are found. Otherwise return None."""
        setattr(
            load_config,
            scout_key,
            self.get_file_from_hk(getattr(self.case_tags, scout_key)),
        )

    def include_sample_files(self, config_sample: ScoutCancerIndividual) -> None:
        """Include all files that are used on sample level in Scout."""
        return None
