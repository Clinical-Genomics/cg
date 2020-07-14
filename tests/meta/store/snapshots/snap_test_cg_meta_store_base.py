# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import GenericRepr, Snapshot


snapshots = Snapshot()

snapshots["test_build_bundle 1"] = {
    "created": GenericRepr("datetime.datetime(2020, 3, 1, 0, 0)"),
    "files": {"path": "mock_path"},
    "name": "case_id",
    "pipeline_version": "v8.2.2",
}

snapshots["test_parse_files 1"] = [
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/salmon_quant/quant.sf",
        "tag_map_key": ("salmon_quant",),
        "tags": None,
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/star_fusion/star-fusion.fusion_predictions.abridged.tsv",
        "tag_map_key": ("star_fusion",),
        "tags": None,
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/arriba_ar/sample_id_lanes_1234_trim_arriba.pdf",
        "tag_map_key": ("arriba_ar", "arriba_report"),
        "tags": None,
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/arriba_ar/sample_id_lanes_1234_trim_arriba.tsv",
        "tag_map_key": ("arriba_ar", "arriba_ar"),
        "tags": None,
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/stringtie_ar/sample_id_lanes_1234_trim_star_sorted_merged_strg.gtf",
        "tag_map_key": ("stringtie_ar",),
        "tags": None,
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/gffcompare_ar/sample_id_lanes_1234_trim_star_sorted_merged_strg_gffcmp.gtf",
        "tag_map_key": ("gffcompare_ar",),
        "tags": None,
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/markduplicates/sample_id_lanes_1234_trim_star_sorted_merged_md.cram",
        "tag_map_key": ("markduplicates",),
        "tags": None,
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/markduplicates/sample_id_lanes_1234_trim_star_sorted_merged_md.cram.crai",
        "tag_map_key": ("markduplicates",),
        "tags": None,
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/gatk_asereadcounter/sample_id_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase.csv",
        "tag_map_key": ("gatk_asereadcounter",),
        "tags": None,
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/bootstrapann/sample_id_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase_bootstr.vcf",
        "tag_map_key": ("bootstrapann",),
        "tags": None,
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/bcftools_merge/case_id_comb.vcf",
        "tag_map_key": ("bcftools_merge",),
        "tags": None,
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/varianteffectpredictor/case_id_comb_vep.vcf",
        "tag_map_key": ("varianteffectpredictor",),
        "tags": None,
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/version_collect_ar/case_id_vcol.yaml",
        "tag_map_key": ("version_collect_ar",),
        "tags": None,
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/multiqc_ar/multiqc_data/multiqc_data.json",
        "tag_map_key": ("multiqc_ar", "json"),
        "tags": None,
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/multiqc_ar/multiqc_report.html",
        "tag_map_key": ("multiqc_ar", "html"),
        "tags": None,
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id_qc_sample_info.yaml",
        "tag_map_key": ("mip_analyse", "sample_info"),
        "tags": None,
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/reference_info.yaml",
        "tag_map_key": ("mip_analyse", "references_info"),
        "tags": None,
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/mip_log/2020-02-28/mip_2020-02-28T10:22:26.log",
        "tag_map_key": ("mip_analyse", "log"),
        "tags": None,
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id_config.yaml",
        "tag_map_key": ("mip_analyse", "config_analysis"),
        "tags": None,
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/pedigree.yaml",
        "tag_map_key": ("mip_analyse", "pedigree"),
        "tags": None,
    },
    {
        "archive": False,
        "path": "/path/to/servers/config/cluster.ourplace.se/mip8.2-rna-stage.yaml",
        "tag_map_key": ("mip_analyse", "config"),
        "tags": None,
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/case_id.fam",
        "tag_map_key": ("mip_analyse", "pedigree_fam"),
        "tags": None,
    },
]
