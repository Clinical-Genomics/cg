"""Builds MIP RNA bundle for linking in Housekeeper"""


def build_bundle_rna(config_data: dict, sampleinfo_data: dict) -> dict:
    """Create a new bundle for RNA."""
    data = {
        'name': config_data['case'],
        'created': sampleinfo_data['date'],
        'pipeline_version': sampleinfo_data['version'],
        'files': get_files_rna(config_data, sampleinfo_data),
    }
    return data


def get_files_rna(config_data: dict, sampleinfo_data: dict) -> dict:
    """Get all the files from the MIP RNA files."""

    data = [{
        'path': config_data['config_path'],
        'tags': ['mip-config', 'rd-rna'],
        'archive': True,
    }, {
        'path': config_data['log_path'],
        'tags': ['mip-log', 'rd-rna'],
        'archive': True,
    }, {
        'path': config_data['sampleinfo_path'],
        'tags': ['sampleinfo', 'rd-rna'],
        'archive': True,
    }, {
        'path': sampleinfo_data['bcftools_merge'],
        'tags': ['bcftools-combined-vcf', 'rd-rna'],
        'archive': True,
    }, {
        'path': sampleinfo_data['multiqc_html'],
        'tags': ['multiqc-html', 'rd-rna'],
        'archive': True,
    }, {
        'path': sampleinfo_data['multiqc_json'],
        'tags': ['multiqc-json', 'rd-rna'],
        'archive': True,
    }, {
        'path': sampleinfo_data['pedigree_path'],
        'tags': ['pedigree', 'rd-rna'],
        'archive': True,
    }, {
        'path': sampleinfo_data['qcmetrics_path'],
        'tags': ['qcmetrics', 'rd-rna'],
        'archive': True,
    }, {
        'path': sampleinfo_data['vep_path'],
        'tags': ['vep-vcf', 'rd-rna'],
        'archive': True,
    }, {
        'path': sampleinfo_data['version_collect_ar_path'],
        'tags': ['versions', 'rd-rna'],
        'archive': True,
    }]

    if sampleinfo_data['vp_stderr_file'] is not None:
        data.append({
            'path': sampleinfo_data['vp_stderr_file'],
            'tags': ['vp-stderr', 'rd-rna'],
            'archive': True,
        })

    for sample_data in sampleinfo_data['samples']:
        data.append({
            'path': sample_data['bootstrap_vcf'],
            'tags': ['bootstrap-vcf', sample_data['id'], 'rd-rna'],
            'archive': False,
        })
        data.append({
            'path': sample_data['gatk_asereadcounter'],
            'tags': ['ase-readcounts', sample_data['id'], 'rd-rna'],
            'archive': False,
        })
        data.append({
            'path': sample_data['gatk_baserecalibration'],
            'tags': ['bam', 'baserecalibration', sample_data['id'], 'rd-rna'],
            'archive': False,
        })
        data.append({
            'path': sample_data['gffcompare_ar'],
            'tags': ['gff-compare-ar', sample_data['id'], 'rd-rna'],
            'archive': False,
        })
        data.append({
            'path': sample_data['mark_duplicates'],
            'tags': ['mark-duplicates', sample_data['id'], 'rd-rna'],
            'archive': False,
        })
        data.append({
            'path': sample_data['salmon_quant'],
            'tags': ['salmon-quant', sample_data['id'], 'rd-rna'],
            'archive': False,
        })
        data.append({
            'path': sample_data['star_fusion'],
            'tags': ['star-fusion', sample_data['id'], 'rd-rna'],
            'archive': False,
        })
        data.append({
            'path': sample_data['stringtie_ar'],
            'tags': ['stringtie-ar', sample_data['id'], 'rd-rna'],
            'archive': False,
            })

    return data
