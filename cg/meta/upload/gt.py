# -*- coding: utf-8 -*-
from pathlib import Path

import ruamel.yaml

from cg.apps import hk, gt, tb
from cg.store import models, Store


class UploadGenotypesAPI(object):

    def __init__(self, status_api: Store, hk_api: hk.HousekeeperAPI, tb_api: tb.TrailblazerAPI,
                 gt_api: gt.GenotypeAPI):
        self.status = status_api
        self.hk = hk_api
        self.tb = tb_api
        self.gt = gt_api

    def data(self, analysis_obj: models.Analysis) -> dict:
        """Fetch data about an analysis to load genotypes."""
        hk_version = self.hk.version(analysis_obj.family.internal_id, analysis_obj.analyzed_at)
        hk_bcf = self.hk.files(version=hk_version.id, tags=['snv-gbcf']).first()
        data = {
            'bcf': hk_bcf.full_path,
            'samples_sex': {},
        }
        analysis_sexes = self._analysis_sex(hk_version)
        for sample_obj in analysis_obj.family.samples:
            data['samples_sex'][sample_obj.internal_id] = {
                'pedigree': sample_obj.sex,
                'analysis': analysis_sexes[sample_obj.internal_id],
            }
        return data

    def _analysis_sex(self, hk_version: hk.models.Version) -> dict:
        """Fetch analysis sex for each sample of an analysis."""
        hk_qcmetrics = self.hk.files(version=hk_version.id, tags=['qcmetrics']).first()
        with Path(hk_qcmetrics.full_path) as in_stream:
            qcmetrics_raw = ruamel.yaml.safe_load(in_stream)
        qcmetrics_data = self.tb.parse_qcmetrics(qcmetrics_raw)
        data = {}
        for sample_data in qcmetrics_data['samples']:
            data[sample_data['id']] = sample_data['predicted_sex']
        return data

    def upload(self, data: dict):
        """Upload data about genotypes for a family of samples."""
        self.gt.upload(data['bcf'], data['samples_sex'])
