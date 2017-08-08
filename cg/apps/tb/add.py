# -*- coding: utf-8 -*-
import logging
from pathlib import Path

import ruamel.yaml
from trailblazer.mip import files as mip_files

from cg.exc import AnalysisNotFinishedError

log = logging.getLogger(__name__)


class AddHandler:

    @classmethod
    def add_analysis(cls, config_stream):
        """Add a MIP analysis to Housekeeper."""
        config_raw = ruamel.yaml.safe_load(config_stream)
        config_data = mip_files.parse_config(config_raw)
        sampleinfo_raw = ruamel.yaml.safe_load(Path(config_data['sampleinfo_path']).open())
        sampleinfo_data = mip_files.parse_sampleinfo(sampleinfo_raw)
        if sampleinfo_data['is_finished'] is False:
            raise AnalysisNotFinishedError('analysis not finished')
        new_bundle = cls._build_bundle(config_data, sampleinfo_data)
        return new_bundle

    @classmethod
    def _build_bundle(cls, config_data: dict, sampleinfo_data: dict) -> dict:
        """Create a new bundle."""
        data = {
            'name': config_data['family'],
            'created': sampleinfo_data['date'],
            'pipeline_version': sampleinfo_data['version'],
            'files': cls._get_files(config_data, sampleinfo_data),
        }
        return data

    @staticmethod
    def _get_files(config_data: dict, sampleinfo_data: dict) -> dict:
        """Get all the files from the MIP files."""
        data = [{
            'path': config_data['config_path'],
            'tags': ['mip-config'],
            'archive': True,
        }, {
            'path': config_data['sampleinfo_path'],
            'tags': ['sampleinfo'],
            'archive': True,
        }, {
            'path': sampleinfo_data['pedigree_path'],
            'tags': ['pedigree'],
            'archive': False,
        }, {
            'path': config_data['log_path'],
            'tags': ['mip-log'],
            'archive': True,
        }, {
            'path': sampleinfo_data['qcmetrics_path'],
            'tags': ['qcmetrics'],
            'archive': True,
        }, {
            'path': sampleinfo_data['snv']['gbcf'],
            'tags': ['snv-gbcf'],
            'archive': True,
        }, {
            'path': f"{sampleinfo_data['snv']['gbcf']}.csi",
            'tags': ['snv-gbcf-index'],
            'archive': True,
        }]

        for variant_type in ['snv', 'sv']:
            for output_type in ['clinical', 'research']:
                vcf_path = sampleinfo_data[variant_type][f"{output_type}_vcf"]
                if vcf_path is None:
                    log.warn(f"missing file: {output_type} {variant_type} VCF")
                    continue
                vcf_tag = f"vcf-{variant_type}-{output_type}"
                data.append({
                    'path': vcf_path,
                    'tags': [vcf_tag],
                    'archive': True,
                })
                data.append({
                    'path': f"{vcf_path}.tbi",
                    'tags': [f"{vcf_tag}-index"],
                    'archive': True,
                })

        for sample_data in sampleinfo_data['samples']:
            data.append({
                'path': sample_data['sambamba'],
                'tags': ['coverage', sample_data['id']],
                'archive': False,
            })
            bam_path = sample_data['bam']
            data.append({
                'path': bam_path,
                'tags': ['bam', sample_data['id']],
                'archive': False,
            })
            data.append({
                'path': f"{bam_path}.bai",
                'tags': ['bam-index', sample_data['id']],
                'archive': False,
            })

        return data
