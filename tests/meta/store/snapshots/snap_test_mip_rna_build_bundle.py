# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import GenericRepr, Snapshot


snapshots = Snapshot()

snapshots['test_build_bundle 1'] = {
    'created': GenericRepr('datetime.datetime(2020, 3, 1, 0, 0)'),
    'files': [
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/salmon_quant/quant.sf',
            'tags': [
                'meta',
                'salmon_quant',
                'rd-rna',
                'sample_id'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/star_fusion/star-fusion.fusion_predictions.abridged.tsv',
            'tags': [
                'meta',
                'star_fusion',
                'rd-rna',
                'sample_id'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/arriba_ar/sample_id_lanes_1234_trim_arriba.pdf',
            'tags': [
                'arriba_ar',
                'rd-rna',
                'sample_id',
                'meta',
                'arriba_report'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/arriba_ar/sample_id_lanes_1234_trim_arriba.tsv',
            'tags': [
                'meta',
                'arriba_ar',
                'rd-rna',
                'sample_id'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/stringtie_ar/sample_id_lanes_1234_trim_star_sorted_merged_strg.gtf',
            'tags': [
                'meta',
                'stringtie_ar',
                'rd-rna',
                'sample_id'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/gffcompare_ar/sample_id_lanes_1234_trim_star_sorted_merged_strg_gffcmp.gtf',
            'tags': [
                'meta',
                'rd-rna',
                'sample_id',
                'gffcompare_ar'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/markduplicates/sample_id_lanes_1234_trim_star_sorted_merged_md.cram',
            'tags': [
                'markduplicates',
                'rd-rna',
                'cram',
                'sample_id'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/gatk_asereadcounter/sample_id_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase.csv',
            'tags': [
                'gatk_asereadcounter',
                'meta',
                'rd-rna',
                'sample_id'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/bootstrapann/sample_id_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase_bootstr.vcf',
            'tags': [
                'bootstrapann',
                'rd-rna',
                'vcf',
                'sample_id'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/case_id/bcftools_merge/case_id_comb.vcf',
            'tags': [
                'case_id',
                'vcf',
                'rd-rna',
                'bcftools_merge'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/case_id/varianteffectpredictor/case_id_comb_vep.vcf',
            'tags': [
                'case_id',
                'vcf',
                'varianteffectpredictor',
                'rd-rna'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/case_id/version_collect_ar/case_id_vcol.yaml',
            'tags': [
                'meta',
                'case_id',
                'rd-rna',
                'version_collect_ar'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/case_id/multiqc_ar/multiqc_data/multiqc_data.json',
            'tags': [
                'json',
                'case_id',
                'rd-rna',
                'meta',
                'multiqc_ar'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/case_id/multiqc_ar/multiqc_report.html',
            'tags': [
                'html',
                'case_id',
                'rd-rna',
                'meta',
                'multiqc_ar'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/case_id_qc_sample_info.yaml',
            'tags': [
                'sample_info',
                'case_id',
                'rd-rna',
                'meta',
                'mip_analyse'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/reference_info.yaml',
            'tags': [
                'case_id',
                'rd-rna',
                'references_info',
                'meta',
                'mip_analyse'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/mip_log/2020-02-28/mip_2020-02-28T10:22:26.log',
            'tags': [
                'case_id',
                'rd-rna',
                'meta',
                'log',
                'mip_analyse'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/case_id_config.yaml',
            'tags': [
                'config_analysis',
                'case_id',
                'rd-rna',
                'meta',
                'mip_analyse'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/pedigree.yaml',
            'tags': [
                'pedigree',
                'case_id',
                'rd-rna',
                'meta',
                'mip_analyse'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/servers/config/cluster.ourplace.se/mip8.2-rna-stage.yaml',
            'tags': [
                'config',
                'case_id',
                'rd-rna',
                'meta',
                'mip_analyse'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/case_id/case_id.fam',
            'tags': [
                'pedigree_fam',
                'case_id',
                'rd-rna',
                'meta',
                'mip_analyse'
            ]
        }
    ],
    'name': 'case_id',
    'pipeline_version': 'v8.2.2'
}
