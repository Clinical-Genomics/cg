"""Module for Flask-Admin views"""
from flask import redirect, request, session, url_for
from flask_admin.contrib.sqla import ModelView
from flask_dance.contrib.google import google
from markupsafe import Markup

from cg.constants.constants import DataDelivery, Pipeline
from cg.server.ext import db
from cg.utils.flask.enum import SelectEnumField


class BaseView(ModelView):
    """Base for the specific views."""

    def is_accessible(self):
        user_obj = db.user(session.get("user_email"))
        return bool(google.authorized and user_obj and user_obj.is_admin)

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        return redirect(url_for("google.login", next=request.url))


def view_priority(unused1, unused2, model, unused3):
    """column formatter for priority"""
    del unused1, unused2, unused3
    return Markup("%s" % model.priority.name) if model else ""


def view_family_sample_link(unused1, unused2, model, unused3):
    """column formatter to open the family-sample view"""

    del unused1, unused2, unused3

    return Markup(
        "<a href='%s'>%s</a>"
        % (url_for("familysample.index_view", search=model.internal_id), model.internal_id)
    )


def is_external_application(unused1, unused2, model, unused3):
    """column formatter to open this view"""
    del unused1, unused2, unused3
    return model.application_version.application.is_external if model.application_version else ""


class ApplicationView(BaseView):
    """Admin view for Model.Application"""

    column_editable_list = [
        "description",
        "is_accredited",
        "target_reads",
        "percent_reads_guaranteed",
        "comment",
        "prep_category",
        "sequencing_depth",
        "min_sequencing_depth",
        "is_external",
        "turnaround_time",
        "sample_concentration",
        "priority_processing",
        "is_archived",
    ]
    column_exclude_list = [
        "minimum_order",
        "sample_amount",
        "sample_volume",
        "details",
        "limitations",
        "created_at",
        "updated_at",
        "category",
    ]
    column_filters = ["prep_category", "is_accredited"]
    column_searchable_list = ["tag", "prep_category"]
    form_excluded_columns = ["category"]

    @staticmethod
    def view_application_link(unused1, unused2, model, unused3):
        """column formatter to open this view"""
        del unused1, unused2, unused3
        return (
            Markup(
                "<a href='%s'>%s</a>"
                % (
                    url_for("application.index_view", search=model.application.tag),
                    model.application.tag,
                )
            )
            if model.application
            else ""
        )


class ApplicationVersionView(BaseView):
    """Admin view for Model.ApplicationVersion"""

    column_default_sort = ("valid_from", True)
    column_editable_list = [
        "valid_from",
        "price_standard",
        "price_priority",
        "price_express",
        "price_clinical_trials",
        "price_research",
    ]
    column_exclude_list = ["created_at", "updated_at"]
    column_filters = ["version", "application.tag"]
    column_formatters = {"application": ApplicationView.view_application_link}
    column_searchable_list = ["application.tag"]
    edit_modal = True
    form_excluded_columns = ["samples", "pools", "microbial_samples"]


class BedView(BaseView):
    """Admin view for Model.Bed"""

    column_default_sort = "name"
    column_editable_list = ["comment"]
    column_exclude_list = ["created_at"]
    column_filters = []
    column_searchable_list = ["name"]
    form_excluded_columns = ["created_at", "updated_at"]

    @staticmethod
    def view_bed_link(unused1, unused2, model, unused3):
        """column formatter to open this view"""
        del unused1, unused2, unused3
        return (
            Markup(
                "<a href='%s'>%s</a>"
                % (url_for("bed.index_view", search=model.bed.name), model.bed.name)
            )
            if model.bed
            else ""
        )


class BedVersionView(BaseView):
    """Admin view for Model.BedVersion"""

    column_default_sort = ("updated_at", True)
    column_editable_list = ["shortname", "filename", "comment", "designer", "checksum"]
    column_exclude_list = ["created_at"]
    form_excluded_columns = ["created_at", "updated_at", "samples"]
    column_filters = []
    column_formatters = {"bed": BedView.view_bed_link}
    column_searchable_list = ["bed.name"]
    edit_modal = True


class CustomerView(BaseView):
    """Admin view for Model.Customer"""

    column_editable_list = [
        "collaborations",
        "comment",
        "delivery_contact",
        "loqus_upload",
        "primary_contact",
        "priority",
        "return_samples",
        "scout_access",
    ]
    column_list = [
        "comment",
        "delivery_contact",
        "internal_id",
        "name",
        "primary_contact",
        "priority",
        "project_account_KI",
        "project_account_kth",
        "return_samples",
        "scout_access",
    ]
    column_filters = ["priority", "scout_access"]
    column_searchable_list = ["internal_id", "name"]
    form_excluded_columns = ["families", "samples", "pools", "orders", "invoices"]


class CollaborationView(BaseView):
    """Admin view for Model.CustomerGroup"""

    column_editable_list = ["name"]
    column_filters = []
    column_hide_backrefs = False
    column_list = ("internal_id", "name", "customers")
    column_searchable_list = ["internal_id", "name"]


class FamilyView(BaseView):
    """Admin view for Model.Family"""

    column_default_sort = ("created_at", True)
    column_editable_list = ["action", "comment"]
    column_exclude_list = ["created_at", "_cohorts", "synopsis"]
    column_filters = [
        "customer.internal_id",
        "priority",
        "action",
        "data_analysis",
        "data_delivery",
    ]
    column_formatters = {
        "internal_id": view_family_sample_link,
        "priority": view_priority,
    }
    column_searchable_list = ["internal_id", "name", "customer.internal_id"]
    form_excluded_columns = [
        "analyses",
        "_cohorts",
        "links",
        "synopsis",
    ]
    form_extra_fields = {
        "data_analysis": SelectEnumField(enum_class=Pipeline),
        "data_delivery": SelectEnumField(enum_class=DataDelivery),
    }

    @staticmethod
    def view_family_link(unused1, unused2, model, unused3):
        """column formatter to open this view"""
        del unused1, unused2, unused3
        markup = ""
        if model.family:
            markup += Markup(
                " <a href='%s'>%s</a>"
                % (url_for("family.index_view", search=model.family.internal_id), model.family)
            )

        return markup


class FlowcellView(BaseView):
    """Admin view for Model.Flowcell"""

    column_default_sort = ("sequenced_at", True)
    column_editable_list = ["status"]
    column_exclude_list = ["archived_at"]
    column_filters = ["sequencer_type", "sequencer_name"]
    column_searchable_list = ["name"]


class InvoiceView(BaseView):
    """Admin view for Model.Invoice"""

    column_default_sort = ("created_at", True)
    column_editable_list = ["comment"]
    column_list = (
        "id",
        "customer",
        "created_at",
        "updated_at",
        "invoiced_at",
        "comment",
        "discount",
        "price",
    )
    column_searchable_list = ["customer.internal_id", "customer.name", "id"]

    @staticmethod
    def view_invoice_link(unused1, unused2, model, unused3):
        """column formatter to open this view"""
        del unused1, unused2, unused3
        return (
            Markup(
                "<a href='%s'>%s</a>"
                % (
                    url_for("invoice.index_view", search=model.invoice.id),
                    model.invoice.invoiced_at.date()
                    if model.invoice.invoiced_at
                    else "In progress",
                )
            )
            if model.invoice
            else ""
        )


class AnalysisView(BaseView):
    """Admin view for Model.Analysis"""

    column_default_sort = ("created_at", True)
    column_editable_list = ["is_primary"]
    column_filters = ["pipeline", "pipeline_version", "is_primary"]
    column_formatters = {"family": FamilyView.view_family_link}
    column_searchable_list = [
        "family.internal_id",
        "family.name",
    ]
    form_extra_fields = {"pipeline": SelectEnumField(enum_class=Pipeline)}


class OrganismView(BaseView):
    """Admin view for Model.Organism"""

    column_default_sort = ("created_at", True)
    column_editable_list = ["internal_id", "name", "reference_genome", "comment"]
    column_searchable_list = ["internal_id", "name", "reference_genome"]


class PanelView(BaseView):
    """Admin view for Model.Panel"""

    column_editable_list = ["current_version", "name"]
    column_filters = ["customer.internal_id"]
    column_searchable_list = ["customer.internal_id", "name", "abbrev"]
    create_modal = True
    edit_modal = True


class PoolView(BaseView):
    """Admin view for Model.Pool"""

    column_default_sort = ("created_at", True)
    column_editable_list = ["ticket"]
    column_filters = ["customer.internal_id", "application_version.application"]
    column_formatters = {"invoice": InvoiceView.view_invoice_link}
    column_searchable_list = ["name", "order", "ticket", "customer.internal_id"]


class SampleView(BaseView):
    """Admin view for Model.Sample"""

    column_exclude_list = [
        "age_at_sampling",
        "invoiced_at",
        "_phenotype_groups",
        "_phenotype_terms",
    ]
    column_default_sort = ("created_at", True)
    column_editable_list = [
        "comment",
        "downsampled_to",
        "is_tumour",
        "sequenced_at",
        "sex",
    ]
    column_filters = ["customer.internal_id", "priority", "sex", "application_version.application"]
    column_formatters = {
        "is_external": is_external_application,
        "internal_id": view_family_sample_link,
        "invoice": InvoiceView.view_invoice_link,
        "priority": view_priority,
    }
    column_searchable_list = [
        "internal_id",
        "name",
        "subject_id",
        "customer.internal_id",
        "original_ticket",
    ]
    form_excluded_columns = [
        "age_at_sampling",
        "deliveries",
        "father_links",
        "flowcells",
        "invoiced_at",
        "invoice",
        "is_external",
        "_phenotype_groups",
        "_phenotype_terms",
        "links",
        "mother_links",
    ]

    @staticmethod
    def view_sample_link(unused1, unused2, model, unused3):
        """column formatter to open this view"""
        del unused1, unused2, unused3
        return (
            Markup(
                "<a href='%s'>%s</a>"
                % (url_for("sample.index_view", search=model.sample.internal_id), model.sample)
            )
            if model.sample
            else ""
        )


class DeliveryView(BaseView):
    """Admin view for Model.Delivery"""

    column_default_sort = ("id", True)
    column_filters = ["sample.internal_id"]
    column_formatters = {"sample": SampleView.view_sample_link}
    column_searchable_list = ["sample.internal_id"]
    create_modal = True
    edit_modal = True


class FamilySampleView(BaseView):
    """Admin view for Model.FamilySample"""

    column_default_sort = ("created_at", True)
    column_editable_list = ["status"]
    column_filters = ["status"]
    column_formatters = {
        "family": FamilyView.view_family_link,
        "sample": SampleView.view_sample_link,
    }
    column_searchable_list = ["family.internal_id", "family.name", "sample.internal_id"]
    create_modal = True
    edit_modal = True


class UserView(BaseView):
    """Admin view for Model.User"""

    column_default_sort = "name"
    column_editable_list = ["order_portal_login"]
    column_filters = ["is_admin", "order_portal_login", "customers"]
    column_hide_backrefs = False
    column_list = ("name", "email", "is_admin", "order_portal_login", "customers")
    column_searchable_list = ["name", "email"]
    create_modal = True
    edit_modal = True
