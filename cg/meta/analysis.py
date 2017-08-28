# -*- coding: utf-8 -*-
import logging
import re
from typing import List

from cg.apps import tb, hk, scoutapi, lims
from cg.store import models, Store

log = logging.getLogger(__name__)

COLLABORATORS = ('cust000', 'cust002', 'cust003', 'cust004', 'cust042')
MASTER_LIST = ('ENDO', 'EP', 'IEM', 'IBMFS', 'mtDNA', 'MIT', 'PEDHEP', 'OMIM-AUTO',
               'PIDCAD', 'PID', 'SKD', 'NMD', 'ATX', 'CTD', 'ID', 'SPG', 'Ataxi', 'AD-HSP')
COMBOS = {
    'DSD': ('DSD', 'HYP', 'SEXDIF', 'SEXDET'),
    'CM': ('CNM', 'CM'),
    'Horsel': ('Horsel', '141217', '141201'),
}
CAPTUREKIT_MAP = {'Agilent Sureselect CRE': 'agilent_sureselect_cre.v1',
                  'SureSelect CRE': 'agilent_sureselect_cre.v1',
                  'Agilent Sureselect V5': 'agilent_sureselect.v5',
                  'SureSelect Focused Exome': 'agilent_sureselect_focusedexome.v1',
                  'other': 'agilent_sureselect_cre.v1'}


class AnalysisAPI():

    def __init__(self, db: Store, hk_api: hk.HousekeeperAPI, scout_api: scoutapi.ScoutAPI,
                 tb_api: tb.TrailblazerAPI, lims_api: lims.LimsAPI):
        self.db = db
        self.tb = tb_api
        self.hk = hk_api
        self.scout = scout_api
        self.lims = lims_api

    def start(self, family_obj: models.Family, **kwargs):
        """Start the analysis."""
        if kwargs.get('priority') is None:
            if family_obj.priority == 0:
                kwargs['priority'] = 'low'
            elif family_obj.priority > 1:
                kwargs['priority'] = 'high'
            else:
                kwargs['priority'] = 'normal'
        self.tb.start(family_obj.internal_id, **kwargs)

    def config(self, family_obj: models.Family) -> dict:
        """Make the MIP config."""
        data = self.build_config(family_obj)
        config_data = self.tb.make_config(data)
        return config_data

    def build_config(self, family_obj: models.Family) -> dict:
        """Fetch data for creating a MIP config file."""
        data = {
            'family': family_obj.internal_id,
            'default_gene_panels': family_obj.panels,
            'samples': [],
        }
        for link in family_obj.links:
            sample_data = {
                'sample_id': link.sample.internal_id,
                'analysis_type': link.sample.application_version.application.category,
                'sex': link.sample.sex,
                'phenotype': link.status,
                'expected_coverage': link.sample.application_version.application.sequencing_depth,
            }
            if sample_data['analysis_type'] in ('tgs', 'wes'):
                capture_kit = self.lims.capture_kit(link.sample.internal_id)
                sample_data['capture_kit'] = CAPTUREKIT_MAP[capture_kit]
            if link.mother:
                sample_data['mother'] = link.mother.internal_id
            if link.father:
                sample_data['father'] = link.father.internal_id
            data['samples'].append(sample_data)
        return data

    def link_sample(self, link_obj: models.FamilySample):
        """Link FASTQ files for a sample."""
        file_objs = self.hk.files(bundle=link_obj.sample.internal_id, tags=['fastq'])
        files = []
        for file_obj in file_objs:
            data = {
                'path': file_obj.path,
                'lane': int(re.findall(r'_L([0-9]{3})_', file_obj.path)[0]),
                'flowcell': re.search(r'[0-9A-Z]{7}[XY]{2}', file_obj.path)[0],
                'read': int(re.findall(r'_R([0-9])_', file_obj.path)[0]),
                'undetermined': ('_Undetermined_' in file_obj.path),
            }
            # look for tile identifier (HiSeq X runs)
            matches = re.findall(r'-l[1-9]t([1-9]{2})_', file_obj.path)
            if len(matches) > 0:
                data['flowcell'] = f"{data['flowcell']}-{matches[0]}"
            files.append(data)

        self.tb.link(
            family=link_obj.family.internal_id,
            sample=link_obj.sample.internal_id,
            analysis_type=link_obj.sample.application_version.application.category,
            files=files,
        )

    def panel(self, family_obj: models.Family) -> List[str]:
        """Create the aggregated panel file."""
        all_panels = self.convert_panels(family_obj.customer.internal_id, family_obj.panels)
        bed_lines = self.scout.export_panels(all_panels)
        return bed_lines

    @staticmethod
    def convert_panels(customer, default_panels):
        """Convert between default panels and all panels included in gene list."""
        if customer in COLLABORATORS:
            # check if all default panels are part of master list
            if all(panel in MASTER_LIST for panel in default_panels):
                return MASTER_LIST

        # the rest are handled the same way
        all_panels = set(default_panels)

        # fill in extra panels if selection is part of a combo
        for panel in default_panels:
            if panel in COMBOS:
                for extra_panel in COMBOS[panel]:
                    all_panels.add(extra_panel)

        # add OMIM to every panel choice
        all_panels.add('OMIM-AUTO')

        return list(all_panels)
