import logging

from housekeeper.store.models import Version

from cg.apps.lims import LimsAPI
from cg.constants.constants import SampleType
from cg.constants.scout_upload import BALSAMIC_CASE_TAGS, BALSAMIC_SAMPLE_TAGS
from cg.constants.subject import PhenotypeStatus
from cg.meta.upload.scout.hk_tags import CaseTags, SampleTags
from cg.meta.upload.scout.scout_config_builder import ScoutConfigBuilder
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.models.scout.scout_load_config import BalsamicLoadConfig, ScoutCancerIndividual
from cg.store.models import Analysis, FamilySample, Sample

LOG = logging.getLogger(__name__)


class BalsamicConfigBuilder(ScoutConfigBuilder):
    def __init__(self, hk_version_obj: Version, analysis_obj: Analysis, lims_api: LimsAPI):
        super().__init__(
            hk_version_obj=hk_version_obj, analysis_obj=analysis_obj, lims_api=lims_api
        )
        self.case_tags: CaseTags = CaseTags(**BALSAMIC_CASE_TAGS)
        self.sample_tags: SampleTags = SampleTags(**BALSAMIC_SAMPLE_TAGS)
        self.load_config: BalsamicLoadConfig = BalsamicLoadConfig(track="cancer")

    def include_case_files(self):
        LOG.info("Including BALSAMIC specific case level files")
        self.load_config.vcf_cancer = self.get_file_from_hk(
            hk_tags=self.case_tags.snv_vcf, latest=True
        )
        self.load_config.vcf_cancer_sv = self.get_file_from_hk(
            hk_tags=self.case_tags.sv_vcf, latest=True
        )
        self.include_cnv_report()
        self.include_multiqc_report()
        self.include_delivery_report()

    def include_sample_files(self, config_sample: ScoutCancerIndividual) -> None:
        LOG.info("Including BALSAMIC specific sample level files.")

        sample_id: str = config_sample.sample_id
        if config_sample.alignment_path:
            if SampleType.TUMOR in config_sample.alignment_path:
                sample_id = SampleType.TUMOR.value
            elif SampleType.NORMAL in config_sample.alignment_path:
                sample_id = SampleType.NORMAL.value

        config_sample.vcf2cytosure = self.get_sample_file(
            hk_tags=self.sample_tags.vcf2cytosure, sample_id=sample_id
        )

    def build_config_sample(self, case_sample: FamilySample) -> ScoutCancerIndividual:
        """Build a sample with balsamic specific information."""
        config_sample = ScoutCancerIndividual()
        self.add_common_sample_info(config_sample=config_sample, case_sample=case_sample)
        self.add_common_sample_files(config_sample=config_sample, case_sample=case_sample)
        if BalsamicAnalysisAPI.get_sample_type(sample_obj=case_sample.sample) == SampleType.TUMOR:
            config_sample.phenotype = PhenotypeStatus.AFFECTED.value
            config_sample.sample_id = SampleType.TUMOR.value.upper()
        else:
            config_sample.phenotype = PhenotypeStatus.UNAFFECTED.value
            # If normal sample analysed as tumor, it will be treated as tumor in terms of ID for the Scout upload
            config_sample.sample_id = (
                SampleType.TUMOR.value.upper()
                if config_sample.alignment_path and SampleType.TUMOR in config_sample.alignment_path
                else SampleType.NORMAL.value.upper()
            )

        config_sample.analysis_type = self.get_balsamic_analysis_type(sample=case_sample.sample)

        return config_sample

    def get_balsamic_analysis_type(self, sample: Sample) -> str:
        """Returns a formatted balsamic analysis type"""

        analysis_type: str = BalsamicAnalysisAPI.get_application_type(sample_obj=sample)
        if analysis_type == "tgs":
            analysis_type = "panel"
        if analysis_type == "wgs":
            analysis_type = "wgs"

        return analysis_type

    def build_load_config(self) -> None:
        LOG.info("Build load config for balsamic case")
        self.add_common_info_to_load_config()
        self.load_config.human_genome_build = "37"
        self.load_config.rank_score_threshold = -100

        self.include_case_files()

        LOG.info("Building samples")
        db_sample: FamilySample

        for db_sample in self.analysis_obj.family.links:
            self.load_config.samples.append(self.build_config_sample(case_sample=db_sample))
