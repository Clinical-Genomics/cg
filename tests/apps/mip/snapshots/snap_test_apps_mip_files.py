# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import GenericRepr, Snapshot

snapshots = Snapshot()

snapshots["test_parse_sampleinfo_rna_result_contents 1"] = {
    "bcftools_merge": "/path/to/stuff/rare-disease/cases/case_id/analysis/files/case_id_comb.vcf",
    "case": "case_id",
    "config_file_path": "/path/to/stuff/rare-disease/cases/case_id/analysis/case_id_config.yaml",
    "date": GenericRepr("datetime.datetime(2019, 11, 21, 14, 31, 2)"),
    "is_finished": True,
    "multiqc_html": "/path/to/stuff/rare-disease/cases/case_id/analysis/files/multiqc_report.html",
    "multiqc_json": "/path/to/stuff/rare-disease/cases/case_id/analysis/files/multiqc_data.json",
    "pedigree_path": "/path/to/stuff/rare-disease/cases/case_id/analysis/files/case_id.fam",
    "qcmetrics_path": "/path/to/stuff/rare-disease/cases/case_id/analysis/files/qcmetrics_file.stub",
    "samples": [
        {
            "bam": "/path/to/stuff/rare-disease/cases/case_id/analysis/files/sample_id_1_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal.bam",
            "bootstrap_vcf": [
                "/path/to/stuff/rare-disease/cases/case_id/analysis/files/foo_sample_id_1_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase_bootstr.vcf",
                "/path/to/stuff/rare-disease/cases/case_id/analysis/files/bar_sample_id_1_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase_bootstr.vcf",
            ],
            "gatk_asereadcounter": [
                "/path/to/stuff/rare-disease/cases/case_id/analysis/files/sample_id_1_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase.csv"
            ],
            "gatk_baserecalibration": [
                "/path/to/stuff/rare-disease/cases/case_id/analysis/files/sample_id_1_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal.bam"
            ],
            "gffcompare_ar": [
                "/path/to/stuff/rare-disease/cases/case_id/analysis/files/sample_id_1_lanes_1234_trim_star_sorted_merged_strg_gffcmp.gtf"
            ],
            "id": "sample_id_1",
            "mark_duplicates": [
                "/path/to/stuff/rare-disease/cases/case_id/analysis/files/sample_id_1_lanes_1234_trim_star_sorted_merged_md_metric"
            ],
            "salmon_quant": ["/path/to/stuff/rare-disease/cases/case_id/analysis/files/quant.sf"],
            "star_fusion": "/path/to/stuff/rare-disease/cases/case_id/analysis/files/star-fusion.fusion_predictions.tsv",
            "stringtie_ar": [
                "/path/to/stuff/rare-disease/cases/case_id/analysis/files/sample_id_1_lanes_1234_trim_star_sorted_merged_strg.gtf"
            ],
        }
    ],
    "vep_path": "/path/to/stuff/rare-disease/cases/case_id/analysis/files/case_id_comb_vep.vcf",
    "version": "v7.1.4",
    "version_collect_ar_path": "/path/to/stuff/rare-disease/cases/case_id/analysis/files/case_id_vcol.yaml",
}
