# -*- coding: utf-8 -*-
import logging

from genotype.store import api
from genotype.load.vcf import load_vcf

log = logging.getLogger(__name__)


def connect(config):
    """Connect to the Housekeeper database."""
    gt_db = api.connect(config['genotype']['database'])
    return gt_db


def add(genotype_db, raw_bcf_path, force=False):
    """Add genotypes for an analysis run."""
    snps = api.snps()
    analyses = load_vcf(raw_bcf_path, snps)
    for analysis in analyses:
        log.debug('loading VCF genotypes for sample: %s', analysis.sample_id)
        is_saved = api.add_analysis(genotype_db, analysis, replace=force)
        if is_saved:
            log.info('loaded VCF genotypes for sample: %s', analysis.sample_id)
        else:
            log.warn('skipped, found previous analysis: %s', analysis.sample_id)
