import logging

from housekeeper.store.models import Version

from cg.apps.lims import LimsAPI
from cg.constants.housekeeper_tags import HK_DELIVERY_REPORT_TAG
from cg.constants.scout import RNAFUSION_CASE_TAGS, RNAFUSION_SAMPLE_TAGS, GenomeBuild, UploadTrack
from cg.meta.upload.scout.hk_tags import CaseTags, SampleTags
from cg.meta.upload.scout.scout_config_builder import ScoutConfigBuilder
from cg.models.scout.scout_load_config import RnafusionLoadConfig, ScoutCancerIndividual
from cg.store.models import Analysis, CaseSample

LOG = logging.getLogger(__name__)


class RnafusionConfigBuilder(ScoutConfigBuilder):
    """Class for handling rnafusion information and files to be included in Scout upload."""

    def __init__(self, lims_api: LimsAPI):
        super().__init__(
            lims_api=lims_api,
        )
        self.case_tags: CaseTags = CaseTags(**RNAFUSION_CASE_TAGS)
        self.sample_tags: SampleTags = SampleTags(**RNAFUSION_SAMPLE_TAGS)

    def build_load_config(self, hk_version: Version, analysis: Analysis) -> RnafusionLoadConfig:
        """Build a rnafusion-specific load config for uploading a case to scout."""
        LOG.info("Build load config for rnafusion case")
        load_config: RnafusionLoadConfig = RnafusionLoadConfig(
            track=UploadTrack.CANCER.value,
            delivery_report=self.get_file_from_hk(
                hk_tags={HK_DELIVERY_REPORT_TAG}, hk_version=hk_version
            ),
        )
        self.add_common_info_to_load_config(load_config=load_config, analysis=analysis)
        load_config.human_genome_build = GenomeBuild.hg38
        self.include_case_files(load_config=load_config, hk_version=hk_version)
        LOG.info("Building samples")
        db_sample: CaseSample
        for db_sample in analysis.case.links:
            load_config.samples.append(
                self.build_config_sample(case_sample=db_sample, hk_version=hk_version)
            )
        return load_config

    def include_case_files(
        self, load_config: RnafusionLoadConfig, hk_version: Version = None
    ) -> None:
        """Include case level files for rnafusion case."""
        LOG.info("Including RNAFUSION specific case level files")
        for scout_key in RNAFUSION_CASE_TAGS.keys():
            self._include_file(load_config, scout_key, hk_version=hk_version)

    def include_sample_alignment_file(
        self, config_sample: ScoutCancerIndividual, hk_version: Version
    ) -> None:
        """Include the alignment file for a sample
        Try if cram file is found, if not: load bam file
        """
        sample_id: str = config_sample.sample_id
        config_sample.rna_alignment_path = self.get_sample_file(
            hk_tags=self.sample_tags.alignment_file,
            sample_id=sample_id,
            hk_version=hk_version,
        )

    def _include_file(
        self, load_config: RnafusionLoadConfig, scout_key: str, hk_version: Version
    ) -> None:
        """Include the file path associated to a scout configuration parameter if the corresponding housekeeper tags
        are found. Otherwise return None."""
        setattr(
            load_config,
            scout_key,
            self.get_file_from_hk(
                hk_tags=getattr(self.case_tags, scout_key), hk_version=hk_version
            ),
        )

    def include_sample_files(
        self, config_sample: ScoutCancerIndividual, hk_version: Version
    ) -> None:
        """Include all files that are used on sample level in Scout."""
        return None
