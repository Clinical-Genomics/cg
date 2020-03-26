# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import GenericRepr, Snapshot


snapshots = Snapshot()

snapshots["test_build_bundle_rna_no_missing_vpstderr 1"] = {
    "created": GenericRepr("datetime.datetime(2019, 11, 21, 14, 31, 2)"),
    "files": [
        {
            "archive": True,
            "path": "/path/to/stuff/rare-disease/cases/case_id/analysis/case_id_config.yaml",
            "tags": ["mip-config", "rd-rna"],
        },
        {
            "archive": True,
            "path": "/path/to/stuff/rare-disease/cases/case_id/analysis/files/mip_2019-11-21T14:31:02.log",
            "tags": ["mip-log", "rd-rna"],
        },
        {
            "archive": True,
            "path": "/path/to/stuff/rare-disease/cases/case_id/analysis/case_id_qc_sample_info.yaml",
            "tags": ["sampleinfo", "rd-rna"],
        },
        {
            "archive": True,
            "path": "/path/to/stuff/rare-disease/cases/case_id/analysis/files/case_id_comb.vcf",
            "tags": ["bcftools-combined-vcf", "rd-rna"],
        },
        {
            "archive": True,
            "path": "/path/to/stuff/rare-disease/cases/case_id/analysis/files/multiqc_report.html",
            "tags": ["multiqc-html", "rd-rna"],
        },
        {
            "archive": True,
            "path": "/path/to/stuff/rare-disease/cases/case_id/analysis/files/multiqc_data.json",
            "tags": ["multiqc-json", "rd-rna"],
        },
        {
            "archive": True,
            "path": "/path/to/stuff/rare-disease/cases/case_id/analysis/files/case_id.fam",
            "tags": ["pedigree", "rd-rna"],
        },
        {
            "archive": True,
            "path": "/path/to/stuff/rare-disease/cases/case_id/analysis/files/qcmetrics_file.stub",
            "tags": ["qcmetrics", "rd-rna"],
        },
        {
            "archive": True,
            "path": "/path/to/stuff/rare-disease/cases/case_id/analysis/files/case_id_comb_vep.vcf",
            "tags": ["vep-vcf", "rd-rna"],
        },
        {
            "archive": True,
            "path": "/path/to/stuff/rare-disease/cases/case_id/analysis/files/case_id_vcol.yaml",
            "tags": ["versions", "rd-rna"],
        },
        {
            "archive": False,
            "path": [
                "/path/to/stuff/rare-disease/cases/case_id/analysis/files/foo_sample_id_1_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase_bootstr.vcf",
                "/path/to/stuff/rare-disease/cases/case_id/analysis/files/bar_sample_id_1_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase_bootstr.vcf",
            ],
            "tags": ["bootstrap-vcf", "sample_id_1", "rd-rna"],
        },
        {
            "archive": False,
            "path": [
                "/path/to/stuff/rare-disease/cases/case_id/analysis/files/sample_id_1_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase.csv"
            ],
            "tags": ["ase-readcounts", "sample_id_1", "rd-rna"],
        },
        {
            "archive": False,
            "path": [
                "/path/to/stuff/rare-disease/cases/case_id/analysis/files/sample_id_1_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal.bam"
            ],
            "tags": ["bam", "baserecalibration", "sample_id_1", "rd-rna"],
        },
        {
            "archive": False,
            "path": [
                "/path/to/stuff/rare-disease/cases/case_id/analysis/files/sample_id_1_lanes_1234_trim_star_sorted_merged_strg_gffcmp.gtf"
            ],
            "tags": ["gff-compare-ar", "sample_id_1", "rd-rna"],
        },
        {
            "archive": False,
            "path": [
                "/path/to/stuff/rare-disease/cases/case_id/analysis/files/sample_id_1_lanes_1234_trim_star_sorted_merged_md_metric"
            ],
            "tags": ["mark-duplicates", "sample_id_1", "rd-rna"],
        },
        {
            "archive": False,
            "path": ["/path/to/stuff/rare-disease/cases/case_id/analysis/files/quant.sf"],
            "tags": ["salmon-quant", "sample_id_1", "rd-rna"],
        },
        {
            "archive": False,
            "path": "/path/to/stuff/rare-disease/cases/case_id/analysis/files/star-fusion.fusion_predictions.tsv",
            "tags": ["star-fusion", "sample_id_1", "rd-rna"],
        },
        {
            "archive": False,
            "path": [
                "/path/to/stuff/rare-disease/cases/case_id/analysis/files/sample_id_1_lanes_1234_trim_star_sorted_merged_strg.gtf"
            ],
            "tags": ["stringtie-ar", "sample_id_1", "rd-rna"],
        },
    ],
    "name": "case_id",
    "pipeline_version": "v7.1.4",
}

snapshots["test_get_rna_files 1"] = [
    {
        "archive": True,
        "path": "/path/to/stuff/rare-disease/cases/case_id/analysis/case_id_config.yaml",
        "tags": ["mip-config", "rd-rna"],
    },
    {
        "archive": True,
        "path": "/path/to/stuff/rare-disease/cases/case_id/analysis/files/mip_2019-11-21T14:31:02.log",
        "tags": ["mip-log", "rd-rna"],
    },
    {
        "archive": True,
        "path": "/path/to/stuff/rare-disease/cases/case_id/analysis/case_id_qc_sample_info.yaml",
        "tags": ["sampleinfo", "rd-rna"],
    },
    {
        "archive": True,
        "path": "/path/to/stuff/rare-disease/cases/case_id/analysis/files/case_id_comb.vcf",
        "tags": ["bcftools-combined-vcf", "rd-rna"],
    },
    {
        "archive": True,
        "path": "/path/to/stuff/rare-disease/cases/case_id/analysis/files/multiqc_report.html",
        "tags": ["multiqc-html", "rd-rna"],
    },
    {
        "archive": True,
        "path": "/path/to/stuff/rare-disease/cases/case_id/analysis/files/multiqc_data.json",
        "tags": ["multiqc-json", "rd-rna"],
    },
    {
        "archive": True,
        "path": "/path/to/stuff/rare-disease/cases/case_id/analysis/files/case_id.fam",
        "tags": ["pedigree", "rd-rna"],
    },
    {
        "archive": True,
        "path": "/path/to/stuff/rare-disease/cases/case_id/analysis/files/qcmetrics_file.stub",
        "tags": ["qcmetrics", "rd-rna"],
    },
    {
        "archive": True,
        "path": "/path/to/stuff/rare-disease/cases/case_id/analysis/files/case_id_comb_vep.vcf",
        "tags": ["vep-vcf", "rd-rna"],
    },
    {
        "archive": True,
        "path": "/path/to/stuff/rare-disease/cases/case_id/analysis/files/case_id_vcol.yaml",
        "tags": ["versions", "rd-rna"],
    },
    {
        "archive": False,
        "path": [
            "/path/to/stuff/rare-disease/cases/case_id/analysis/files/foo_sample_id_1_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase_bootstr.vcf",
            "/path/to/stuff/rare-disease/cases/case_id/analysis/files/bar_sample_id_1_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase_bootstr.vcf",
        ],
        "tags": ["bootstrap-vcf", "sample_id_1", "rd-rna"],
    },
    {
        "archive": False,
        "path": [
            "/path/to/stuff/rare-disease/cases/case_id/analysis/files/sample_id_1_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase.csv"
        ],
        "tags": ["ase-readcounts", "sample_id_1", "rd-rna"],
    },
    {
        "archive": False,
        "path": [
            "/path/to/stuff/rare-disease/cases/case_id/analysis/files/sample_id_1_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal.bam"
        ],
        "tags": ["bam", "baserecalibration", "sample_id_1", "rd-rna"],
    },
    {
        "archive": False,
        "path": [
            "/path/to/stuff/rare-disease/cases/case_id/analysis/files/sample_id_1_lanes_1234_trim_star_sorted_merged_strg_gffcmp.gtf"
        ],
        "tags": ["gff-compare-ar", "sample_id_1", "rd-rna"],
    },
    {
        "archive": False,
        "path": [
            "/path/to/stuff/rare-disease/cases/case_id/analysis/files/sample_id_1_lanes_1234_trim_star_sorted_merged_md_metric"
        ],
        "tags": ["mark-duplicates", "sample_id_1", "rd-rna"],
    },
    {
        "archive": False,
        "path": ["/path/to/stuff/rare-disease/cases/case_id/analysis/files/quant.sf"],
        "tags": ["salmon-quant", "sample_id_1", "rd-rna"],
    },
    {
        "archive": False,
        "path": "/path/to/stuff/rare-disease/cases/case_id/analysis/files/star-fusion.fusion_predictions.tsv",
        "tags": ["star-fusion", "sample_id_1", "rd-rna"],
    },
    {
        "archive": False,
        "path": [
            "/path/to/stuff/rare-disease/cases/case_id/analysis/files/sample_id_1_lanes_1234_trim_star_sorted_merged_strg.gtf"
        ],
        "tags": ["stringtie-ar", "sample_id_1", "rd-rna"],
    },
]

snapshots["test_build_bundle_rna 1"] = {
    "created": GenericRepr("datetime.datetime(2019, 11, 21, 14, 31, 2)"),
    "files": [
        {
            "archive": True,
            "path": "/path/to/stuff/rare-disease/cases/case_id/analysis/case_id_config.yaml",
            "tags": ["mip-config", "rd-rna"],
        },
        {
            "archive": True,
            "path": "/path/to/stuff/rare-disease/cases/case_id/analysis/files/mip_2019-11-21T14:31:02.log",
            "tags": ["mip-log", "rd-rna"],
        },
        {
            "archive": True,
            "path": "/path/to/stuff/rare-disease/cases/case_id/analysis/case_id_qc_sample_info.yaml",
            "tags": ["sampleinfo", "rd-rna"],
        },
        {
            "archive": True,
            "path": "/path/to/stuff/rare-disease/cases/case_id/analysis/files/case_id_comb.vcf",
            "tags": ["bcftools-combined-vcf", "rd-rna"],
        },
        {
            "archive": True,
            "path": "/path/to/stuff/rare-disease/cases/case_id/analysis/files/multiqc_report.html",
            "tags": ["multiqc-html", "rd-rna"],
        },
        {
            "archive": True,
            "path": "/path/to/stuff/rare-disease/cases/case_id/analysis/files/multiqc_data.json",
            "tags": ["multiqc-json", "rd-rna"],
        },
        {
            "archive": True,
            "path": "/path/to/stuff/rare-disease/cases/case_id/analysis/files/case_id.fam",
            "tags": ["pedigree", "rd-rna"],
        },
        {
            "archive": True,
            "path": "/path/to/stuff/rare-disease/cases/case_id/analysis/files/qcmetrics_file.stub",
            "tags": ["qcmetrics", "rd-rna"],
        },
        {
            "archive": True,
            "path": "/path/to/stuff/rare-disease/cases/case_id/analysis/files/case_id_comb_vep.vcf",
            "tags": ["vep-vcf", "rd-rna"],
        },
        {
            "archive": True,
            "path": "/path/to/stuff/rare-disease/cases/case_id/analysis/files/case_id_vcol.yaml",
            "tags": ["versions", "rd-rna"],
        },
        {
            "archive": False,
            "path": [
                "/path/to/stuff/rare-disease/cases/case_id/analysis/files/foo_sample_id_1_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase_bootstr.vcf",
                "/path/to/stuff/rare-disease/cases/case_id/analysis/files/bar_sample_id_1_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase_bootstr.vcf",
            ],
            "tags": ["bootstrap-vcf", "sample_id_1", "rd-rna"],
        },
        {
            "archive": False,
            "path": [
                "/path/to/stuff/rare-disease/cases/case_id/analysis/files/sample_id_1_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase.csv"
            ],
            "tags": ["ase-readcounts", "sample_id_1", "rd-rna"],
        },
        {
            "archive": False,
            "path": [
                "/path/to/stuff/rare-disease/cases/case_id/analysis/files/sample_id_1_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal.bam"
            ],
            "tags": ["bam", "baserecalibration", "sample_id_1", "rd-rna"],
        },
        {
            "archive": False,
            "path": [
                "/path/to/stuff/rare-disease/cases/case_id/analysis/files/sample_id_1_lanes_1234_trim_star_sorted_merged_strg_gffcmp.gtf"
            ],
            "tags": ["gff-compare-ar", "sample_id_1", "rd-rna"],
        },
        {
            "archive": False,
            "path": [
                "/path/to/stuff/rare-disease/cases/case_id/analysis/files/sample_id_1_lanes_1234_trim_star_sorted_merged_md_metric"
            ],
            "tags": ["mark-duplicates", "sample_id_1", "rd-rna"],
        },
        {
            "archive": False,
            "path": ["/path/to/stuff/rare-disease/cases/case_id/analysis/files/quant.sf"],
            "tags": ["salmon-quant", "sample_id_1", "rd-rna"],
        },
        {
            "archive": False,
            "path": "/path/to/stuff/rare-disease/cases/case_id/analysis/files/star-fusion.fusion_predictions.tsv",
            "tags": ["star-fusion", "sample_id_1", "rd-rna"],
        },
        {
            "archive": False,
            "path": [
                "/path/to/stuff/rare-disease/cases/case_id/analysis/files/sample_id_1_lanes_1234_trim_star_sorted_merged_strg.gtf"
            ],
            "tags": ["stringtie-ar", "sample_id_1", "rd-rna"],
        },
    ],
    "name": "case_id",
    "pipeline_version": "v7.1.4",
}
