# -*- coding: utf-8 -*-
import logging
from pathlib import Path

from cg.apps import hk, coverage
from cg.store import models, Store

log = logging.getLogger(__name__)


class UploadCoverageApi(object):

    def __init__(self, status_api: Store, hk_api: hk.HousekeeperAPI,
                 chanjo_api: coverage.ChanjoAPI):
        self.status = status_api
        self.hk = hk_api
        self.chanjo = chanjo_api

    def data(self, analysis_obj: models.Analysis) -> dict:
        """Get data for uploading coverage."""
        family_id = analysis_obj.family.internal_id
        data = {
            'family': family_id,
            'family_name': analysis_obj.family.name,
            'samples': [],
        }
        for link_obj in analysis_obj.family.links:
            analysis_date = analysis_obj.started_at or analysis_obj.completed_at
            hk_version = self.hk.version(family_id, analysis_date)
            hk_coverage = self.hk.files(version=hk_version.id,
                                        tags=[link_obj.sample.internal_id, 'coverage']).first()
            data['samples'].append({
                'sample': link_obj.sample.internal_id,
                'sample_name': link_obj.sample.name,
                'coverage': hk_coverage.full_path,
            })
        return data

    def upload(self, data: dict, replace: bool = False):
        """Upload coverage to Chanjo from an analysis."""
        for sample_data in data['samples']:
            chanjo_sample = self.chanjo.sample(sample_data['sample'])
            if chanjo_sample and replace:
                self.chanjo.delete_sample(chanjo_sample)
            elif chanjo_sample:
                log.warning(f"sample already loaded, skipping: {sample_data['sample']}")
                continue

            log.debug(f"upload coverage for sample: {sample_data['sample']}")
            with Path(sample_data['coverage']).open() as bed_stream:
                self.chanjo.upload(
                    sample_id=sample_data['sample'],
                    sample_name=sample_data['sample_name'],
                    group_id=data['family'],
                    group_name=data['family_name'],
                    bed_stream=bed_stream,
                )
