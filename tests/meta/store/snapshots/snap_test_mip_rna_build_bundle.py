# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
# pylint: disable-all

from __future__ import unicode_literals

from snapshottest import GenericRepr, Snapshot


snapshots = Snapshot()

snapshots['test_get_rna_files 1'] = [
    {
        'archive': True,
        'path': '/home/proj/stage/rare-disease/cases/finequagga/analysis/finequagga_config.yaml',
        'tags': [
            'mip-config',
            'rd-rna'
        ]
    },
    {
        'archive': True,
        'path': '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/mip_2019-11-21T14:31:02.log',
        'tags': [
            'mip-log',
            'rd-rna'
        ]
    },
    {
        'archive': True,
        'path': '/home/proj/stage/rare-disease/cases/finequagga/analysis/finequagga_qc_sample_info.yaml',
        'tags': [
            'sampleinfo',
            'rd-rna'
        ]
    },
    {
        'archive': True,
        'path': '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/finequagga_comb.vcf',
        'tags': [
            'bcftools-combined-vcf',
            'rd-rna'
        ]
    },
    {
        'archive': True,
        'path': '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/multiqc_report.html',
        'tags': [
            'multiqc-html',
            'rd-rna'
        ]
    },
    {
        'archive': True,
        'path': '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/multiqc_data.json',
        'tags': [
            'multiqc-json',
            'rd-rna'
        ]
    },
    {
        'archive': True,
        'path': '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/finequagga.fam',
        'tags': [
            'pedigree',
            'rd-rna'
        ]
    },
    {
        'archive': True,
        'path': '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/qcmetrics_file.stub',
        'tags': [
            'qcmetrics',
            'rd-rna'
        ]
    },
    {
        'archive': True,
        'path': '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/finequagga_comb_vep.vcf',
        'tags': [
            'vep-vcf',
            'rd-rna'
        ]
    },
    {
        'archive': True,
        'path': '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/finequagga_vcol.yaml',
        'tags': [
            'versions',
            'rd-rna'
        ]
    },
    {
        'archive': False,
        'path': [
            '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/foo_ACC5963A1_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase_bootstr.vcf',
            '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/bar_ACC5963A1_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase_bootstr.vcf'
        ],
        'tags': [
            'bootstrap-vcf',
            'ACC5963A1',
            'rd-rna'
        ]
    },
    {
        'archive': False,
        'path': [
            '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/ACC5963A1_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase.csv'
        ],
        'tags': [
            'ase-readcounts',
            'ACC5963A1',
            'rd-rna'
        ]
    },
    {
        'archive': False,
        'path': [
            '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/ACC5963A1_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal.bam'
        ],
        'tags': [
            'bam',
            'baserecalibration',
            'ACC5963A1',
            'rd-rna'
        ]
    },
    {
        'archive': False,
        'path': [
            '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/ACC5963A1_lanes_1234_trim_star_sorted_merged_strg_gffcmp.gtf'
        ],
        'tags': [
            'gff-compare-ar',
            'ACC5963A1',
            'rd-rna'
        ]
    },
    {
        'archive': False,
        'path': [
            '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/ACC5963A1_lanes_1234_trim_star_sorted_merged_md_metric'
        ],
        'tags': [
            'mark-duplicates',
            'ACC5963A1',
            'rd-rna'
        ]
    },
    {
        'archive': False,
        'path': [
            '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/quant.sf'
        ],
        'tags': [
            'salmon-quant',
            'ACC5963A1',
            'rd-rna'
        ]
    },
    {
        'archive': False,
        'path': '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/star-fusion.fusion_predictions.tsv',
        'tags': [
            'star-fusion',
            'ACC5963A1',
            'rd-rna'
        ]
    },
    {
        'archive': False,
        'path': [
            '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/ACC5963A1_lanes_1234_trim_star_sorted_merged_strg.gtf'
        ],
        'tags': [
            'stringtie-ar',
            'ACC5963A1',
            'rd-rna'
        ]
    }
]

snapshots['test_build_bundle_rna 1'] = {
    'created': GenericRepr('datetime.datetime(2019, 11, 21, 14, 31, 2)'),
    'files': [
        {
            'archive': True,
            'path': '/home/proj/stage/rare-disease/cases/finequagga/analysis/finequagga_config.yaml',
            'tags': [
                'mip-config',
                'rd-rna'
            ]
        },
        {
            'archive': True,
            'path': '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/mip_2019-11-21T14:31:02.log',
            'tags': [
                'mip-log',
                'rd-rna'
            ]
        },
        {
            'archive': True,
            'path': '/home/proj/stage/rare-disease/cases/finequagga/analysis/finequagga_qc_sample_info.yaml',
            'tags': [
                'sampleinfo',
                'rd-rna'
            ]
        },
        {
            'archive': True,
            'path': '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/finequagga_comb.vcf',
            'tags': [
                'bcftools-combined-vcf',
                'rd-rna'
            ]
        },
        {
            'archive': True,
            'path': '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/multiqc_report.html',
            'tags': [
                'multiqc-html',
                'rd-rna'
            ]
        },
        {
            'archive': True,
            'path': '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/multiqc_data.json',
            'tags': [
                'multiqc-json',
                'rd-rna'
            ]
        },
        {
            'archive': True,
            'path': '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/finequagga.fam',
            'tags': [
                'pedigree',
                'rd-rna'
            ]
        },
        {
            'archive': True,
            'path': '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/qcmetrics_file.stub',
            'tags': [
                'qcmetrics',
                'rd-rna'
            ]
        },
        {
            'archive': True,
            'path': '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/finequagga_comb_vep.vcf',
            'tags': [
                'vep-vcf',
                'rd-rna'
            ]
        },
        {
            'archive': True,
            'path': '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/finequagga_vcol.yaml',
            'tags': [
                'versions',
                'rd-rna'
            ]
        },
        {
            'archive': False,
            'path': [
                '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/foo_ACC5963A1_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase_bootstr.vcf',
                '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/bar_ACC5963A1_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase_bootstr.vcf'
            ],
            'tags': [
                'bootstrap-vcf',
                'ACC5963A1',
                'rd-rna'
            ]
        },
        {
            'archive': False,
            'path': [
                '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/ACC5963A1_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase.csv'
            ],
            'tags': [
                'ase-readcounts',
                'ACC5963A1',
                'rd-rna'
            ]
        },
        {
            'archive': False,
            'path': [
                '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/ACC5963A1_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal.bam'
            ],
            'tags': [
                'bam',
                'baserecalibration',
                'ACC5963A1',
                'rd-rna'
            ]
        },
        {
            'archive': False,
            'path': [
                '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/ACC5963A1_lanes_1234_trim_star_sorted_merged_strg_gffcmp.gtf'
            ],
            'tags': [
                'gff-compare-ar',
                'ACC5963A1',
                'rd-rna'
            ]
        },
        {
            'archive': False,
            'path': [
                '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/ACC5963A1_lanes_1234_trim_star_sorted_merged_md_metric'
            ],
            'tags': [
                'mark-duplicates',
                'ACC5963A1',
                'rd-rna'
            ]
        },
        {
            'archive': False,
            'path': [
                '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/quant.sf'
            ],
            'tags': [
                'salmon-quant',
                'ACC5963A1',
                'rd-rna'
            ]
        },
        {
            'archive': False,
            'path': '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/star-fusion.fusion_predictions.tsv',
            'tags': [
                'star-fusion',
                'ACC5963A1',
                'rd-rna'
            ]
        },
        {
            'archive': False,
            'path': [
                '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/ACC5963A1_lanes_1234_trim_star_sorted_merged_strg.gtf'
            ],
            'tags': [
                'stringtie-ar',
                'ACC5963A1',
                'rd-rna'
            ]
        }
    ],
    'name': 'finequagga',
    'pipeline_version': 'v7.1.4'
}

snapshots['test_build_bundle_rna_no_missing_vpstderr 1'] = {
    'created': GenericRepr('datetime.datetime(2019, 11, 21, 14, 31, 2)'),
    'files': [
        {
            'archive': True,
            'path': '/home/proj/stage/rare-disease/cases/finequagga/analysis/finequagga_config.yaml',
            'tags': [
                'mip-config',
                'rd-rna'
            ]
        },
        {
            'archive': True,
            'path': '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/mip_2019-11-21T14:31:02.log',
            'tags': [
                'mip-log',
                'rd-rna'
            ]
        },
        {
            'archive': True,
            'path': '/home/proj/stage/rare-disease/cases/finequagga/analysis/finequagga_qc_sample_info.yaml',
            'tags': [
                'sampleinfo',
                'rd-rna'
            ]
        },
        {
            'archive': True,
            'path': '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/finequagga_comb.vcf',
            'tags': [
                'bcftools-combined-vcf',
                'rd-rna'
            ]
        },
        {
            'archive': True,
            'path': '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/multiqc_report.html',
            'tags': [
                'multiqc-html',
                'rd-rna'
            ]
        },
        {
            'archive': True,
            'path': '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/multiqc_data.json',
            'tags': [
                'multiqc-json',
                'rd-rna'
            ]
        },
        {
            'archive': True,
            'path': '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/finequagga.fam',
            'tags': [
                'pedigree',
                'rd-rna'
            ]
        },
        {
            'archive': True,
            'path': '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/qcmetrics_file.stub',
            'tags': [
                'qcmetrics',
                'rd-rna'
            ]
        },
        {
            'archive': True,
            'path': '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/finequagga_comb_vep.vcf',
            'tags': [
                'vep-vcf',
                'rd-rna'
            ]
        },
        {
            'archive': True,
            'path': '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/finequagga_vcol.yaml',
            'tags': [
                'versions',
                'rd-rna'
            ]
        },
        {
            'archive': True,
            'path': '/some/path/file.name',
            'tags': [
                'vp-stderr',
                'rd-rna'
            ]
        },
        {
            'archive': False,
            'path': [
                '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/foo_ACC5963A1_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase_bootstr.vcf',
                '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/bar_ACC5963A1_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase_bootstr.vcf'
            ],
            'tags': [
                'bootstrap-vcf',
                'ACC5963A1',
                'rd-rna'
            ]
        },
        {
            'archive': False,
            'path': [
                '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/ACC5963A1_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase.csv'
            ],
            'tags': [
                'ase-readcounts',
                'ACC5963A1',
                'rd-rna'
            ]
        },
        {
            'archive': False,
            'path': [
                '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/ACC5963A1_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal.bam'
            ],
            'tags': [
                'bam',
                'baserecalibration',
                'ACC5963A1',
                'rd-rna'
            ]
        },
        {
            'archive': False,
            'path': [
                '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/ACC5963A1_lanes_1234_trim_star_sorted_merged_strg_gffcmp.gtf'
            ],
            'tags': [
                'gff-compare-ar',
                'ACC5963A1',
                'rd-rna'
            ]
        },
        {
            'archive': False,
            'path': [
                '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/ACC5963A1_lanes_1234_trim_star_sorted_merged_md_metric'
            ],
            'tags': [
                'mark-duplicates',
                'ACC5963A1',
                'rd-rna'
            ]
        },
        {
            'archive': False,
            'path': [
                '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/quant.sf'
            ],
            'tags': [
                'salmon-quant',
                'ACC5963A1',
                'rd-rna'
            ]
        },
        {
            'archive': False,
            'path': '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/star-fusion.fusion_predictions.tsv',
            'tags': [
                'star-fusion',
                'ACC5963A1',
                'rd-rna'
            ]
        },
        {
            'archive': False,
            'path': [
                '/home/proj/stage/rare-disease/cases/finequagga/analysis/files/ACC5963A1_lanes_1234_trim_star_sorted_merged_strg.gtf'
            ],
            'tags': [
                'stringtie-ar',
                'ACC5963A1',
                'rd-rna'
            ]
        }
    ],
    'name': 'finequagga',
    'pipeline_version': 'v7.1.4'
}
