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
                'mip-rna',
                'salmon_quant',
                'sample_id'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/star_fusion/star-fusion.fusion_predictions.abridged.tsv',
            'tags': [
                'meta',
                'mip-rna',
                'sample_id',
                'star_fusion'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/arriba_ar/sample_id_lanes_1234_trim_arriba.pdf',
            'tags': [
                'arriba_ar',
                'arriba_report',
                'meta',
                'mip-rna',
                'sample_id'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/arriba_ar/sample_id_lanes_1234_trim_arriba.tsv',
            'tags': [
                'arriba_ar',
                'meta',
                'mip-rna',
                'sample_id'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/stringtie_ar/sample_id_lanes_1234_trim_star_sorted_merged_strg.gtf',
            'tags': [
                'meta',
                'mip-rna',
                'sample_id',
                'stringtie_ar'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/gffcompare_ar/sample_id_lanes_1234_trim_star_sorted_merged_strg_gffcmp.gtf',
            'tags': [
                'gffcompare_ar',
                'meta',
                'mip-rna',
                'sample_id'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/markduplicates/sample_id_lanes_1234_trim_star_sorted_merged_md.cram',
            'tags': [
                'cram',
                'markduplicates',
                'mip-rna',
                'sample_id'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/gatk_asereadcounter/sample_id_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase.csv',
            'tags': [
                'gatk_asereadcounter',
                'meta',
                'mip-rna',
                'sample_id'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/bootstrapann/sample_id_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase_bootstr.vcf',
            'tags': [
                'bootstrapann',
                'mip-rna',
                'sample_id',
                'vcf'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/case_id/bcftools_merge/case_id_comb.vcf',
            'tags': [
                'bcftools_merge',
                'case_id',
                'mip-rna',
                'vcf'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/case_id/varianteffectpredictor/case_id_comb_vep.vcf',
            'tags': [
                'case_id',
                'mip-rna',
                'varianteffectpredictor',
                'vcf'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/case_id/version_collect_ar/case_id_vcol.yaml',
            'tags': [
                'case_id',
                'meta',
                'mip-rna',
                'version_collect_ar'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/case_id/multiqc_ar/multiqc_data/multiqc_data.json',
            'tags': [
                'case_id',
                'json',
                'meta',
                'mip-rna',
                'multiqc_ar'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/case_id/multiqc_ar/multiqc_report.html',
            'tags': [
                'case_id',
                'html',
                'meta',
                'mip-rna',
                'multiqc_ar'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/case_id_qc_sample_info.yaml',
            'tags': [
                'case_id',
                'meta',
                'mip-rna',
                'mip_analyse',
                'sample_info'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/reference_info.yaml',
            'tags': [
                'case_id',
                'meta',
                'mip-rna',
                'mip_analyse',
                'references_info'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/mip_log/2020-02-28/mip_2020-02-28T10:22:26.log',
            'tags': [
                'case_id',
                'log',
                'meta',
                'mip-rna',
                'mip_analyse'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/case_id_config.yaml',
            'tags': [
                'case_id',
                'config_analysis',
                'meta',
                'mip-rna',
                'mip_analyse'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/pedigree.yaml',
            'tags': [
                'case_id',
                'meta',
                'mip-rna',
                'mip_analyse',
                'pedigree'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/servers/config/cluster.ourplace.se/mip8.2-rna-stage.yaml',
            'tags': [
                'case_id',
                'config',
                'meta',
                'mip-rna',
                'mip_analyse'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/case_id/case_id.fam',
            'tags': [
                'case_id',
                'meta',
                'mip-rna',
                'mip_analyse',
                'pedigree_fam'
            ]
        }
    ],
    'name': 'case_id',
    'pipeline_version': 'v8.2.2'
}

snapshots['test_get_files 1'] = [
    {
        'archive': False,
        'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/salmon_quant/quant.sf',
        'tags': [
            'meta',
            's',
            'salmon_quant',
            'sample_id',
            't',
            'w'
        ]
    },
    {
        'archive': False,
        'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/star_fusion/star-fusion.fusion_predictions.abridged.tsv',
        'tags': [
            'meta',
            's',
            'sample_id',
            'star_fusion',
            't',
            'w'
        ]
    },
    {
        'archive': False,
        'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/arriba_ar/sample_id_lanes_1234_trim_arriba.pdf',
        'tags': [
            'arriba_ar',
            'arriba_report',
            'meta',
            's',
            'sample_id',
            't',
            'w'
        ]
    },
    {
        'archive': False,
        'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/arriba_ar/sample_id_lanes_1234_trim_arriba.tsv',
        'tags': [
            'arriba_ar',
            'meta',
            's',
            'sample_id',
            't',
            'w'
        ]
    },
    {
        'archive': False,
        'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/stringtie_ar/sample_id_lanes_1234_trim_star_sorted_merged_strg.gtf',
        'tags': [
            'meta',
            's',
            'sample_id',
            'stringtie_ar',
            't',
            'w'
        ]
    },
    {
        'archive': False,
        'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/gffcompare_ar/sample_id_lanes_1234_trim_star_sorted_merged_strg_gffcmp.gtf',
        'tags': [
            'gffcompare_ar',
            'meta',
            's',
            'sample_id',
            't',
            'w'
        ]
    },
    {
        'archive': False,
        'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/markduplicates/sample_id_lanes_1234_trim_star_sorted_merged_md.cram',
        'tags': [
            'cram',
            'markduplicates',
            's',
            'sample_id',
            't',
            'w'
        ]
    },
    {
        'archive': False,
        'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/gatk_asereadcounter/sample_id_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase.csv',
        'tags': [
            'gatk_asereadcounter',
            'meta',
            's',
            'sample_id',
            't',
            'w'
        ]
    },
    {
        'archive': False,
        'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/bootstrapann/sample_id_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase_bootstr.vcf',
        'tags': [
            'bootstrapann',
            's',
            'sample_id',
            't',
            'vcf',
            'w'
        ]
    },
    {
        'archive': False,
        'path': '/path/to/rare-disease/cases/case_id/analysis/case_id/bcftools_merge/case_id_comb.vcf',
        'tags': [
            'bcftools_merge',
            'case_id',
            's',
            't',
            'vcf',
            'w'
        ]
    },
    {
        'archive': False,
        'path': '/path/to/rare-disease/cases/case_id/analysis/case_id/varianteffectpredictor/case_id_comb_vep.vcf',
        'tags': [
            'case_id',
            's',
            't',
            'varianteffectpredictor',
            'vcf',
            'w'
        ]
    },
    {
        'archive': False,
        'path': '/path/to/rare-disease/cases/case_id/analysis/case_id/version_collect_ar/case_id_vcol.yaml',
        'tags': [
            'case_id',
            'meta',
            's',
            't',
            'version_collect_ar',
            'w'
        ]
    },
    {
        'archive': False,
        'path': '/path/to/rare-disease/cases/case_id/analysis/case_id/multiqc_ar/multiqc_data/multiqc_data.json',
        'tags': [
            'case_id',
            'json',
            'meta',
            'multiqc_ar',
            's',
            't',
            'w'
        ]
    },
    {
        'archive': False,
        'path': '/path/to/rare-disease/cases/case_id/analysis/case_id/multiqc_ar/multiqc_report.html',
        'tags': [
            'case_id',
            'html',
            'meta',
            'multiqc_ar',
            's',
            't',
            'w'
        ]
    },
    {
        'archive': False,
        'path': '/path/to/rare-disease/cases/case_id/analysis/case_id_qc_sample_info.yaml',
        'tags': [
            'case_id',
            'meta',
            'mip_analyse',
            's',
            'sample_info',
            't',
            'w'
        ]
    },
    {
        'archive': False,
        'path': '/path/to/rare-disease/cases/case_id/analysis/reference_info.yaml',
        'tags': [
            'case_id',
            'meta',
            'mip_analyse',
            'references_info',
            's',
            't',
            'w'
        ]
    },
    {
        'archive': False,
        'path': '/path/to/rare-disease/cases/case_id/analysis/mip_log/2020-02-28/mip_2020-02-28T10:22:26.log',
        'tags': [
            'case_id',
            'log',
            'meta',
            'mip_analyse',
            's',
            't',
            'w'
        ]
    },
    {
        'archive': False,
        'path': '/path/to/rare-disease/cases/case_id/analysis/case_id_config.yaml',
        'tags': [
            'case_id',
            'config_analysis',
            'meta',
            'mip_analyse',
            's',
            't',
            'w'
        ]
    },
    {
        'archive': False,
        'path': '/path/to/rare-disease/cases/case_id/pedigree.yaml',
        'tags': [
            'case_id',
            'meta',
            'mip_analyse',
            'pedigree',
            's',
            't',
            'w'
        ]
    },
    {
        'archive': False,
        'path': '/path/to/servers/config/cluster.ourplace.se/mip8.2-rna-stage.yaml',
        'tags': [
            'case_id',
            'config',
            'meta',
            'mip_analyse',
            's',
            't',
            'w'
        ]
    },
    {
        'archive': False,
        'path': '/path/to/rare-disease/cases/case_id/analysis/case_id/case_id.fam',
        'tags': [
            'case_id',
            'meta',
            'mip_analyse',
            'pedigree_fam',
            's',
            't',
            'w'
        ]
    }
]
