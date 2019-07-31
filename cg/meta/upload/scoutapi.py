# -*- coding: utf-8 -*-
import logging

from cg.apps import hk, scoutapi, madeline
from cg.store import models, Store
from cg.meta.analysis import AnalysisAPI

LOG = logging.getLogger(__name__)


class UploadScoutAPI(object):

    def __init__(self, status_api: Store, hk_api: hk.HousekeeperAPI,
                 scout_api: scoutapi.ScoutAPI,
                 analysis_api: AnalysisAPI, madeline_exe: str, madeline=madeline,
                 ):
        self.status = status_api
        self.housekeeper = hk_api
        self.scout = scout_api
        self.madeline_exe = madeline_exe
        self.madeline = madeline
        self.analysis = analysis_api

    def generate_config(self, analysis_obj: models.Analysis) -> dict:
        """Fetch data about an analysis to load Scout."""
        analysis_date = analysis_obj.started_at or analysis_obj.completed_at
        hk_version = self.housekeeper.version(analysis_obj.family.internal_id, analysis_date)
        analysis_data = self.analysis.get_latest_metadata(analysis_obj.family.internal_id)

        data = {
            'owner': analysis_obj.family.customer.internal_id,
            'family': analysis_obj.family.internal_id,
            'family_name': analysis_obj.family.name,
            'samples': [],
            'analysis_date': analysis_obj.completed_at,
            'gene_panels': self.analysis.convert_panels(analysis_obj.family.customer.internal_id,
                                                      analysis_obj.family.panels),
            'default_gene_panels': analysis_obj.family.panels,
            'human_genome_build': analysis_data.get('genome_build'),
            'rank_model_version': analysis_data.get('rank_model_version'),
            'sv_rank_model_version': analysis_data.get('sv_rank_model_version')
        }

        for link_obj in analysis_obj.family.links:
            sample_id = link_obj.sample.internal_id
            bam_tags = ['bam', sample_id]
            bam_file = self.housekeeper.files(version=hk_version.id, tags=bam_tags).first()
            bam_path = bam_file.full_path if bam_file else None
            mt_bam_tags = ['bam-mt', sample_id]
            mt_bam_file = self.housekeeper.files(version=hk_version.id, tags=mt_bam_tags).first()
            mt_bam_path = mt_bam_file.full_path if mt_bam_file else None
            vcf2cytosure_tags = ['vcf2cytosure', sample_id]
            vcf2cytosure_file = self.housekeeper.files(version=hk_version.id, tags=vcf2cytosure_tags).first()
            vcf2cytosure_path = vcf2cytosure_file.full_path if vcf2cytosure_file else None
            data['samples'].append({
                'analysis_type': link_obj.sample.application_version.application.analysis_type,
                'sample_id': sample_id,
                'capture_kit': None,
                'father': link_obj.father.internal_id if link_obj.father else None,
                'mother': link_obj.mother.internal_id if link_obj.mother else None,
                'sample_name': link_obj.sample.name,
                'phenotype': link_obj.status,
                'sex': link_obj.sample.sex,
                'bam_path': bam_path,
                'mt_bam': mt_bam_path,
                'vcf2cytosure': vcf2cytosure_path,
            })

        files = {('vcf_snv', 'vcf-snv-clinical'), ('vcf_snv_research', 'vcf-snv-research'),
                 ('vcf_sv', 'vcf-sv-clinical'), ('vcf_sv_research', 'vcf-sv-research')}
        for scout_key, hk_tag in files:
            hk_vcf = self.housekeeper.files(version=hk_version.id, tags=[hk_tag]).first()
            data[scout_key] = str(hk_vcf.full_path)

        files = [('peddy_ped', 'ped'), ('peddy_sex', 'sex-check'), ('peddy_check', 'ped-check')]
        for scout_key, hk_tag in files:
            hk_file = self.housekeeper.files(version=hk_version.id, tags=['peddy', hk_tag]).first()
            if hk_file is None:
                LOG.debug(f"skipping missing file: {scout_key}")
            else:
                data[scout_key] = str(hk_file.full_path)

        files = [('delivery_report', 'delivery-report')]
        for scout_key, hk_tag in files:
            hk_file = self.housekeeper.files(version=hk_version.id, tags=[hk_tag]).first()
            if hk_file is None:
                LOG.debug(f"skipping missing file: {scout_key}")
            else:
                data[scout_key] = str(hk_file.full_path)

        if len(data['samples']) > 1:
            if any(sample['father'] or sample['mother'] for sample in data['samples']):
                svg_path = self.run_madeline(analysis_obj.family)
                data['madeline'] = svg_path
            else:
                LOG.info('family of unconnected samples - skip pedigree graph')
        else:
            LOG.info('family of 1 sample - skip pedigree graph')

        return data

    def run_madeline(self, family_obj: models.Family):
        """Generate a madeline file for an analysis."""
        samples = [{
            'sample': link_obj.sample.name,
            'sex': link_obj.sample.sex,
            'father': link_obj.father.name if link_obj.father else None,
            'mother': link_obj.mother.name if link_obj.mother else None,
            'status': link_obj.status,
        } for link_obj in family_obj.links]
        ped_stream = self.madeline.make_ped(family_obj.name, samples=samples)
        svg_path = self.madeline.run(self.madeline_exe, ped_stream)
        return svg_path
