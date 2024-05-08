import logging

from housekeeper.store.models import Version

from cg.apps.lims import LimsAPI
from cg.constants.constants import PrepCategory
from cg.constants.housekeeper_tags import HK_DELIVERY_REPORT_TAG
from cg.constants.scout import TOMTE_CASE_TAGS, TOMTE_SAMPLE_TAGS, GenomeBuild, UploadTrack
from cg.constants.subject import RelationshipStatus
from cg.meta.upload.scout.hk_tags import CaseTags, SampleTags
from cg.meta.upload.scout.scout_config_builder import ScoutConfigBuilder
from cg.models.scout.scout_load_config import ScoutRnaIndividual, TomteLoadConfig
from cg.store.models import Analysis, CaseSample

LOG = logging.getLogger(__name__)


class TomteConfigBuilder(ScoutConfigBuilder):
    """Class for handling Tomte information and files to be included in Scout upload."""

    def __init__(self, hk_version_obj: Version, analysis_obj: Analysis, lims_api: LimsAPI):
        super().__init__(
            hk_version_obj=hk_version_obj, analysis_obj=analysis_obj, lims_api=lims_api
        )
        self.case_tags: CaseTags = CaseTags(**TOMTE_CASE_TAGS)
        self.sample_tags: SampleTags = SampleTags(**TOMTE_SAMPLE_TAGS)
        self.load_config: TomteLoadConfig = TomteLoadConfig(
            track=UploadTrack.RARE_DISEASE.value,
            delivery_report=self.get_file_from_hk({HK_DELIVERY_REPORT_TAG}),
        )

    def build_load_config(self) -> None:
        """Build a Tomte-specific load config for uploading a case to scout."""
        LOG.info("Build load config for tomte case")
        self.add_common_info_to_load_config()
        self.load_config.human_genome_build = GenomeBuild.hg38
        self.include_case_files()

        LOG.info("Building samples")
        db_sample: CaseSample

        for db_sample in self.analysis_obj.case.links:
            self.load_config.samples.append(self.build_config_sample(case_sample=db_sample))

    def include_case_files(self) -> None:
        """Include case level files for Tomte case."""
        LOG.info("Including Tomte specific case level files")
        for scout_key in TOMTE_CASE_TAGS.keys():
            self._include_file(scout_key)

    def _include_file(self, scout_key) -> None:
        """Include the file path associated to a scout configuration parameter if the corresponding housekeeper tags
        are found. Otherwise return None."""
        setattr(
            self.load_config,
            scout_key,
            self.get_file_from_hk(getattr(self.case_tags, scout_key)),
        )

    def include_sample_files(self, config_sample: ScoutRnaIndividual) -> None:
        """Include sample level files that are optional for mip samples"""
        LOG.info("Including Tomte specific sample level files")
        self.include_sample_rna_alignment_file(config_sample=config_sample)
        self.include_sample_splice_junctions_bed(config_sample=config_sample)
        self.include_sample_rna_coverage_bigwig(config_sample=config_sample)

    def build_config_sample(self, case_sample: CaseSample) -> ScoutRnaIndividual:
        """Build a sample with Tomte specific information."""
        config_sample = ScoutRnaIndividual()
        self.add_common_sample_info(config_sample=config_sample, case_sample=case_sample)
        self.include_sample_files(config_sample)
        config_sample.analysis_type = PrepCategory.WHOLE_TRANSCRIPTOME_SEQUENCING.value
        config_sample.father = (
            case_sample.father.internal_id
            if case_sample.father
            else RelationshipStatus.HAS_NO_PARENT
        )
        config_sample.mother = (
            case_sample.mother.internal_id
            if case_sample.mother
            else RelationshipStatus.HAS_NO_PARENT
        )
        return config_sample
