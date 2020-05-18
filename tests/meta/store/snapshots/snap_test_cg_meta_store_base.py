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
                'salmon-quant',
                'sample_id',
                'mip-rna'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/star_fusion/star-fusion.fusion_predictions.abridged.tsv',
            'tags': [
                'meta',
                'sample_id',
                'star-fusion',
                'mip-rna'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/arriba_ar/sample_id_lanes_1234_trim_arriba.pdf',
            'tags': [
                'sample_id',
                'mip-rna',
                'arriba-ar',
                'meta',
                'arriba-report'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/arriba_ar/sample_id_lanes_1234_trim_arriba.tsv',
            'tags': [
                'meta',
                'sample_id',
                'mip-rna',
                'arriba-ar'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/stringtie_ar/sample_id_lanes_1234_trim_star_sorted_merged_strg.gtf',
            'tags': [
                'meta',
                'sample_id',
                'stringtie-ar',
                'mip-rna'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/gffcompare_ar/sample_id_lanes_1234_trim_star_sorted_merged_strg_gffcmp.gtf',
            'tags': [
                'meta',
                'sample_id',
                'gffcompare-ar',
                'mip-rna'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/markduplicates/sample_id_lanes_1234_trim_star_sorted_merged_md.cram',
            'tags': [
                'markduplicates',
                'cram',
                'sample_id',
                'mip-rna'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/gatk_asereadcounter/sample_id_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase.csv',
            'tags': [
                'meta',
                'sample_id',
                'mip-rna',
                'gatk-asereadcounter'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/bootstrapann/sample_id_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase_bootstr.vcf',
            'tags': [
                'bootstrapann',
                'sample_id',
                'vcf',
                'mip-rna'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/case_id/bcftools_merge/case_id_comb.vcf',
            'tags': [
                'bcftools-merge',
                'vcf',
                'case_id',
                'mip-rna'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/case_id/varianteffectpredictor/case_id_comb_vep.vcf',
            'tags': [
                'vcf',
                'case_id',
                'mip-rna',
                'varianteffectpredictor'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/case_id/version_collect_ar/case_id_vcol.yaml',
            'tags': [
                'meta',
                'version-collect-ar',
                'case_id',
                'mip-rna'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/case_id/multiqc_ar/multiqc_data/multiqc_data.json',
            'tags': [
                'meta',
                'multiqc-json',
                'case_id',
                'mip-rna'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/case_id/multiqc_ar/multiqc_report.html',
            'tags': [
                'meta',
                'case_id',
                'mip-rna',
                'multiqc-html'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/case_id_qc_sample_info.yaml',
            'tags': [
                'mip-rna',
                'case_id',
                'mip-analyse',
                'sample-info',
                'meta'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/reference_info.yaml',
            'tags': [
                'mip-rna',
                'case_id',
                'mip-analyse',
                'meta',
                'reference-info'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/mip_log/2020-02-28/mip_2020-02-28T10:22:26.log',
            'tags': [
                'mip-rna',
                'log',
                'case_id',
                'mip-analyse',
                'meta'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/case_id_config.yaml',
            'tags': [
                'mip-rna',
                'case_id',
                'mip-analyse',
                'config-analysis',
                'meta'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/pedigree.yaml',
            'tags': [
                'pedigree',
                'mip-rna',
                'case_id',
                'mip-analyse',
                'meta'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/servers/config/cluster.ourplace.se/mip8.2-rna-stage.yaml',
            'tags': [
                'mip-rna',
                'case_id',
                'mip-analyse',
                'meta',
                'config'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/case_id/case_id.fam',
            'tags': [
                'pedigree-fam',
                'mip-rna',
                'case_id',
                'mip-analyse',
                'meta'
            ]
        },
        {
            'archive': False,
            'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/markduplicates/sample_id_lanes_1234_trim_star_sorted_merged_md.cram.crai',
            'tags': [
                'markduplicates-index',
                'cram',
                'sample_id',
                'mip-rna'
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
            'salmon-quant',
            'sample_id',
            'mip-rna'
        ]
    },
    {
        'archive': False,
        'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/star_fusion/star-fusion.fusion_predictions.abridged.tsv',
        'tags': [
            'meta',
            'sample_id',
            'star-fusion',
            'mip-rna'
        ]
    },
    {
        'archive': False,
        'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/arriba_ar/sample_id_lanes_1234_trim_arriba.pdf',
        'tags': [
            'sample_id',
            'mip-rna',
            'arriba-ar',
            'meta',
            'arriba-report'
        ]
    },
    {
        'archive': False,
        'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/arriba_ar/sample_id_lanes_1234_trim_arriba.tsv',
        'tags': [
            'meta',
            'sample_id',
            'mip-rna',
            'arriba-ar'
        ]
    },
    {
        'archive': False,
        'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/stringtie_ar/sample_id_lanes_1234_trim_star_sorted_merged_strg.gtf',
        'tags': [
            'meta',
            'sample_id',
            'stringtie-ar',
            'mip-rna'
        ]
    },
    {
        'archive': False,
        'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/gffcompare_ar/sample_id_lanes_1234_trim_star_sorted_merged_strg_gffcmp.gtf',
        'tags': [
            'meta',
            'sample_id',
            'gffcompare-ar',
            'mip-rna'
        ]
    },
    {
        'archive': False,
        'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/markduplicates/sample_id_lanes_1234_trim_star_sorted_merged_md.cram',
        'tags': [
            'markduplicates',
            'cram',
            'sample_id',
            'mip-rna'
        ]
    },
    {
        'archive': False,
        'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/gatk_asereadcounter/sample_id_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase.csv',
        'tags': [
            'meta',
            'sample_id',
            'mip-rna',
            'gatk-asereadcounter'
        ]
    },
    {
        'archive': False,
        'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/bootstrapann/sample_id_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase_bootstr.vcf',
        'tags': [
            'bootstrapann',
            'sample_id',
            'vcf',
            'mip-rna'
        ]
    },
    {
        'archive': False,
        'path': '/path/to/rare-disease/cases/case_id/analysis/case_id/bcftools_merge/case_id_comb.vcf',
        'tags': [
            'bcftools-merge',
            'vcf',
            'case_id',
            'mip-rna'
        ]
    },
    {
        'archive': False,
        'path': '/path/to/rare-disease/cases/case_id/analysis/case_id/varianteffectpredictor/case_id_comb_vep.vcf',
        'tags': [
            'vcf',
            'case_id',
            'mip-rna',
            'varianteffectpredictor'
        ]
    },
    {
        'archive': False,
        'path': '/path/to/rare-disease/cases/case_id/analysis/case_id/version_collect_ar/case_id_vcol.yaml',
        'tags': [
            'meta',
            'version-collect-ar',
            'case_id',
            'mip-rna'
        ]
    },
    {
        'archive': False,
        'path': '/path/to/rare-disease/cases/case_id/analysis/case_id/multiqc_ar/multiqc_data/multiqc_data.json',
        'tags': [
            'meta',
            'multiqc-json',
            'case_id',
            'mip-rna'
        ]
    },
    {
        'archive': False,
        'path': '/path/to/rare-disease/cases/case_id/analysis/case_id/multiqc_ar/multiqc_report.html',
        'tags': [
            'meta',
            'case_id',
            'mip-rna',
            'multiqc-html'
        ]
    },
    {
        'archive': False,
        'path': '/path/to/rare-disease/cases/case_id/analysis/case_id_qc_sample_info.yaml',
        'tags': [
            'mip-rna',
            'case_id',
            'mip-analyse',
            'sample-info',
            'meta'
        ]
    },
    {
        'archive': False,
        'path': '/path/to/rare-disease/cases/case_id/analysis/reference_info.yaml',
        'tags': [
            'mip-rna',
            'case_id',
            'mip-analyse',
            'meta',
            'reference-info'
        ]
    },
    {
        'archive': False,
        'path': '/path/to/rare-disease/cases/case_id/analysis/mip_log/2020-02-28/mip_2020-02-28T10:22:26.log',
        'tags': [
            'mip-rna',
            'log',
            'case_id',
            'mip-analyse',
            'meta'
        ]
    },
    {
        'archive': False,
        'path': '/path/to/rare-disease/cases/case_id/analysis/case_id_config.yaml',
        'tags': [
            'mip-rna',
            'case_id',
            'mip-analyse',
            'config-analysis',
            'meta'
        ]
    },
    {
        'archive': False,
        'path': '/path/to/rare-disease/cases/case_id/pedigree.yaml',
        'tags': [
            'pedigree',
            'mip-rna',
            'case_id',
            'mip-analyse',
            'meta'
        ]
    },
    {
        'archive': False,
        'path': '/path/to/servers/config/cluster.ourplace.se/mip8.2-rna-stage.yaml',
        'tags': [
            'mip-rna',
            'case_id',
            'mip-analyse',
            'meta',
            'config'
        ]
    },
    {
        'archive': False,
        'path': '/path/to/rare-disease/cases/case_id/analysis/case_id/case_id.fam',
        'tags': [
            'pedigree-fam',
            'mip-rna',
            'case_id',
            'mip-analyse',
            'meta'
        ]
    },
    {
        'archive': False,
        'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/markduplicates/sample_id_lanes_1234_trim_star_sorted_merged_md.cram.crai',
        'tags': [
            'markduplicates-index',
            'cram',
            'sample_id',
            'mip-rna'
        ]
    }
]
