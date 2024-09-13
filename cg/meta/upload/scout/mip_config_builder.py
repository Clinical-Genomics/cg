import logging
import re
from pathlib import Path

from housekeeper.store.models import Version

from cg.apps.lims import LimsAPI
from cg.apps.madeline.api import MadelineAPI
from cg.constants.housekeeper_tags import HK_DELIVERY_REPORT_TAG
from cg.constants.scout import MIP_CASE_TAGS, MIP_SAMPLE_TAGS, UploadTrack
from cg.constants.subject import RelationshipStatus
from cg.meta.upload.scout.hk_tags import CaseTags, SampleTags
from cg.meta.upload.scout.scout_config_builder import ScoutConfigBuilder
from cg.meta.workflow.mip import MipAnalysisAPI
from cg.models.mip.mip_analysis import MipAnalysis
from cg.models.scout.scout_load_config import (
    MipLoadConfig,
    ScoutLoadConfig,
    ScoutMipIndividual,
)
from cg.store.models import Analysis, Case, CaseSample

LOG = logging.getLogger(__name__)


class MipConfigBuilder(ScoutConfigBuilder):
    def __init__(
        self,
        hk_version_obj: Version,
        analysis_obj: Analysis,
        mip_analysis_api: MipAnalysisAPI,
        lims_api: LimsAPI,
        madeline_api: MadelineAPI,
    ):
        super().__init__(
            hk_version_obj=hk_version_obj, analysis_obj=analysis_obj, lims_api=lims_api
        )
        self.case_tags: CaseTags = CaseTags(**MIP_CASE_TAGS)
        self.sample_tags: SampleTags = SampleTags(**MIP_SAMPLE_TAGS)
        self.load_config: MipLoadConfig = MipLoadConfig(
            track=UploadTrack.RARE_DISEASE.value,
            delivery_report=self.get_file_from_hk({HK_DELIVERY_REPORT_TAG}),
        )
        self.mip_analysis_api: MipAnalysisAPI = mip_analysis_api
        self.lims_api: LimsAPI = lims_api
        self.madeline_api: MadelineAPI = madeline_api

    def build_load_config(self, rank_score_threshold: int = 5) -> None:
        """Create a MIP specific load config for uploading analysis to Scout"""
        LOG.info("Generate load config for mip case")

        self.add_common_info_to_load_config()
        mip_analysis_data: MipAnalysis = self.mip_analysis_api.get_latest_metadata(
            self.analysis_obj.case.internal_id
        )
        self.load_config.human_genome_build = (
            "38" if "38" in mip_analysis_data.genome_build else "37"
        )
        self.load_config.rank_score_threshold = rank_score_threshold
        self.load_config.rank_model_version = mip_analysis_data.rank_model_version
        self.load_config.sv_rank_model_version = mip_analysis_data.sv_rank_model_version

        self.load_config.gene_panels = (
            self.mip_analysis_api.get_aggregated_panels(
                customer_id=self.analysis_obj.case.customer.internal_id,
                default_panels=set(self.analysis_obj.case.panels),
            )
            or None
        )

        self.include_case_files()

        LOG.info("Building samples")
        db_sample: CaseSample
        for db_sample in self.analysis_obj.case.links:
            self.load_config.samples.append(self.build_config_sample(case_sample=db_sample))
        self.include_pedigree_picture()

    def include_pedigree_picture(self) -> None:
        if self.is_multi_sample_case(self.load_config):
            if self.is_family_case(self.load_config):
                svg_path: Path = self.run_madeline(self.analysis_obj.case)
                self.load_config.madeline = str(svg_path)
            else:
                LOG.info("family of unconnected samples - skip pedigree graph")
        else:
            LOG.info("family of 1 sample - skip pedigree graph")

    def build_config_sample(self, case_sample: CaseSample) -> ScoutMipIndividual:
        """Build a sample with mip specific information"""

        config_sample = ScoutMipIndividual()
        self.add_common_sample_info(config_sample=config_sample, case_sample=case_sample)
        self.add_common_sample_files(config_sample=config_sample, case_sample=case_sample)
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

    def include_case_files(self):
        """Include case level files for mip case"""
        LOG.info("Including MIP specific case level files")
        self.load_config.peddy_check = self.get_file_from_hk(self.case_tags.peddy_check)
        self.load_config.peddy_ped = self.get_file_from_hk(self.case_tags.peddy_ped)
        self.load_config.peddy_sex = self.get_file_from_hk(self.case_tags.peddy_sex)
        self.load_config.smn_tsv = self.get_file_from_hk(self.case_tags.smn_tsv)
        self.load_config.vcf_mei = self.get_file_from_hk(self.case_tags.vcf_mei)
        self.load_config.vcf_mei_research = self.get_file_from_hk(self.case_tags.vcf_mei_research)
        self.load_config.vcf_snv = self.get_file_from_hk(self.case_tags.snv_vcf)
        self.load_config.vcf_snv_research = self.get_file_from_hk(self.case_tags.snv_research_vcf)
        self.load_config.vcf_str = self.get_file_from_hk(self.case_tags.vcf_str)
        self.load_config.vcf_sv = self.get_file_from_hk(self.case_tags.sv_vcf)
        self.load_config.vcf_sv_research = self.get_file_from_hk(self.case_tags.sv_research_vcf)
        self.include_multiqc_report()

    def include_sample_files(self, config_sample: ScoutMipIndividual) -> None:
        """Include sample level files that are optional for mip samples"""
        LOG.info("Including MIP specific sample level files")
        sample_id: str = config_sample.sample_id
        config_sample.vcf2cytosure = self.get_sample_file(
            hk_tags=self.sample_tags.vcf2cytosure, sample_id=sample_id
        )
        config_sample.mt_bam = self.get_sample_file(
            hk_tags=self.sample_tags.mt_bam, sample_id=sample_id
        )
        config_sample.chromograph_images.autozygous = self.extract_generic_filepath(
            file_path=self.get_sample_file(
                hk_tags=self.sample_tags.chromograph_autozyg, sample_id=sample_id
            )
        )
        config_sample.chromograph_images.coverage = self.extract_generic_filepath(
            file_path=self.get_sample_file(
                hk_tags=self.sample_tags.chromograph_coverage, sample_id=sample_id
            )
        )
        config_sample.chromograph_images.upd_regions = self.extract_generic_filepath(
            file_path=self.get_sample_file(
                hk_tags=self.sample_tags.chromograph_regions, sample_id=sample_id
            )
        )
        config_sample.chromograph_images.upd_sites = self.extract_generic_filepath(
            file_path=self.get_sample_file(
                hk_tags=self.sample_tags.chromograph_sites, sample_id=sample_id
            )
        )
        config_sample.reviewer.alignment = self.get_sample_file(
            hk_tags=self.sample_tags.reviewer_alignment, sample_id=sample_id
        )
        config_sample.reviewer.alignment_index = self.get_sample_file(
            hk_tags=self.sample_tags.reviewer_alignment_index, sample_id=sample_id
        )
        config_sample.reviewer.vcf = self.get_sample_file(
            hk_tags=self.sample_tags.reviewer_vcf, sample_id=sample_id
        )
        config_sample.reviewer.catalog = self.get_file_from_hk(hk_tags=self.case_tags.str_catalog)
        config_sample.mitodel_file = self.get_sample_file(
            hk_tags=self.sample_tags.mitodel_file, sample_id=sample_id
        )

    @staticmethod
    def extract_generic_filepath(file_path: str | None) -> str | None:
        """Remove a file's suffix and identifying integer or X/Y
        Example:
        `/some/path/gatkcomb_rhocall_vt_af_chromograph_sites_X.png` becomes
        `/some/path/gatkcomb_rhocall_vt_af_chromograph_sites_`"""
        if file_path is None:
            return file_path
        return re.split("(\d+|X|Y)\.png", file_path)[0]

    @staticmethod
    def is_family_case(load_config: ScoutLoadConfig) -> bool:
        """Check if there are any linked individuals in a case"""
        for sample in load_config.samples:
            if sample.mother and sample.mother != "0":
                return True
            if sample.father and sample.father != "0":
                return True
        return False

    @staticmethod
    def is_multi_sample_case(load_config: ScoutLoadConfig) -> bool:
        return len(load_config.samples) > 1

    def run_madeline(self, family_obj: Case) -> Path:
        """Generate a madeline file for an analysis. Use customer sample names"""
        samples = [
            {
                "sample": link_obj.sample.name,
                "sex": link_obj.sample.sex,
                "father": link_obj.father.name if link_obj.father else None,
                "mother": link_obj.mother.name if link_obj.mother else None,
                "status": link_obj.status,
            }
            for link_obj in family_obj.links
        ]
        svg_path: Path = self.madeline_api.run(family_id=family_obj.name, samples=samples)
        return svg_path
