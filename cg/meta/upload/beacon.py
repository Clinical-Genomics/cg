import datetime as dt
import tempfile

from cg.store import Store
from cg.apps.hk import HousekeeperAPI
from cg.apps.scoutapi import ScoutAPI


class UploadBeaconApi():
    
    def __init__(self, status: Store, hk_api: HousekeeperAPI, scout_api: ScoutAPI):
        self.status = status
        self.housekeeper = hk_api
        self.scout = scout_api
        self.beacon = None
    
    def upload(self, family_id: str, panel: str=None, dataset: str='clinicalgenomics'):
        """Upload variants to Beacon for a family."""
        family_obj = self.status.family(family_id)
        # get the VCF file
        analysis_obj = family_obj.analyses[0]
        analysis_date = analysis_obj.started_at or analysis_obj.completed_at
        hk_version = self.housekeeper.version(family_id, analysis_date)
        hk_vcf = self.housekeeper.files(version=hk_version.id, tags=['vcf-snv-clinical']).first()
        # list affected samples
        affected_samples = [link_obj.sample for link_obj in family_obj.links if
                            link_obj.status == 'affected']
        sample_ids = [sample_obj.internal_id for sample_obj in affected_samples]
        # generate BED file
        bed_lines = self.scout.export_panels([panel] if panel else family_obj.panels)
        with tempfile.NamedTemporaryFile() as temp_panel:
            temp_panel.write('\n'.join(bed_lines))

            result = self.beacon.upload(
                vcf_path=hk_vcf.full_path,
                samples=sample_ids,
                panel_path=temp_panel.name,
                dataset=dataset,
            )

        # mark samples as uploaded to beacon
        for sample_obj in affected_samples:
            sample_obj.beaconized_at = dt.datetime.now()
        self.status.commit()

        return result
