"""
1. Application + Version <- admin (DONE)
1. Customer <- admin
2. User <- admin (scout)
2. Panel <- scout
2. Sample <- lims
3. Family + FamilySample <- lims
3. Flowcell <- cgstats
4. Analysis <- housekeeper

Delivery <- ???
Pool <- lims
Genotype <- genotype

Manual: clinicalgenomics.se
"""
import datetime as dt
import logging
import re

import click
import pymongo
import ruamel.yaml
from housekeeper.store import api as housekeeeper_api

from cg.apps import lims as lims_app
from cg.apps import scoutapi, stats
from cg.constants import PRIORITY_MAP
from cg.store import Store, models
from cgadmin.store.api import AdminDatabase

# from cg.meta.transfer.flowcell import TransferFlowcell

LOG = logging.getLogger(__name__)


class ApplicationImporter(Store):

    """Import data about application tags."""

    def __init__(self, uri: str, admin: AdminDatabase):
        super(ApplicationImporter, self).__init__(uri)
        self.admin = admin

    def process(self):
        """Transfer application tag info from cgadmin."""
        query = self.admin.ApplicationTag
        count = query.count()
        with click.progressbar(
            query, length=count, label="applications"
        ) as progressbar:
            for admin_record in progressbar:
                data = self.extract(admin_record)
                if not self.application(data["tag"]):
                    new_record = self.build(data)
                    self.add(new_record)
        self.commit()

    def extract(self, record):
        """Extract info from an admin record."""
        target_reads = 0
        if "WIP" not in record.name:
            type_id = record.name[-4]
            number = int(record.name[-3:])
            if type_id == "R":
                target_reads = number * 1000000
            elif type_id == "K":
                target_reads = number * 1000
            elif type_id == "C":
                reads_per_1x = 300000000 / 30
                target_reads = number * reads_per_1x

        data = {
            "tag": record.name,
            "category": {
                "Microbial": "mic",
                "Panel": "tga",
                "Whole exome": "wes",
                "Whole genome": "wgs",
            }.get(record.category),
            "created_at": record.created_at,
            "minimum_order": record.minimum_order,
            "sequencing_depth": record.sequencing_depth,
            "target_reads": target_reads,
            "sample_amount": record.sample_amount,
            "sample_volume": record.sample_volume,
            "sample_concentration": record.sample_concentration,
            "priority_processing": record.priority_processing,
            "turnaround_time": record.turnaround_time,
            "updated_at": record.last_updated,
            "comment": record.comment,
            "description": record.versions[0].description
            if record.versions
            else "MISSING",
            "is_accredited": record.versions[0].is_accredited
            if record.versions
            else False,
            "percent_kth": record.versions[0].percent_kth if record.versions else None,
            "details": record.versions[0].description if record.versions else None,
            "limitations": record.versions[0].limitations if record.versions else None,
            "versions": [
                {
                    "version": version.version,
                    "valid_from": version.valid_from,
                    "price_standard": version.price_standard,
                    "price_priority": version.price_priority,
                    "price_express": version.price_express,
                    "price_research": version.price_research,
                    "comment": version.comment,
                    "created_at": version.valid_from,
                    "updated_at": version.last_updated,
                }
                for version in record.versions
            ],
        }
        return data

    def build(self, data: dict):
        """Build database objects."""
        kwargs = dict(
            turnaround_time=data["turnaround_time"],
            minimum_order=data["minimum_order"],
            sequencing_depth=data["sequencing_depth"],
            target_reads=data["target_reads"],
            sample_amount=data["sample_amount"],
            sample_volume=data["sample_volume"],
            sample_concentration=data["sample_concentration"],
            priority_processing=data["priority_processing"],
            details=data["details"],
            limitations=data["limitations"],
            comment=data["comment"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )
        new_record = self.add_application(
            tag=data["tag"],
            category=data["category"],
            description=data["description"],
            is_accredited=data["is_accredited"],
            percent_kth=data["percent_kth"],
            **kwargs,
        )
        for version in data["versions"]:
            version_kwargs = dict(
                comment=version["comment"],
                created_at=version["created_at"],
                updated_at=version["updated_at"],
            )
            new_version = self.add_version(
                application=new_record,
                version=version["version"],
                valid_from=version["valid_from"],
                prices=dict(
                    standard=version["price_standard"],
                    priority=version["price_priority"],
                    express=version["price_express"],
                    research=version["price_research"],
                ),
            )
            new_record.versions.append(new_version)
        return new_record


class CustomerImporter(Store):

    """Import data about customers."""

    def __init__(self, uri: str, admin: AdminDatabase):
        super(CustomerImporter, self).__init__(uri)
        self.admin = admin

    def process(self):
        """Transfer customer info from cgadmin."""
        query = self.admin.Customer
        count = query.count()
        with click.progressbar(query, length=count, label="customers") as progressbar:
            for admin_record in progressbar:
                data = self.extract(admin_record)
                if not self.customer(data["internal_id"]):
                    new_record = self.build(data)
                    self.add(new_record)
        self.commit()

    def extract(self, record):
        """Extract info about a customer."""
        data = {
            "internal_id": record.customer_id,
            "name": record.name,
            "scout_access": record.scout_access,
            "agreement_date": (
                dt.datetime.combine(record.agreement_date, dt.time())
                if record.agreement_date
                else None
            ),
            "agreement_registration": record.agreement_registration,
            "invoice_address": record.invoice_address,
            "invoice_reference": record.invoice_reference,
            "organisation_number": record.organisation_number,
            "project_account_ki": record.project_account_ki,
            "project_account_kth": record.project_account_kth,
            "uppmax_account": record.uppmax_account,
            "primary_contact": (
                record.primary_contact.email if record.primary_contact else None
            ),
            "delivery_contact": (
                record.delivery_contact.email if record.delivery_contact else None
            ),
            "invoice_contact": (
                record.invoice_contact.email if record.invoice_contact else None
            ),
        }
        return data

    def build(self, data: dict):
        """Build a database record."""
        kwargs = dict(
            agreement_date=data["agreement_date"],
            agreement_registration=data["agreement_registration"],
            project_account_ki=data["project_account_ki"],
            project_account_kth=data["project_account_kth"],
            organisation_number=data["organisation_number"],
            invoice_address=data["invoice_address"],
            invoice_reference=data["invoice_reference"],
            uppmax_account=data["uppmax_account"],
            primary_contact=data["primary_contact"],
            delivery_contact=data["delivery_contact"],
            invoice_contact=data["invoice_contact"],
        )
        new_record = self.add_customer(
            internal_id=data["internal_id"],
            name=data["name"],
            scout_access=data["scout_access"],
            **kwargs,
        )
        return new_record


class UserImporter(Store):

    """Import data about users."""

    def __init__(self, uri: str, admin: AdminDatabase):
        super(UserImporter, self).__init__(uri)
        self.admin = admin

    def process(self):
        """Transfer cgadmin info to store."""
        query = self.admin.User
        count = query.count()
        with click.progressbar(query, length=count, label="users") as progressbar:
            for admin_record in progressbar:
                data = self.extract(admin_record)
                if not self.user(data["email"]):
                    new_record = self.build(data)
                    self.add(new_record)
        self.commit()

    def extract(self, record):
        """Extract info about a customer."""
        data = {
            "name": record.name,
            "email": record.email,
            "is_admin": record.is_admin,
            "customer": record.customers[0].customer_id
            if record.customers
            else "cust999",
        }
        return data

    def build(self, data: dict):
        """Build a database record."""
        customer_obj = self.customer(data["customer"])
        new_record = self.add_user(
            customer=customer_obj,
            email=data["email"],
            name=data["name"],
            is_admin=data["is_admin"],
        )
        return new_record


class PanelImporter(Store):

    """Import data about gene panels."""

    def __init__(self, uri: str, scout):
        super(PanelImporter, self).__init__(uri)
        self.scout = scout

    def process(self):
        """Transfer scout info to store."""
        panel_names = self.scout.panel_collection.find().distinct("panel_name")
        count = len(panel_names)
        with click.progressbar(
            panel_names, length=count, label="panels"
        ) as progressbar:
            for panel_name in progressbar:
                scout_record = self.scout.panel_collection.find(
                    {"panel_name": panel_name}
                ).sort("version", pymongo.DESCENDING)[0]
                data = self.extract(scout_record)
                if self.panel(data["abbrev"]) is None:
                    new_record = self.build(data)
                    self.add(new_record)
        self.commit()

    def extract(self, record):
        """Extract info about a customer."""
        data = {
            "name": record["display_name"],
            "abbrev": record["panel_name"],
            "customer": record["institute"],
            "version": record["version"],
            "date": record["date"],
            "genes": len(record["genes"]),
        }
        return data

    def build(self, data: dict):
        """Build a database record."""
        customer_obj = self.customer(data["customer"])
        new_record = self.add_panel(
            customer=customer_obj,
            name=data["name"],
            abbrev=data["abbrev"],
            version=data["version"],
            date=data["date"],
            genes=data["genes"],
        )
        return new_record


class SampleImporter(Store):

    """Import data about samples."""

    def __init__(self, uri: str, lims):
        super(SampleImporter, self).__init__(uri)
        self.lims = lims

    def process(self):
        """Transfer lims info to store."""
        for customer_obj in [self.customer("cust002")]:
            # if self.samples(customer=customer_obj).first():
            #     continue
            samples = self.lims.get_samples(udf=dict(customer=customer_obj.internal_id))
            count = len(samples)
            label = f"samples | {customer_obj.internal_id}"
            with click.progressbar(samples, length=count, label=label) as progressbar:
                for lims_sample in progressbar:
                    if self.sample(lims_sample.id) is not None:
                        continue
                    if self.sample(lims_sample.id):
                        continue
                    data = self.extract(lims_sample)
                    if data is None:
                        continue
                    new_record = self.build(customer_obj, data)
                    if new_record is None:
                        continue
                    self.add(new_record)
            self.commit()

    def extract(self, lims_sample):
        """Extract lims info."""
        sample = self.lims.sample(lims_sample.id)

        if sample["application"] is None:
            LOG.debug(f"missing application udf: {sample}")
            return None
        elif sample["application"].startswith(("MW", "RML", "MET")):
            return None

        ticket_match = re.search(r"([0-9]{6})", sample["project"]["name"])
        data = {
            "internal_id": sample["id"],
            "order": sample["project"]["name"],
            "ticket_number": int(ticket_match.group()) if ticket_match else None,
            "ordered_at": sample["project"]["date"],
            "name": sample["name"],
            "sex": sample["sex"],
            "application": sample["application"],
            "application_version": sample["application_version"],
            "received_at": sample["received"],
            "is_external": (sample["application"][:3] in ("EXX", "WGX")),
            "is_tumour": (sample.get("tumor") == "yes"),
            "comment": sample["comment"],
        }

        if sample["priority"] not in PRIORITY_MAP:
            LOG.warning(f"unknown priority: {sample['id']} - {sample['priority']}")
            data["priority"] = "standard"
        else:
            data["priority"] = sample["priority"]

        capture_kit = lims_sample.udf.get("Capture Library version")
        data["capture_kit"] = (
            capture_kit if capture_kit and capture_kit != "NA" else None
        )
        return data

    def build(self, customer_obj, data):
        """Build a record."""
        application_obj = self.application(data["application"])
        if application_obj is None:
            LOG.warning(
                f"unknown application tag: {data['internal_id']} - {data['application']}"
            )
            return None
        version_obj = self.application_version(
            application_obj, data["application_version"]
        )
        version_obj = version_obj if version_obj else application_obj.versions[-1]
        kwargs = dict(capture_kit=data["capture_kit"])
        new_record = self.add_sample(
            name=data["name"],
            sex=data["sex"] or "unknown",
            internal_id=data["internal_id"],
            ordered=data["ordered_at"],
            received=data["received_at"],
            order=data["order"],
            external=data["is_external"],
            tumour=data["is_tumour"],
            priority=data["priority"] or "standard",
            ticket=data["ticket_number"],
            comment=data["comment"],
            **kwargs,
        )
        new_record.customer = customer_obj
        new_record.application_version = version_obj
        return new_record


class FamilyImporter(Store):

    """Import data about families."""

    def __init__(self, uri: str, lims):
        super(FamilyImporter, self).__init__(uri)
        self.lims = lims

    def process(self):
        """Process data."""
        for customer_obj in [self.customer("cust002")]:
            # if self.families(customer=customer_obj).first():
            #     continue
            query = self.samples(customer=customer_obj)
            label = f"families | {customer_obj.internal_id}"
            with click.progressbar(
                query, length=query.count(), label=label
            ) as progressbar:
                for sample_obj in progressbar:
                    sample = self.lims.sample(sample_obj.internal_id)
                    if sample["family"] is None:
                        continue
                    if self.find_family(customer_obj, sample["family"]):
                        continue
                    samples = [
                        self.lims.sample(family_sample.id)
                        for family_sample in self.lims.get_samples(
                            udf={
                                "customer": sample["customer"],
                                "familyID": sample["family"],
                            }
                        )
                    ]
                    samples = [
                        sample
                        for sample in samples
                        if sample["application"]
                        and not sample["application"].startswith(("MW", "RML", "MET"))
                    ]
                    data = self.extract(sample["family"], samples)
                    new_records = self.build(customer_obj, data)
                    self.add(list(new_records))
            self.commit()

    def extract(self, family_name, samples):
        """Extract LIMS information."""
        sample_map = {sample["name"]: sample["id"] for sample in samples}

        panels = set([])
        for sample in samples:
            if sample["panels"]:
                panels.update(sample["panels"])

        data = {
            "name": family_name,
            "panels": list(panels) if panels else ["OMIM-AUTO"],
            "links": [],
        }
        for sample in samples:
            sample_data = {
                "sample": sample["id"],
                "status": sample["status"] or "unknown",
            }
            for parent_key in ["mother", "father"]:
                parent_name = sample_map.get(sample[parent_key])
                if parent_name in sample_map:
                    sample_data[parent_key] = parent_name
                else:
                    if sample[parent_key] is None:
                        sample_data[parent_key] = None
                    elif re.match(
                        "^[A-Z]{3}[1-9]{3,4}A[1-9]{1,2}$", sample[parent_key]
                    ):
                        sample_data[parent_key] = sample[parent_key]
                    else:
                        sample_data[parent_key] = None
            data["links"].append(sample_data)
        return data

    def build(self, customer_obj, data):
        """Build database objects."""
        samples = {}
        for link in data["links"]:
            sample_obj = self.sample(link["sample"])
            if sample_obj is None:
                LOG.warning(f"sample not found: {link['sample']}")
                continue
            samples[link["sample"]] = sample_obj
        priorities = set(sample.priority_human for sample in samples.values())
        if len(priorities) == 1:
            priority = priorities.pop()
        else:
            if "express" in priorities:
                priority = "express"
            elif "priority" in priorities:
                priority = "priority"
            else:
                priority = "standard"

        new_record = self.add_family(
            name=data["name"], priority=priority, panels=data["panels"]
        )
        new_record.customer = customer_obj
        yield new_record

        for link_data in data["links"]:
            try:
                link_obj = self.relate_sample(
                    family=new_record,
                    sample=samples[link_data["sample"]],
                    status=link_data["status"],
                    father=(
                        samples[link_data["father"]] if link_data["father"] else None
                    ),
                    mother=(
                        samples[link_data["mother"]] if link_data["mother"] else None
                    ),
                )
                yield link_obj
            except Exception:
                LOG.warning("Missing link")


# class FlowcellImporter(TransferFlowcell):

#     """Import info from cgstats."""

#     def process(self):
#         """Transfer cgstats info to store."""
#         query = self.stats.Flowcell.query
#         with click.progressbar(query, length=query.count(), label='flowcells') as progressbar:
#             for stats_record in progressbar:
#                 new_record = self.transfer(stats_record.flowcellname, store=False)
#                 self.db.add(new_record)
#         self.db.commit()


class AnalysisImporter(Store):
    def __init__(self, uri: str, hk_api):
        super(AnalysisImporter, self).__init__(uri)
        self.hk = hk_api

    def process(self):
        """Transfer housekeeeper info to store."""
        query = self.hk.runs()
        with click.progressbar(
            query, length=query.count(), label="analyses"
        ) as progressbar:
            for hk_record in progressbar:
                data = self.extract(hk_record)

                customer_obj = self.customer(data["customer"])
                family_obj = self.find_family(customer_obj, data["family"])
                if family_obj is None:
                    LOG.error(
                        f"family not found: {data['customer']} | {data['family']}"
                    )
                    continue

                if not self.analysis(family_obj, data["analyzed"]):
                    new_record = self.build(family_obj, data)
                    self.add(new_record)
        self.commit()

    def extract(self, hk_record):
        return {
            "pipeline": hk_record.pipeline,
            "version": hk_record.pipeline_version,
            "analyzed": hk_record.analyzed_at,
            "uploaded": hk_record.delivered_at,
            "primary": hk_record.case.runs[0] == hk_record,
            "family": hk_record.case.family_id,
            "customer": hk_record.case.customer,
        }

    def build(self, family_obj, data):
        new_record = self.add_analysis(
            pipeline=data["pipeline"],
            version=data["version"],
            completed_at=data["analyzed"],
            uploaded=data["uploaded"] or dt.datetime(1970, 1, 1),
            primary=data["primary"],
        )
        new_record.family = family_obj
        return new_record


@click.command()
@click.option("--admin", required=True, help="CG admin connection string")
@click.option("--housekeeper", required=True, help="Old housekeeper connection string")
@click.argument("config_file", type=click.File())
def transfer(admin, housekeeper, config_file):
    """Transfer stuff from external interfaces."""
    config = ruamel.yaml.safe_load(config_file)
    admin_api = AdminDatabase(admin)

    # ApplicationImporter(config['database'], admin_api).process()
    # CustomerImporter(config['database'], admin_api).process()
    # UserImporter(config['database'], admin_api).process()

    # PanelImporter(config['database'], scoutapi.ScoutAPI(config)).process()

    lims_api = lims_app.LimsAPI(config)
    SampleImporter(config["database"], lims_api).process()
    FamilyImporter(config["database"], lims_api).process()
    # FlowcellImporter(Store(config['database']), stats.StatsAPI(config)).process()

    # housekeeeper_api.manager(housekeeper)
    # AnalysisImporter(config['database'], housekeeeper_api).process()

    # # set all samples from 2016 as received + sequenced
    # status = Store(config['database'])
    # old_date = dt.datetime(2017, 1, 1)
    # (models.Sample.query.filter(
    #     models.Sample.received_at == None,
    #     models.Sample.sequenced_at == None,
    #     models.Sample.is_external == False
    # ).filter(models.Sample.ordered_at < old_date)
    #  .update({models.Sample.received_at: dt.datetime(1970, 1, 1),
    #           models.Sample.sequenced_at: dt.datetime(1970, 1, 1)}))
    # status.commit()

    # # set all families to analyze "on hold"
    # for family_obj in status.families_to_analyze(limit=1000):
    #     LOG.info(f"setting family on hold: {family_obj.name}")
    #     family_obj.action = 'hold'
    # status.commit()


if __name__ == "__main__":
    transfer()
