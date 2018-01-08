import logging
import datetime as dt
import time
from tempfile import NamedTemporaryFile

from cg.store import Store
from cg.apps.hk import HousekeeperAPI
from cg.apps.scoutapi import ScoutAPI
from cg.apps.beacon import BeaconApi

LOG = logging.getLogger(__name__)

class UploadBeaconApi():

    def __init__(self, status: Store, hk_api: HousekeeperAPI, scout_api: ScoutAPI,
                 beacon_api: BeaconApi):
        self.status = status
        self.housekeeper = hk_api
        self.scout = scout_api
        self.beacon = beacon_api

<<<<<<< HEAD
    def upload(self, family_id: str, panel: str=None, dataset: str='clinicalgenomics'):
=======
    def upload(self, family_id: str, panel: str=None, dataset: str='clinicalgenomics', outfile: str=None, customer: str=None, qual: int=20, reference: str="grch37"):
>>>>>>> added interface to cgbeacon
        """Upload variants to Beacon for a family."""
        family_obj = self.status.family(family_id)
        # get the VCF file
        analysis_obj = family_obj.analyses[0]
        analysis_date = analysis_obj.started_at or analysis_obj.completed_at
        hk_version = self.housekeeper.version(family_id, analysis_date)
        hk_vcf = self.housekeeper.files(version=hk_version.id, tags=['vcf-snv-clinical']).first()
        if hk_vcf is None:
            LOG.info("regular clinical VCF not found, trying old tag")
            hk_vcf = self.housekeeper.files(version=hk_version.id, tags=['vcf-clinical-bin']).first()
            if hk_vcf is None:
                LOG.error("Couldn't find old tag!")

        # list affected samples
        affected_samples = [link_obj.sample for link_obj in family_obj.links if
                            link_obj.status == 'affected']
        sample_ids = [sample_obj.internal_id for sample_obj in affected_samples]
        # generate BED file
        bed_lines = self.scout.export_panels([panel] if panel else family_obj.panels)

        outfile_name = 'cgbeacon_'+time.strftime("%Y%m%d-%H%M%S")

        temp_panel = NamedTemporaryFile('w+t',suffix='.'+panel)
        temp_panel.write('\n'.join(bed_lines))

        result = self.beacon.upload(
            vcf_path = hk_vcf.full_path,
            panel_path = temp_panel.name,
            dataset = dataset,
            outfile = outfile_name,
            customer = customer,
            samples = sample_ids,
            quality = qual,
            genome_reference = reference,
        )
        temp_panel.close()

        # mark samples as uploaded to beacon
        for sample_obj in affected_samples:
            sample_obj.beaconized_at = dt.datetime.now()
        self.status.commit()

        return result
