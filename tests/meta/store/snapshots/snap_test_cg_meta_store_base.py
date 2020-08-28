# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import GenericRepr, Snapshot


snapshots = Snapshot()

snapshots["test_build_rna_bundle 1"] = {
    "created": GenericRepr("datetime.datetime(2020, 3, 1, 0, 0)"),
    "files": {"path": "mock_path"},
    "name": "case_id",
    "pipeline_version": "v8.2.2",
}

snapshots["test_build_dna_bundle 1"] = {
    "created": GenericRepr("datetime.datetime(2020, 3, 1, 0, 0)"),
    "files": {"path": "mock_path"},
    "name": "case_id",
    "pipeline_version": "v8.2.2",
}

snapshots["test_parse_files_rna 1"] = [
    {
        "archive": False,
        "deliverables_tag_map": ("salmon_quant",),
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/salmon_quant/quant.sf",
        "tags": ["mip-rna", "salmon-quant", "sample_id"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("star_fusion",),
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/star_fusion/star-fusion.fusion_predictions.abridged.tsv",
        "tags": ["mip-rna", "sample_id", "star-fusion"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("arriba_ar", "arriba_report"),
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/arriba_ar/sample_id_lanes_1234_trim_arriba.pdf",
        "tags": ["arriba-ar", "arriba-report", "mip-rna", "sample_id"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("arriba_ar", "arriba_ar"),
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/arriba_ar/sample_id_lanes_1234_trim_arriba.tsv",
        "tags": ["arriba-ar", "mip-rna", "sample_id"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("stringtie_ar",),
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/stringtie_ar/sample_id_lanes_1234_trim_star_sorted_merged_strg.gtf",
        "tags": ["mip-rna", "sample_id", "stringtie-ar"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("gffcompare_ar",),
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/gffcompare_ar/sample_id_lanes_1234_trim_star_sorted_merged_strg_gffcmp.gtf",
        "tags": ["gffcompare-ar", "mip-rna", "sample_id"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("markduplicates",),
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/markduplicates/sample_id_lanes_1234_trim_star_sorted_merged_md.cram",
        "tags": ["cram", "mip-rna", "sample_id"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("markduplicates",),
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/markduplicates/sample_id_lanes_1234_trim_star_sorted_merged_md.cram.crai",
        "tags": ["cram-index", "mip-rna", "sample_id"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("gatk_asereadcounter",),
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/gatk_asereadcounter/sample_id_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase.csv",
        "tags": ["gatk-asereadcounter", "mip-rna", "sample_id"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("bootstrapann",),
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/bootstrapann/sample_id_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase_bootstr.vcf",
        "tags": ["bootstrapann", "mip-rna", "sample_id"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("bcftools_merge",),
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/bcftools_merge/case_id_comb.vcf",
        "tags": ["bcftools-merge", "case_id", "mip-rna"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("varianteffectpredictor",),
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/varianteffectpredictor/case_id_comb_vep.vcf",
        "tags": ["case_id", "mip-rna", "varianteffectpredictor"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("version_collect_ar",),
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/version_collect_ar/case_id_vcol.yaml",
        "tags": ["case_id", "mip-rna", "version-collect-ar"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("multiqc_ar", "json"),
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/multiqc_ar/multiqc_data/multiqc_data.json",
        "tags": ["case_id", "mip-rna", "multiqc-json"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("multiqc_ar", "html"),
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/multiqc_ar/multiqc_report.html",
        "tags": ["case_id", "mip-rna", "multiqc-html"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("mip_analyse", "sample_info"),
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id_qc_sample_info.yaml",
        "tags": ["case_id", "mip-analyse", "mip-rna", "sample-info"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("mip_analyse", "references_info"),
        "path": "/path/to/rare-disease/cases/case_id/analysis/reference_info.yaml",
        "tags": ["case_id", "mip-analyse", "mip-rna", "reference-info"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("mip_analyse", "log"),
        "path": "/path/to/rare-disease/cases/case_id/analysis/mip_log/2020-02-28/mip_2020-02-28T10:22:26.log",
        "tags": ["case_id", "log", "mip-analyse", "mip-rna"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("mip_analyse", "config_analysis"),
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id_config.yaml",
        "tags": ["case_id", "config-analysis", "mip-analyse", "mip-rna"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("mip_analyse", "pedigree"),
        "path": "/path/to/rare-disease/cases/case_id/pedigree.yaml",
        "tags": ["case_id", "mip-analyse", "mip-rna", "pedigree"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("mip_analyse", "config"),
        "path": "/path/to/servers/config/cluster.ourplace.se/mip8.2-rna-stage.yaml",
        "tags": ["case_id", "config", "mip-analyse", "mip-rna"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("mip_analyse", "pedigree_fam"),
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/case_id.fam",
        "tags": ["case_id", "mip-analyse", "mip-rna", "pedigree-fam"],
    },
]

snapshots["test_parse_files_dna 1"] = [
    {
        "archive": False,
        "deliverables_tag_map": ("gatk_baserecalibration",),
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/gatk_baserecalibration/sample_id_lanes_5555_sorted_md_brecal.cram",
        "tags": ["cram", "mip-dna", "sample_id"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("gatk_baserecalibration",),
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/gatk_baserecalibration/sample_id_lanes_5555_sorted_md_brecal.cram.crai",
        "tags": ["cram-index", "mip-dna", "sample_id"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("chanjo_sexcheck",),
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/chanjo_sexcheck/sample_id_lanes_5555_sorted_md_brecal_sex.tsv",
        "tags": ["chanjo", "mip-dna", "sample_id", "sex-check"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("samtools_subsample_mt",),
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/samtools_subsample_mt/sample_id_lanes_5555_sorted_md_brecal_subsample_MT.bam",
        "tags": ["bam-mt", "mip-dna", "sample_id"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("samtools_subsample_mt",),
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/samtools_subsample_mt/sample_id_lanes_5555_sorted_md_brecal_subsample_MT.bam.bai",
        "tags": ["bam-mt-index", "mip-dna", "sample_id"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("smncopynumbercaller",),
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/smncopynumbercaller/sample_id_lanes_5555_sorted_md_brecal_smn.tsv",
        "tags": ["mip-dna", "sample_id", "smn-calling", "smncopynumbercaller"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("expansionhunter", "sv_str"),
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/expansionhunter/case_id_exphun.vcf.gz",
        "tags": ["case_id", "mip-dna", "vcf-str"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("expansionhunter", "sv_str"),
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/expansionhunter/case_id_exphun.vcf.gz.csi",
        "tags": ["case_id", "mip-dna", "vcf-str-index"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("sv_combinevariantcallsets",),
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/sv_combinevariantcallsets/case_id_comb.bcf",
        "tags": ["case_id", "mip-dna", "sv-bcf"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("sv_combinevariantcallsets",),
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/sv_combinevariantcallsets/case_id_comb.bcf.csi",
        "tags": ["case_id", "mip-dna", "sv-bcf-index"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("sv_reformat", "research"),
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/sv_reformat/case_id_comb_ann_vep_parsed_ranked.vcf.gz",
        "tags": ["case_id", "mip-dna", "vcf-sv-research"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("sv_reformat", "research"),
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/sv_reformat/case_id_comb_ann_vep_parsed_ranked.vcf.gz.csi",
        "tags": ["case_id", "mip-dna", "vcf-sv-research-index"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("sv_reformat", "clinical"),
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/sv_reformat/case_id_comb_ann_vep_parsed_ranked.selected.vcf.gz",
        "tags": ["case_id", "mip-dna", "vcf-sv-clinical"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("sv_reformat", "clinical"),
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/sv_reformat/case_id_comb_ann_vep_parsed_ranked.selected.vcf.gz.csi",
        "tags": ["case_id", "mip-dna", "vcf-sv-clinical-index"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("vcf2cytosure_ar",),
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/vcf2cytosure_ar/case_id_cyto.sample_id.cgh",
        "tags": ["mip-dna", "sample_id", "vcf2cytosure"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("peddy_ar", "peddy"),
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/peddy_ar/case_id_gatkcomb.peddy.ped",
        "tags": ["case_id", "mip-dna", "ped", "peddy"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("peddy_ar", "ped_check"),
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/peddy_ar/case_id_gatkcomb.ped_check.csv",
        "tags": ["case_id", "mip-dna", "ped-check", "peddy"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("peddy_ar", "sex_check"),
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/peddy_ar/case_id_gatkcomb.sex_check.csv",
        "tags": ["case_id", "mip-dna", "peddy", "sex-check"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("endvariantannotationblock", "research"),
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/endvariantannotationblock/case_id_gatkcomb_rhocall_vt_af_frqf_cadd_vep_parsed_ranked.vcf.gz",
        "tags": ["case_id", "mip-dna", "vcf-snv-research"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("endvariantannotationblock", "research"),
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/endvariantannotationblock/case_id_gatkcomb_rhocall_vt_af_frqf_cadd_vep_parsed_ranked.vcf.gz.tbi",
        "tags": ["case_id", "mip-dna", "vcf-snv-research-index"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("endvariantannotationblock", "clinical"),
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/endvariantannotationblock/case_id_gatkcomb_rhocall_vt_af_frqf_cadd_vep_parsed_ranked.selected.vcf.gz",
        "tags": ["case_id", "mip-dna", "vcf-snv-clinical"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("endvariantannotationblock", "clinical"),
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/endvariantannotationblock/case_id_gatkcomb_rhocall_vt_af_frqf_cadd_vep_parsed_ranked.selected.vcf.gz.tbi",
        "tags": ["case_id", "mip-dna", "vcf-snv-clinical-index"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("qccollect_ar",),
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/qccollect_ar/case_id_qc_metrics.yaml",
        "tags": ["case_id", "mip-dna", "qcmetrics"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("version_collect_ar",),
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/version_collect_ar/case_id_vcol.yaml",
        "tags": ["case_id", "exe-ver", "mip-dna"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("multiqc_ar", "html"),
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/multiqc_ar/multiqc_report.html",
        "tags": ["case_id", "mip-dna", "multiqc-html"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("multiqc_ar", "json"),
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/multiqc_ar/multiqc_data/multiqc_data.json",
        "tags": ["case_id", "mip-dna", "multiqc-json"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("gatk_combinevariantcallsets",),
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/gatk_combinevariantcallsets/case_id_gatkcomb.bcf",
        "tags": ["case_id", "mip-dna", "snv-bcf", "snv-gbcf"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("gatk_combinevariantcallsets",),
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/gatk_combinevariantcallsets/case_id_gatkcomb.bcf.csi",
        "tags": ["case_id", "gbcf-index", "mip-dna"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("peddy_ar", "peddy"),
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/peddy_ar/case_id_gatkcomb.peddy.ped",
        "tags": ["case_id", "mip-dna", "ped", "peddy"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("peddy_ar", "sex_check"),
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/peddy_ar/case_id_gatkcomb.sex_check.csv",
        "tags": ["case_id", "mip-dna", "peddy", "sex-check"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("peddy_ar", "ped_check"),
        "path": "/path/to/rare-disease/cases/case_id/analysis/case_id/peddy_ar/case_id_gatkcomb.ped_check.csv",
        "tags": ["case_id", "mip-dna", "ped-check", "peddy"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("chromograph_ar",),
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/chromograph_ar/sample_id_lanes_5555_sorted_md_brecal_tcov_chromograph.tar.gz",
        "tags": ["chromograph", "mip-dna", "sample_id"],
    },
    {
        "archive": False,
        "deliverables_tag_map": ("sambamba_depth", "coverage"),
        "path": "/path/to/rare-disease/cases/case_id/analysis/sample_id/sambamba_depth/sample_id_lanes_5555_sorted_md_brecal_coverage.bed",
        "tags": ["coverage", "mip-dna", "sambamba-depth", "sample_id"],
    },
]
