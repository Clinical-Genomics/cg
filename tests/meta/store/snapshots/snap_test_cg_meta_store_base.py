# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import GenericRepr, Snapshot


snapshots = Snapshot()

snapshots['test_build_bundle 1'] = {
    'created': GenericRepr('datetime.datetime(2020, 3, 1, 0, 0)'),
    'files': {
        'path': 'mock_path'
    },
    'name': 'case_id',
    'pipeline_version': 'v8.2.2'
}

snapshots['test_parse_files 1'] = [
    {
        'archive': False,
        'deliverables_tag_map': (
            'salmon_quant'
        ,),
        'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/salmon_quant/quant.sf',
        'tags': [
            'meta',
            'mip-rna',
            'salmon-quant',
            'sample_id'
        ]
    },
    {
        'archive': False,
        'deliverables_tag_map': (
            'star_fusion'
        ,),
        'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/star_fusion/star-fusion.fusion_predictions.abridged.tsv',
        'tags': [
            'meta',
            'mip-rna',
            'sample_id',
            'star-fusion'
        ]
    },
    {
        'archive': False,
        'deliverables_tag_map': (
            'arriba_ar',
            'arriba_report'
        ),
        'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/arriba_ar/sample_id_lanes_1234_trim_arriba.pdf',
        'tags': [
            'arriba-ar',
            'arriba-report',
            'meta',
            'mip-rna',
            'sample_id'
        ]
    },
    {
        'archive': False,
        'deliverables_tag_map': (
            'arriba_ar',
            'arriba_ar'
        ),
        'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/arriba_ar/sample_id_lanes_1234_trim_arriba.tsv',
        'tags': [
            'arriba-ar',
            'meta',
            'mip-rna',
            'sample_id'
        ]
    },
    {
        'archive': False,
        'deliverables_tag_map': (
            'stringtie_ar'
        ,),
        'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/stringtie_ar/sample_id_lanes_1234_trim_star_sorted_merged_strg.gtf',
        'tags': [
            'meta',
            'mip-rna',
            'sample_id',
            'stringtie-ar'
        ]
    },
    {
        'archive': False,
        'deliverables_tag_map': (
            'gffcompare_ar'
        ,),
        'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/gffcompare_ar/sample_id_lanes_1234_trim_star_sorted_merged_strg_gffcmp.gtf',
        'tags': [
            'gffcompare-ar',
            'meta',
            'mip-rna',
            'sample_id'
        ]
    },
    {
        'archive': False,
        'deliverables_tag_map': (
            'markduplicates'
        ,),
        'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/markduplicates/sample_id_lanes_1234_trim_star_sorted_merged_md.cram',
        'tags': [
            'cram',
            'mip-rna',
            'sample_id'
        ]
    },
    {
        'archive': False,
        'deliverables_tag_map': (
            'markduplicates'
        ,),
        'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/markduplicates/sample_id_lanes_1234_trim_star_sorted_merged_md.cram.crai',
        'tags': [
            'cram',
            'cram-index',
            'mip-rna',
            'sample_id'
        ]
    },
    {
        'archive': False,
        'deliverables_tag_map': (
            'gatk_asereadcounter'
        ,),
        'path': '/path/to/rare-disease/cases/case_id/analysis/sample_id/gatk_asereadcounter/sample_id_lanes_1234_trim_star_sorted_merged_md_splitncigar_brecal_haptc_filtered_ase.csv',
        'tags': [
            'gatk-asereadcounter',
            'meta',
            'mip-rna',
            'sample_id'
        ]
    },
    {
        'archive': False,
        'deliverables_tag_map': (
            'bootstrapann'
        ,),
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
        'deliverables_tag_map': (
            'bcftools_merge'
        ,),
        'path': '/path/to/rare-disease/cases/case_id/analysis/case_id/bcftools_merge/case_id_comb.vcf',
        'tags': [
            'bcftools-merge',
            'case_id',
            'mip-rna',
            'vcf'
        ]
    },
    {
        'archive': False,
        'deliverables_tag_map': (
            'varianteffectpredictor'
        ,),
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
        'deliverables_tag_map': (
            'version_collect_ar'
        ,),
        'path': '/path/to/rare-disease/cases/case_id/analysis/case_id/version_collect_ar/case_id_vcol.yaml',
        'tags': [
            'case_id',
            'meta',
            'mip-rna',
            'version-collect-ar'
        ]
    },
    {
        'archive': False,
        'deliverables_tag_map': (
            'multiqc_ar',
            'json'
        ),
        'path': '/path/to/rare-disease/cases/case_id/analysis/case_id/multiqc_ar/multiqc_data/multiqc_data.json',
        'tags': [
            'case_id',
            'meta',
            'mip-rna',
            'multiqc-json'
        ]
    },
    {
        'archive': False,
        'deliverables_tag_map': (
            'multiqc_ar',
            'html'
        ),
        'path': '/path/to/rare-disease/cases/case_id/analysis/case_id/multiqc_ar/multiqc_report.html',
        'tags': [
            'case_id',
            'meta',
            'mip-rna',
            'multiqc-html'
        ]
    },
    {
        'archive': False,
        'deliverables_tag_map': (
            'mip_analyse',
            'sample_info'
        ),
        'path': '/path/to/rare-disease/cases/case_id/analysis/case_id_qc_sample_info.yaml',
        'tags': [
            'case_id',
            'meta',
            'mip-analyse',
            'mip-rna',
            'sample-info'
        ]
    },
    {
        'archive': False,
        'deliverables_tag_map': (
            'mip_analyse',
            'references_info'
        ),
        'path': '/path/to/rare-disease/cases/case_id/analysis/reference_info.yaml',
        'tags': [
            'case_id',
            'meta',
            'mip-analyse',
            'mip-rna',
            'reference-info'
        ]
    },
    {
        'archive': False,
        'deliverables_tag_map': (
            'mip_analyse',
            'log'
        ),
        'path': '/path/to/rare-disease/cases/case_id/analysis/mip_log/2020-02-28/mip_2020-02-28T10:22:26.log',
        'tags': [
            'case_id',
            'log',
            'meta',
            'mip-analyse',
            'mip-rna'
        ]
    },
    {
        'archive': False,
        'deliverables_tag_map': (
            'mip_analyse',
            'config_analysis'
        ),
        'path': '/path/to/rare-disease/cases/case_id/analysis/case_id_config.yaml',
        'tags': [
            'case_id',
            'config-analysis',
            'meta',
            'mip-analyse',
            'mip-rna'
        ]
    },
    {
        'archive': False,
        'deliverables_tag_map': (
            'mip_analyse',
            'pedigree'
        ),
        'path': '/path/to/rare-disease/cases/case_id/pedigree.yaml',
        'tags': [
            'case_id',
            'meta',
            'mip-analyse',
            'mip-rna',
            'pedigree'
        ]
    },
    {
        'archive': False,
        'deliverables_tag_map': (
            'mip_analyse',
            'config'
        ),
        'path': '/path/to/servers/config/cluster.ourplace.se/mip8.2-rna-stage.yaml',
        'tags': [
            'case_id',
            'config',
            'meta',
            'mip-analyse',
            'mip-rna'
        ]
    },
    {
        'archive': False,
        'deliverables_tag_map': (
            'mip_analyse',
            'pedigree_fam'
        ),
        'path': '/path/to/rare-disease/cases/case_id/analysis/case_id/case_id.fam',
        'tags': [
            'case_id',
            'meta',
            'mip-analyse',
            'mip-rna',
            'pedigree-fam'
        ]
    }
]
