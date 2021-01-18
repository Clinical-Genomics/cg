"""Functions that handle files in the context of scout uploading"""
import logging
import re
from typing import List, Optional, Set, Tuple

from housekeeper.store import models as hk_models

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.scout.scout_load_config import ScoutIndividual, ScoutLoadConfig

LOG = logging.getLogger(__name__)

# Maps keys that are used in scout load config on tags that are used in scout
CASE_TAG_MAP = dict(
    rare_vcf_to_tag={
        ("vcf_snv", {"vcf-snv-clinical"}),
        ("vcf_snv_research", {"vcf-snv-research"}),
        ("vcf_sv", {"vcf-sv-clinical"}),
        ("vcf_sv_research", {"vcf-sv-research"}),
    },
    cancer_vcf_to_tag={
        ("vcf_cancer", {"vcf-snv-clinical"}),
        ("vcf_cancer_sv", {"vcf-sv-clinical"}),
        # ("vcf_cancer_research", "vcf-snv-research"),
        # ("vcf_cancer_sv_research", "vcf-sv-research"),
    },
    peddy_file_to_tag={
        ("peddy_ped", {"ped"}),
        ("peddy_sex", {"sex-check"}),
        ("peddy_check", {"ped-check"}),
    },
    optional_mip_to_tag={
        ("delivery_report", {"delivery-report"}),
        ("multiqc", {"multiqc-html"}),
        ("vcf_str", {"vcf-str"}),
        ("smn_tsv", {"smn-calling"}),
    },
    optional_balsamic_to_tag={
        ("multiqc", {"multiqc-html"}),
    },
    bam_tag_map={("bam_path", {"bam"})},
    alignment_file_tag_map={("alignment_path", {"cram"})},
)


def include_mip_case_files(sample: ScoutLoadConfig, hk_version_obj: hk_models.Version) -> None:
    """Add the files that are specific for a mip rare disease analysis"""
    pass


def include_sample_alignment_file(
    sample: ScoutIndividual, hk_version_obj: hk_models.Version
) -> None:
    """Include the files that are common for all samples to the sample data"""
    sample_id: str = sample.sample_id
    cram_tags = {"cram", sample_id}
    cram_file = fetch_file_from_hk(hk_version_obj=hk_version_obj, hk_tags=cram_tags)
    if cram_file:
        LOG.debug("Including cram file for sample %s", sample_id)
        sample.alignment_path = cram_file
        return
    bam_tags = {"bam", sample_id}
    bam_file = fetch_file_from_hk(hk_version_obj=hk_version_obj, hk_tags=bam_tags)
    if bam_file:
        LOG.debug("Including bam file for sample %s", sample_id)
        sample.alignment_path = bam_file
        return
    LOG.info("Could not find alignment files form sample %s", sample_id)


def include_mip_optional_sample_files(
    sample: ScoutIndividual, hk_version_obj: hk_models.Version
) -> None:
    """Include sample level files that are optional for mip samples"""
    sample_id: str = sample.sample_id
    cytosure_tags = {"vcf2cytosure", sample_id}
    LOG.debug("Including vcf2cytosure with tags %s for sample %s", sample_id)
    sample.vcf2cytosure = fetch_file_from_hk(hk_version_obj=hk_version_obj, hk_tags=cytosure_tags)

    mt_bam_tags = {"bam-mt", sample_id}
    LOG.debug("Including mithocondrial bam with tags %s for sample %s", mt_bam_tags, sample_id)
    sample.mt_bam = fetch_file_from_hk(hk_version_obj=hk_version_obj, hk_tags=mt_bam_tags)

    autozyg_regions_tags = {"chromograph", "autozyg", sample_id}
    LOG.debug(
        "Including autozygotic regions file with tags %s for sample %s",
        autozyg_regions_tags,
        sample_id,
    )
    sample.chromograph_images.autozyg = fetch_file_from_hk(
        hk_version_obj=hk_version_obj, hk_tags=autozyg_regions_tags
    )

    chromograph_coverage_tags = {"chromograph", "tcov", sample_id}
    LOG.debug(
        "Including chromograph coverage file with tags %s for sample %s",
        chromograph_coverage_tags,
        sample_id,
    )
    sample.chromograph_images.coverage = extract_generic_filepath(
        fetch_file_from_hk(hk_version_obj=hk_version_obj, hk_tags=chromograph_coverage_tags)
    )

    upd_region_tags = {"chromograph", "regions", sample_id}
    LOG.debug("Including upd regions files with tags %s for sample %s", upd_region_tags, sample_id)
    sample.chromograph_images.upd_regions = extract_generic_filepath(
        fetch_file_from_hk(hk_version_obj=hk_version_obj, hk_tags=upd_region_tags)
    )

    upd_site_tags = {"chromograph", "sites", sample_id}
    LOG.debug("Including upd site files with tags %s for sample %s", upd_site_tags, sample_id)
    sample.chromograph_images.upd_sites = extract_generic_filepath(
        fetch_file_from_hk(hk_version_obj=hk_version_obj, hk_tags=upd_site_tags)
    )


def fetch_file_from_hk(hk_version_obj: hk_models.Version, hk_tags: Set[str]) -> Optional[str]:
    """Fetch a file from housekeeper and return the path as a string.
    If file does not exist return None
    """
    hk_file: Optional[hk_models.File] = HousekeeperAPI.fetch_file_from_version(
        version_obj=hk_version_obj, tags=hk_tags
    )
    if hk_file is None:
        return hk_file
    return hk_file.full_path


def extract_generic_filepath(file_path: Optional[str]) -> Optional[str]:
    """Remove a file's suffix and identifying integer or X/Y
    Example:
    `/some/path/gatkcomb_rhocall_vt_af_chromograph_sites_X.png` becomes
    `/some/path/gatkcomb_rhocall_vt_af_chromograph_sites_`"""
    if file_path is None:
        return file_path
    return re.split("(\d+|X|Y)\.png", file_path)[0]


def include_files(
    data: dict,
    hk_version_obj: hk_models.Version,
    hk_tag_map: Set[Tuple[str, Set[str]]],
    extra_tag: str = "",
    skip_missing: bool = True,
) -> None:
    """Fetch files from a housekeeper version object and add them to a dictionary"""
    for key, hk_tags in hk_tag_map:
        if extra_tag:
            hk_tags.add(extra_tag)

        hk_file: Optional[hk_models.File] = HousekeeperAPI.fetch_file_from_version(
            version_obj=hk_version_obj, tags=hk_tags
        )
        if hk_file is None:
            if skip_missing:
                LOG.debug("skipping missing file: %s", key)
                continue
            raise FileNotFoundError(f"missing file: {key}")
        data[key] = str(hk_file.full_path)
