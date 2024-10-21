"""Functions that handle files in the context of Scout uploading."""

import logging
import re
from pathlib import Path
from typing import Any

from housekeeper.store.models import File, Version

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.constants.constants import Workflow
from cg.constants.subject import RelationshipStatus
from cg.meta.upload.scout.hk_tags import CaseTags, SampleTags
from cg.models.scout.scout_load_config import (
    ScoutIndividual,
    ScoutLoadConfig,
    ScoutMipIndividual,
    ScoutRarediseaseIndividual,
)
from cg.store.models import Analysis, Case, CaseSample, Sample

LOG = logging.getLogger(__name__)


class ScoutConfigBuilder:
    """Base class for handling files that should be included in Scout upload."""

    def __init__(self, hk_version_obj: Version, analysis_obj: Analysis, lims_api: LimsAPI):
        self.hk_version_obj: Version = hk_version_obj
        self.analysis_obj: Analysis = analysis_obj
        self.lims_api: LimsAPI = lims_api
        self.case_tags: CaseTags
        self.sample_tags: SampleTags

    def add_common_info_to_load_config(self, load_config: ScoutLoadConfig) -> None:
        """Add the mandatory common information to a Scout load config object."""
        load_config.analysis_date = self.analysis_obj.completed_at or self.analysis_obj.started_at
        load_config.default_gene_panels = self.analysis_obj.case.panels
        load_config.family = self.analysis_obj.case.internal_id
        load_config.family_name = self.analysis_obj.case.name
        load_config.owner = self.analysis_obj.case.customer.internal_id
        load_config.synopsis = self.analysis_obj.case.synopsis
        self.include_cohorts(load_config=load_config)
        self.include_phenotype_groups(load_config=load_config)
        self.include_phenotype_terms(load_config=load_config)

    def run_madeline(self, family_obj: Case) -> Path:
        """Generate a madeline file for an analysis. Use customer sample names."""
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

    @staticmethod
    def is_multi_sample_case(load_config: ScoutLoadConfig) -> bool:
        return len(load_config.samples) > 1

    @staticmethod
    def is_family_case(load_config: ScoutLoadConfig) -> bool:
        """Check if there are any linked individuals in a case."""
        for sample in load_config.samples:
            if sample.mother and sample.mother != "0":
                return True

            if sample.father and sample.father != "0":
                return True
        return False

    def include_pedigree_picture(self, load_config: ScoutLoadConfig) -> None:
        if self.is_multi_sample_case(load_config=load_config):
            if self.is_family_case(load_config=load_config):
                svg_path: Path = self.run_madeline(self.analysis_obj.case)
                load_config.madeline = str(svg_path)
            else:
                LOG.info("family of unconnected samples - skip pedigree graph")
        else:
            LOG.info("family of 1 sample - skip pedigree graph")

    @staticmethod
    def remove_chromosome_substring(file_path: str | None) -> str | None:
        """Remove a file's suffix and identifying integer or X/Y
        Example:
        `/some/path/gatkcomb_rhocall_vt_af_chromograph_sites_X.png` becomes
        `/some/path/gatkcomb_rhocall_vt_af_chromograph_sites_`"""
        if file_path is None:
            return file_path
        return re.split(r"(?:[1-9]|1[0-9]|2[0-2]|[XY])\.png$", file_path)[0]

    def get_sample_information(self, load_config: ScoutLoadConfig) -> None:
        LOG.info("Building samples")
        db_sample: CaseSample
        for db_sample in self.analysis_obj.case.links:
            load_config.samples.append(self.build_config_sample(case_sample=db_sample))

    def build_config_sample(self, case_sample: CaseSample) -> ScoutIndividual:
        """Build a sample with rnafusion specific information."""
        if self.analysis_obj.workflow == Workflow.RAREDISEASE:
            config_sample = ScoutRarediseaseIndividual()
        elif self.analysis_obj.workflow == Workflow.MIP_DNA:
            config_sample = ScoutMipIndividual()
        elif self.analysis_obj.workflow == Workflow.RNAFUSION:
            config_sample = ScoutIndividual()
        self.add_common_sample_info(config_sample=config_sample, case_sample=case_sample)
        self.add_common_sample_files(config_sample=config_sample, case_sample=case_sample)
        return config_sample

    def add_common_sample_info(
        self, config_sample: ScoutIndividual, case_sample: CaseSample
    ) -> None:
        """Add the information to a sample that is common for different analysis types."""
        sample_id: str = case_sample.sample.internal_id
        LOG.info(f"Building sample {sample_id}")
        lims_sample: dict[str, Any] = self.lims_api.sample(sample_id)
        config_sample.sample_id = sample_id
        config_sample.sex = case_sample.sample.sex
        config_sample.phenotype = case_sample.status
        config_sample.analysis_type = (
            case_sample.sample.application_version.application.analysis_type
        )
        config_sample.sample_name = case_sample.sample.name
        config_sample.tissue_type = lims_sample.get("source", "unknown")
        config_sample.subject_id = case_sample.sample.subject_id
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

    def add_common_sample_files(
        self,
        config_sample: ScoutIndividual,
        case_sample: CaseSample,
    ) -> None:
        """Add common sample files for different analysis types."""
        LOG.info(f"Adding common files for sample {case_sample.sample.internal_id}")
        self.include_sample_alignment_file(config_sample)
        self.include_sample_files(config_sample)

    def build_load_config(self) -> ScoutLoadConfig:
        """Build a load config for uploading a case to Scout."""
        raise NotImplementedError

    def include_sample_files(self, config_sample: ScoutIndividual) -> None:
        """Include all files that are used on sample level in Scout."""
        raise NotImplementedError

    def include_case_files(self) -> None:
        """Include all files that are used on case level in Scout."""
        raise NotImplementedError

    def include_phenotype_terms(self, load_config: ScoutLoadConfig) -> None:
        LOG.info("Adding phenotype terms to Scout load config")
        phenotype_terms: set[str] = set()
        link_obj: CaseSample
        for link_obj in self.analysis_obj.case.links:
            sample_obj: Sample = link_obj.sample
            for phenotype_term in sample_obj.phenotype_terms:
                LOG.debug(
                    f"Adding term {phenotype_term} from sample {sample_obj.internal_id} to "
                    f"phenotype terms",
                )
                phenotype_terms.add(phenotype_term)
        if phenotype_terms:
            load_config.phenotype_terms = list(phenotype_terms)

    def include_phenotype_groups(self, load_config: ScoutLoadConfig) -> None:
        LOG.info("Adding phenotype groups to Scout load config")
        phenotype_groups: set[str] = set()
        link_obj: CaseSample
        for link_obj in self.analysis_obj.case.links:
            sample_obj: Sample = link_obj.sample
            for phenotype_group in sample_obj.phenotype_groups:
                LOG.debug(
                    f"Adding group {phenotype_group} from sample { sample_obj.internal_id} to "
                    f"phenotype groups",
                )
                phenotype_groups.add(phenotype_group)
        if phenotype_groups:
            load_config.phenotype_groups = list(phenotype_groups)

    def include_cohorts(self, load_config: ScoutLoadConfig) -> None:
        LOG.info("Including cohorts to Scout load config")
        cohorts: list[str] = self.analysis_obj.case.cohorts
        if cohorts:
            LOG.debug(f"Adding cohorts {', '.join(cohorts)}")
            load_config.cohorts = cohorts

    def include_cnv_report(self, load_config: ScoutLoadConfig) -> None:
        LOG.info("Include CNV report to case")
        load_config.cnv_report = self.get_file_from_hk(
            hk_tags=self.case_tags.cnv_report, latest=True
        )

    def include_multiqc_report(self, load_config: ScoutLoadConfig) -> None:
        LOG.info("Include MultiQC report to case")
        load_config.multiqc = self.get_file_from_hk(
            hk_tags=self.case_tags.multiqc_report, latest=True
        )

    def include_sample_alignment_file(self, config_sample: ScoutIndividual) -> None:
        """Include the alignment file for a sample
        Try if cram file is found, if not: load bam file
        """
        sample_id: str = config_sample.sample_id
        config_sample.alignment_path = self.get_sample_file(
            hk_tags=self.sample_tags.alignment_file, sample_id=sample_id
        )

        if not config_sample.alignment_path:
            self.include_sample_alignment_bam(config_sample)

    def include_sample_alignment_bam(self, config_sample: ScoutIndividual) -> None:
        sample_id: str = config_sample.sample_id
        config_sample.alignment_path = self.get_sample_file(
            hk_tags=self.sample_tags.bam_file, sample_id=sample_id
        )

    def get_sample_file(self, hk_tags: set[str], sample_id: str) -> str | None:
        """Return a file that is specific for an individual from Housekeeper."""
        if hk_tags:  # skip if no tag found
            tags: set = hk_tags.copy()
            tags.add(sample_id)
            return self.get_file_from_hk(hk_tags=tags)

    def get_file_from_hk(self, hk_tags: set[str], latest: bool | None = False) -> str | None:
        """Return the Housekeeper file path as a string."""

        LOG.info(f"Get file with tags {hk_tags}")
        if not hk_tags:
            LOG.debug("No tags provided, skipping")
            return None
        hk_file: File | None = (
            HousekeeperAPI.get_latest_file_from_version(version=self.hk_version_obj, tags=hk_tags)
            if latest
            else HousekeeperAPI.get_file_from_version(version=self.hk_version_obj, tags=hk_tags)
        )
        return hk_file.full_path if hk_file else None
