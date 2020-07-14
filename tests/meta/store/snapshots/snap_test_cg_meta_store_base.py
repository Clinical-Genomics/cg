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
        "tags": ["meta", "mip-rna", "salmon-quant", "sample_id"],
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/star_fusion/star-fusion.fusion_predictions.abridged.tsv",
        "tag_map_key": ("star_fusion",),
        "tags": ["meta", "mip-rna", "sample_id", "star-fusion"],
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/arriba_ar/sample_id_lanes_1234_trim_arriba.pdf",
        "tag_map_key": ("arriba_ar", "arriba_report"),
        "tags": ["arriba-ar", "arriba-report", "meta", "mip-rna", "sample_id"],
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/arriba_ar/sample_id_lanes_1234_trim_arriba.tsv",
        "tag_map_key": ("arriba_ar", "arriba_ar"),
        "tags": ["arriba-ar", "meta", "mip-rna", "sample_id"],
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/stringtie_ar/sample_id_lanes_1234_trim_star_sorted_merged_strg.gtf",
        "tag_map_key": ("stringtie_ar",),
        "tags": ["meta", "mip-rna", "sample_id", "stringtie-ar"],
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/gffcompare_ar/sample_id_lanes_1234_trim_star_sorted_merged_strg_gffcmp.gtf",
        "tag_map_key": ("gffcompare_ar",),
        "tags": ["gffcompare-ar", "meta", "mip-rna", "sample_id"],
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/markduplicates/sample_id_lanes_1234_trim_star_sorted_merged_md.cram",
        "tag_map_key": ("markduplicates",),
        "tags": ["cram", "mip-rna", "sample_id"],
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/markduplicates/sample_id_lanes_1234_trim_star_sorted_merged_md.cram.crai",
        "tag_map_key": ("markduplicates",),
        "tags": ["cram", "cram-index", "mip-rna", "sample_id"],
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/gatk_asereadcounter/sample_id_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase.csv",
        "tag_map_key": ("gatk_asereadcounter",),
        "tags": ["gatk-asereadcounter", "meta", "mip-rna", "sample_id"],
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/bootstrapann/sample_id_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase_bootstr.vcf",
        "tag_map_key": ("bootstrapann",),
        "tags": ["bootstrapann", "mip-rna", "sample_id", "vcf"],
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/bcftools_merge/case_id_comb.vcf",
        "tag_map_key": ("bcftools_merge",),
        "tags": ["bcftools-merge", "case_id", "mip-rna", "vcf"],
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/varianteffectpredictor/case_id_comb_vep.vcf",
        "tag_map_key": ("varianteffectpredictor",),
        "tags": ["case_id", "mip-rna", "varianteffectpredictor", "vcf"],
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/version_collect_ar/case_id_vcol.yaml",
        "tag_map_key": ("version_collect_ar",),
        "tags": ["case_id", "meta", "mip-rna", "version-collect-ar"],
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/multiqc_ar/multiqc_data/multiqc_data.json",
        "tag_map_key": ("multiqc_ar", "json"),
        "tags": ["case_id", "meta", "mip-rna", "multiqc-json"],
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/multiqc_ar/multiqc_report.html",
        "tag_map_key": ("multiqc_ar", "html"),
        "tags": ["case_id", "meta", "mip-rna", "multiqc-html"],
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id_qc_sample_info.yaml",
        "tag_map_key": ("mip_analyse", "sample_info"),
        "tags": ["case_id", "meta", "mip-analyse", "mip-rna", "sample-info"],
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/reference_info.yaml",
        "tag_map_key": ("mip_analyse", "references_info"),
        "tags": ["case_id", "meta", "mip-analyse", "mip-rna", "reference-info"],
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/mip_log/2020-02-28/mip_2020-02-28T10:22:26.log",
        "tag_map_key": ("mip_analyse", "log"),
        "tags": ["case_id", "log", "meta", "mip-analyse", "mip-rna"],
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id_config.yaml",
        "tag_map_key": ("mip_analyse", "config_analysis"),
        "tags": ["case_id", "config-analysis", "meta", "mip-analyse", "mip-rna"],
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/pedigree.yaml",
        "tag_map_key": ("mip_analyse", "pedigree"),
        "tags": ["case_id", "meta", "mip-analyse", "mip-rna", "pedigree"],
    },
    {
        "archive": False,
        "path": "/path/to/servers/config/cluster.ourplace.se/mip8.2-rna-stage.yaml",
        "tag_map_key": ("mip_analyse", "config"),
        "tags": ["case_id", "config", "meta", "mip-analyse", "mip-rna"],
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/case_id.fam",
        "tag_map_key": ("mip_analyse", "pedigree_fam"),
        "tags": ["case_id", "meta", "mip-analyse", "mip-rna", "pedigree-fam"],
    },
]
