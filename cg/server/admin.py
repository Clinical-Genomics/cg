"""Module for Flask-Admin views"""
from datetime import datetime
from gettext import ngettext, gettext
from typing import List, Union

from cgmodels.cg.constants import Pipeline
from flask import redirect, request, session, url_for, flash
from flask_admin.actions import action
from flask_admin.contrib.sqla import ModelView
from flask_dance.contrib.google import google
from markupsafe import Markup
from sqlalchemy.orm import Query

from cg.constants.constants import DataDelivery, CaseActions
from cg.server.ext import db
from cg.store.models import Family, Sample
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
        "tickets",
    ]
    column_formatters = {
        "internal_id": view_family_sample_link,
        "priority": view_priority,
    }
    column_searchable_list = [
        "internal_id",
        "name",
        "customer.internal_id",
        "tickets",
    ]
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

    @action(
        "set_hold",
        "Set action to hold",
        "Are you sure you want to set the action for selected families to hold?",
    )
    def action_set_hold(self, ids: List[str]):
        self.set_action_for_batch(action=CaseActions.HOLD, entry_ids=ids)

    @action(
        "set_empty",
        "Set action to Empty",
        "Are you sure you want to set the action for selected families to Empty?",
    )
    def action_set_empty(self, ids: List[str]):
        self.set_action_for_batch(action=None, entry_ids=ids)

    def set_action_for_batch(self, action: Union[CaseActions, None], entry_ids: List[str]):
        try:
            query: Query = db.Family.query.filter(db.Family.id.in_(entry_ids))
            family: Family
            for family in query.all():
                family.action = action

            flash(
                ngettext(
                    f"Families were set to {action}.",
                    f"{len(entry_ids)} families were set to {action}.",
                    len(entry_ids),
                )
            )
            db.commit()
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise

            flash(gettext(f"Failed to set family action. {str(ex)}"))


class FlowcellView(BaseView):
    """Admin view for Model.Flowcell"""

    column_default_sort = ("sequenced_at", True)
    column_editable_list = ["status"]
    column_exclude_list = ["archived_at"]
    column_filters = ["sequencer_type", "sequencer_name", "status"]
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

    @action(
        "cancel_samples",
        "Cancel samples",
        "Are you sure you want to cancel the selected samples?",
    )
    def cancel_samples(self, entry_ids: List[str]) -> None:
        """
        Action for cancelling samples:
            - Comments each sample being cancelled with date and user.
            - Deletes any relationship between the cancelled samples and cases.
            - Deletes any cases that only contain samples being cancelled.
        """
        all_associated_case_ids: set = set()

        for entry_id in entry_ids:
            sample: Sample = db.get_sample_by_id(entry_id=int(entry_id))

            sample_case_ids: List[str] = [
                case_sample.family.internal_id for case_sample in sample.links
            ]
            all_associated_case_ids.update(sample_case_ids)

            db.delete_relationships_sample(sample=sample)
            self.write_cancel_comment(sample=sample)

        case_ids: List[str] = list(all_associated_case_ids)
        db.delete_cases_without_samples(case_ids=case_ids)
        cases_with_remaining_samples: List[str] = db.filter_cases_with_samples(case_ids=case_ids)

        self.display_cancel_confirmation(
            sample_entry_ids=entry_ids, remaining_cases=cases_with_remaining_samples
        )

    def write_cancel_comment(self, sample: Sample) -> None:
        """Add comment to sample with date and user cancelling the sample."""
        username: str = db.user(session.get("user_email")).name
        date: str = datetime.now().strftime("%Y-%m-%d")
        comment: str = f"Cancelled {date} by {username}"

        db.add_sample_comment(sample=sample, comment=comment)

    def display_cancel_confirmation(
        self, sample_entry_ids: List[str], remaining_cases: List[str]
    ) -> None:
        """Show a summary of the cancelled samples and any cases in which other samples were present."""
        samples: str = "sample" if len(sample_entry_ids) == 1 else "samples"
        cases: str = "case" if len(remaining_cases) == 1 else "cases"

        message: str = f"Cancelled {len(sample_entry_ids)} {samples}. "
        case_message: str = ""

        for case_id in remaining_cases:
            case_message = f"{case_message} {case_id},"

        case_message = case_message.strip(",")

        if remaining_cases:
            message += (
                f"Found {len(remaining_cases)} {cases} with additional samples: {case_message}."
            )
        else:
            message += "No case contained additional samples."

        flash(message=message)


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
