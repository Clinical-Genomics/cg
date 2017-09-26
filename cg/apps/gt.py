# -*- coding: utf-8 -*-
import logging

from alchy import Manager
from genotype.store import api, models
from genotype.load.vcf import load_vcf

log = logging.getLogger(__name__)


class GenotypeAPI(Manager):

    def __init__(self, config: dict):
        alchy_config = dict(SQLALCHEMY_DATABASE_URI=config['genotype']['database'])
        super(GenotypeAPI, self).__init__(config=alchy_config, Model=models.Model)

    def upload(self, bcf_path: str, samples_sex: dict, force: bool=False):
        """Upload genotypes for a family of samples."""
        snps = api.snps()
        analyses = load_vcf(bcf_path, snps)
        for analysis_obj in analyses:
            log.debug('loading VCF genotypes for sample: %s', analysis_obj.sample_id)
            is_saved = api.add_analysis(self, analysis_obj, replace=force)
            if is_saved:
                log.info('loaded VCF genotypes for sample: %s', analysis_obj.sample_id)
            else:
                log.warn('skipped, found previous analysis: %s', analysis_obj.sample_id)

            if is_saved or force:
                analysis_obj.sex = samples_sex[analysis_obj.sample_id]['analysis']
                analysis_obj.sample.sex = samples_sex[analysis_obj.sample_id]['pedigree']
                self.commit()
