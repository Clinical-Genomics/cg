"""Functions that handle files in the context of scout uploading"""
import logging
from typing import List, Optional, Set

import requests
from housekeeper.store.models import File, Version

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.meta.upload.scout.hk_tags import CaseTags, SampleTags
from cg.models.scout.scout_load_config import ScoutIndividual, ScoutLoadConfig
from cg.store.models import Analysis, FamilySample, Sample

LOG = logging.getLogger(__name__)

# Maps keys that are used in scout load config on tags that are used in scout


class ScoutConfigBuilder:
    """Base class for handling files that should be included in Scout upload"""

    def __init__(self, hk_version_obj: Version, analysis_obj: Analysis, lims_api: LimsAPI):
        self.hk_version_obj: Version = hk_version_obj
        self.analysis_obj: Analysis = analysis_obj
        self.lims_api: LimsAPI = lims_api
        self.case_tags: CaseTags
        self.sample_tags: SampleTags
        self.load_config: ScoutLoadConfig = ScoutLoadConfig()

    def add_common_info_to_load_config(self) -> None:
        """Add the mandatory common information to a scout load config object"""
        self.load_config.analysis_date = self.analysis_obj.completed_at
        self.load_config.default_gene_panels = self.analysis_obj.family.panels
        self.load_config.family = self.analysis_obj.family.internal_id
        self.load_config.family_name = self.analysis_obj.family.name
        self.load_config.owner = self.analysis_obj.family.customer.internal_id
        self.load_config.synopsis = self.analysis_obj.family.synopsis
        self.include_cohorts()
        self.include_phenotype_groups()
        self.include_phenotype_terms()

    def add_common_sample_info(
        self, config_sample: ScoutIndividual, case_sample: FamilySample
    ) -> None:
        """Add the information to a sample that is common for different analysis types"""
        sample_id: str = case_sample.sample.internal_id
        LOG.info("Building sample %s", sample_id)
        lims_sample = dict()
        try:
            lims_sample = self.lims_api.sample(sample_id) or {}
        except requests.exceptions.HTTPError as ex:
            LOG.info("Could not fetch sample %s from LIMS: %s", sample_id, ex)

        config_sample.sample_id = sample_id
        config_sample.sex = case_sample.sample.sex
        config_sample.phenotype = case_sample.status
        config_sample.analysis_type = (
            case_sample.sample.application_version.application.analysis_type
        )
        config_sample.sample_name = case_sample.sample.name
        config_sample.tissue_type = lims_sample.get("source", "unknown")
        config_sample.subject_id = case_sample.sample.subject_id

    def add_common_sample_files(
        self,
        config_sample: ScoutIndividual,
        case_sample: FamilySample,
    ) -> None:
        """Add common sample files for different analysis types."""
        sample_id: str = case_sample.sample.internal_id
        LOG.info(f"Adding common files for sample {sample_id}")
        self.include_sample_alignment_file(config_sample=config_sample)
        self.include_sample_files(config_sample=config_sample)

    def build_config_sample(self, case_sample: FamilySample) -> ScoutIndividual:
        """Build a sample for the scout load config"""
        raise NotImplementedError

    def build_load_config(self) -> ScoutLoadConfig:
        """Build a load config for uploading a case to scout"""
        raise NotImplementedError

    def include_sample_files(self, config_sample: ScoutIndividual) -> None:
        """Include all files that are used on sample level in Scout"""
        raise NotImplementedError

    def include_case_files(self) -> None:
        """Include all files that are used on case level in scout"""
        raise NotImplementedError

    def include_phenotype_terms(self) -> None:
        LOG.info("Adding phenotype terms to scout load config")
        phenotype_terms: Set[str] = set()
        link_obj: FamilySample
        for link_obj in self.analysis_obj.family.links:
            sample_obj: Sample = link_obj.sample
            for phenotype_term in sample_obj.phenotype_terms:
                LOG.debug(
                    "Adding term %s from sample %s to phenotype terms",
                    phenotype_term,
                    sample_obj.internal_id,
                )
                phenotype_terms.add(phenotype_term)
        if phenotype_terms:
            self.load_config.phenotype_terms = list(phenotype_terms)

    def include_phenotype_groups(self) -> None:
        LOG.info("Adding phenotype groups to scout load config")
        phenotype_groups: Set[str] = set()
        link_obj: FamilySample
        for link_obj in self.analysis_obj.family.links:
            sample_obj: Sample = link_obj.sample
            for phenotype_group in sample_obj.phenotype_groups:
                LOG.debug(
                    "Adding group %s from sample %s to phenotype groups",
                    phenotype_group,
                    sample_obj.internal_id,
                )
                phenotype_groups.add(phenotype_group)
        if phenotype_groups:
            self.load_config.phenotype_groups = list(phenotype_groups)

    def include_cohorts(self) -> None:
        LOG.info("Including cohorts to scout load config")
        cohorts: List[str] = self.analysis_obj.family.cohorts
        if cohorts:
            LOG.debug("Adding cohorts %s", ", ".join(cohorts))
            self.load_config.cohorts = cohorts

    def include_cnv_report(self) -> None:
        LOG.info("Include CNV report to case")
        self.load_config.cnv_report = self.get_file_from_hk(
            hk_tags=self.case_tags.cnv_report, latest=True
        )

    def include_multiqc_report(self) -> None:
        LOG.info("Include MultiQC report to case")
        self.load_config.multiqc = self.get_file_from_hk(
            hk_tags=self.case_tags.multiqc_report, latest=True
        )

    def include_delivery_report(self) -> None:
        LOG.info("Include delivery report to case")
        self.load_config.delivery_report = self.get_file_from_hk(
            hk_tags=self.case_tags.delivery_report, latest=True
        )

    def include_sample_alignment_file(self, config_sample: ScoutIndividual) -> None:
        """Include the alignment file for a sample

        First add the bam.
        Cram is preferred so overwrite if found
        """
        sample_id: str = config_sample.sample_id
        config_sample.alignment_path = self.get_sample_file(
            hk_tags=self.sample_tags.bam_file, sample_id=sample_id
        )

        config_sample.alignment_path = self.get_sample_file(
            hk_tags=self.sample_tags.alignment_file, sample_id=sample_id
        )

    def get_sample_file(self, hk_tags: Set[str], sample_id: str) -> Optional[str]:
        """Return a file that is specific for a individual from housekeeper"""
        tags: set = hk_tags.copy()
        tags.add(sample_id)
        return self.get_file_from_hk(hk_tags=tags)

    def get_file_from_hk(self, hk_tags: Set[str], latest: Optional[bool] = False) -> Optional[str]:
        """Get a file from housekeeper and return the path as a string."""
        LOG.info(f"Get file with tags {hk_tags}")
        if not hk_tags:
            LOG.debug("No tags provided, skipping")
            return None
        hk_file: Optional[File] = (
            HousekeeperAPI.get_latest_file_from_version(version=self.hk_version_obj, tags=hk_tags)
            if latest
            else HousekeeperAPI.get_file_from_version(version=self.hk_version_obj, tags=hk_tags)
        )
        return hk_file.full_path if hk_file else None
