# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import GenericRepr, Snapshot


snapshots = Snapshot()

snapshots["test_build_bundle 1"] = {
    "created": GenericRepr("datetime.datetime(2020, 3, 1, 0, 0)"),
    "files": [
        {
            "archive": False,
            "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/salmon_quant/quant.sf",
            "tags": ["meta", "mip-rna", "salmon_quant", "sample_id"],
        },
        {
            "archive": False,
            "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/star_fusion/star-fusion.fusion_predictions.abridged.tsv",
            "tags": ["meta", "mip-rna", "sample_id", "star_fusion"],
        },
        {
            "archive": False,
            "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/arriba_ar/sample_id_lanes_1234_trim_arriba.pdf",
            "tags": ["arriba_ar", "arriba_report", "meta", "mip-rna", "sample_id"],
        },
        {
            "archive": False,
            "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/arriba_ar/sample_id_lanes_1234_trim_arriba.tsv",
            "tags": ["arriba_ar", "meta", "mip-rna", "sample_id"],
        },
        {
            "archive": False,
            "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/stringtie_ar/sample_id_lanes_1234_trim_star_sorted_merged_strg.gtf",
            "tags": ["meta", "mip-rna", "sample_id", "stringtie_ar"],
        },
        {
            "archive": False,
            "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/gffcompare_ar/sample_id_lanes_1234_trim_star_sorted_merged_strg_gffcmp.gtf",
            "tags": ["gffcompare_ar", "meta", "mip-rna", "sample_id"],
        },
        {
            "archive": False,
            "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/markduplicates/sample_id_lanes_1234_trim_star_sorted_merged_md.cram",
            "tags": ["cram", "markduplicates", "mip-rna", "sample_id"],
        },
        {
            "archive": False,
            "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/gatk_asereadcounter/sample_id_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase.csv",
            "tags": ["gatk_asereadcounter", "meta", "mip-rna", "sample_id"],
        },
        {
            "archive": False,
            "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/bootstrapann/sample_id_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase_bootstr.vcf",
            "tags": ["bootstrapann", "mip-rna", "sample_id", "vcf"],
        },
        {
            "archive": False,
            "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/bcftools_merge/case_id_comb.vcf",
            "tags": ["bcftools_merge", "case_id", "mip-rna", "vcf"],
        },
        {
            "archive": False,
            "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/varianteffectpredictor/case_id_comb_vep.vcf",
            "tags": ["case_id", "mip-rna", "varianteffectpredictor", "vcf"],
        },
        {
            "archive": False,
            "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/version_collect_ar/case_id_vcol.yaml",
            "tags": ["case_id", "meta", "mip-rna", "version_collect_ar"],
        },
        {
            "archive": False,
            "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/multiqc_ar/multiqc_data/multiqc_data.json",
            "tags": ["case_id", "json", "meta", "mip-rna", "multiqc_ar"],
        },
        {
            "archive": False,
            "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/multiqc_ar/multiqc_report.html",
            "tags": ["case_id", "html", "meta", "mip-rna", "multiqc_ar"],
        },
        {
            "archive": False,
            "path": "/path/to/rare-disease/cases/case_id/analysis/case_id_qc_sample_info.yaml",
            "tags": ["case_id", "meta", "mip-rna", "mip_analyse", "sample_info"],
        },
        {
            "archive": False,
            "path": "/path/to/rare-disease/cases/case_id/analysis/reference_info.yaml",
            "tags": ["case_id", "meta", "mip-rna", "mip_analyse", "references_info"],
        },
        {
            "archive": False,
            "path": "/path/to/rare-disease/cases/case_id/analysis/mip_log/2020-02-28/mip_2020-02-28T10:22:26.log",
            "tags": ["case_id", "log", "meta", "mip-rna", "mip_analyse"],
        },
        {
            "archive": False,
            "path": "/path/to/rare-disease/cases/case_id/analysis/case_id_config.yaml",
            "tags": ["case_id", "config_analysis", "meta", "mip-rna", "mip_analyse"],
        },
        {
            "archive": False,
            "path": "/path/to/rare-disease/cases/case_id/pedigree.yaml",
            "tags": ["case_id", "meta", "mip-rna", "mip_analyse", "pedigree"],
        },
        {
            "archive": False,
            "path": "/path/to/servers/config/cluster.ourplace.se/mip8.2-rna-stage.yaml",
            "tags": ["case_id", "config", "meta", "mip-rna", "mip_analyse"],
        },
        {
            "archive": False,
            "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/case_id.fam",
            "tags": ["case_id", "meta", "mip-rna", "mip_analyse", "pedigree_fam"],
        },
    ],
    "name": "case_id",
    "pipeline_version": "v8.2.2",
}

snapshots["test_get_files 1"] = [
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/salmon_quant/quant.sf",
        "tags": ["meta", "salmon_quant", "sample_id", "wts"],
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/star_fusion/star-fusion.fusion_predictions.abridged.tsv",
        "tags": ["meta", "sample_id", "star_fusion", "wts"],
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/arriba_ar/sample_id_lanes_1234_trim_arriba.pdf",
        "tags": ["arriba_ar", "arriba_report", "meta", "sample_id", "wts"],
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/arriba_ar/sample_id_lanes_1234_trim_arriba.tsv",
        "tags": ["arriba_ar", "meta", "sample_id", "wts"],
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/stringtie_ar/sample_id_lanes_1234_trim_star_sorted_merged_strg.gtf",
        "tags": ["meta", "sample_id", "stringtie_ar", "wts"],
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/gffcompare_ar/sample_id_lanes_1234_trim_star_sorted_merged_strg_gffcmp.gtf",
        "tags": ["gffcompare_ar", "meta", "sample_id", "wts"],
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/markduplicates/sample_id_lanes_1234_trim_star_sorted_merged_md.cram",
        "tags": ["cram", "markduplicates", "sample_id", "wts"],
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/gatk_asereadcounter/sample_id_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase.csv",
        "tags": ["gatk_asereadcounter", "meta", "sample_id", "wts"],
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/bootstrapann/sample_id_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase_bootstr.vcf",
        "tags": ["bootstrapann", "sample_id", "vcf", "wts"],
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/bcftools_merge/case_id_comb.vcf",
        "tags": ["bcftools_merge", "case_id", "vcf", "wts"],
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/varianteffectpredictor/case_id_comb_vep.vcf",
        "tags": ["case_id", "varianteffectpredictor", "vcf", "wts"],
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/version_collect_ar/case_id_vcol.yaml",
        "tags": ["case_id", "meta", "version_collect_ar", "wts"],
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/multiqc_ar/multiqc_data/multiqc_data.json",
        "tags": ["case_id", "json", "meta", "multiqc_ar", "wts"],
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/multiqc_ar/multiqc_report.html",
        "tags": ["case_id", "html", "meta", "multiqc_ar", "wts"],
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id_qc_sample_info.yaml",
        "tags": ["case_id", "meta", "mip_analyse", "sample_info", "wts"],
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/reference_info.yaml",
        "tags": ["case_id", "meta", "mip_analyse", "references_info", "wts"],
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/mip_log/2020-02-28/mip_2020-02-28T10:22:26.log",
        "tags": ["case_id", "log", "meta", "mip_analyse", "wts"],
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id_config.yaml",
        "tags": ["case_id", "config_analysis", "meta", "mip_analyse", "wts"],
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/pedigree.yaml",
        "tags": ["case_id", "meta", "mip_analyse", "pedigree", "wts"],
    },
    {
        "archive": False,
        "path": "/path/to/servers/config/cluster.ourplace.se/mip8.2-rna-stage.yaml",
        "tags": ["case_id", "config", "meta", "mip_analyse", "wts"],
    },
    {
        "archive": False,
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/case_id.fam",
        "tags": ["case_id", "meta", "mip_analyse", "pedigree_fam", "wts"],
    },
]

snapshots["test_parse_config 1"] = {
    "case": "case_id",
    "email": None,
    "is_dryrun": False,
    "out_dir": "tests/fixtures/apps/mip/rna/store/",
    "priority": "low",
    "sampleinfo_path": "tests/fixtures/apps/mip/rna/store/case_qc_sample_info.yaml",
    "samples": [{"id": "sample_id", "type": "wts"}],
}

snapshots["test_parse_sampleinfo_data 1"] = {
    "case": "case_id",
    "date": GenericRepr("datetime.datetime(2019, 11, 21, 14, 31, 2)"),
    "is_finished": True,
    "version": "v7.1.4",
}
