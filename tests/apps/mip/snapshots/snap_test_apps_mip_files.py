# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
# pylint: disable-all
from __future__ import unicode_literals

from snapshottest import GenericRepr, Snapshot


snapshots = Snapshot()

snapshots['test_parse_sampleinfo_rna_result_contents 1'] = {
    'bcftools_merge': '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/finequagga_comb.vcf',
    'case': 'finequagga',
    'config_file_path': '/home/proj/stage/rare-disease/cases/finequagga/analysis/finequagga_config.yaml',
    'date': GenericRepr('datetime.datetime(2019, 11, 21, 14, 31, 2)'),
    'is_finished': True,
    'multiqc_html': '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/multiqc_report.html',
    'multiqc_json': '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/multiqc_data.json',
    'pedigree_path': '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/finequagga.fam',
    'qcmetrics_path': '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/qcmetrics_file.stub',
    'samples': [
        {
            'bam': '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/ACC5963A1_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal.bam',
            'bootstrap_vcf': [
                '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/foo_ACC5963A1_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase_bootstr.vcf',
                '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/bar_ACC5963A1_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase_bootstr.vcf'
            ],
            'gatk_asereadcounter': [
                '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/ACC5963A1_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase.csv'
            ],
            'gatk_baserecalibration': [
                '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/ACC5963A1_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal.bam'
            ],
            'gffcompare_ar': [
                '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/ACC5963A1_lanes_1234_trim_star_sorted_merged_strg_gffcmp.gtf'
            ],
            'id': 'ACC5963A1',
            'mark_duplicates': [
                '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/ACC5963A1_lanes_1234_trim_star_sorted_merged_md_metric'
            ],
            'salmon_quant': [
                '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/quant.sf'
            ],
            'star_fusion': '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/star-fusion.fusion_predictions.tsv',
            'stringtie_ar': [
                '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/ACC5963A1_lanes_1234_trim_star_sorted_merged_strg.gtf'
            ]
        }
    ],
    'vep_path': '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/finequagga_comb_vep.vcf',
    'version': 'v7.1.4',
    'version_collect_ar_path': '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/finequagga_vcol.yaml',
    'vp_stderr_file': None
}
