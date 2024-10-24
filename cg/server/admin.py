"""Module for Flask-Admin views"""

from gettext import gettext

from flask import flash, redirect, request, session, url_for
from flask_admin.actions import action
from flask_admin.contrib.sqla import ModelView
from flask_dance.contrib.google import google
from markupsafe import Markup
from sqlalchemy import inspect
from wtforms.form import Form

from cg.constants.constants import NG_UL_SUFFIX, CaseActions, DataDelivery, Workflow
from cg.models.orders.constants import OrderType
from cg.server.ext import applications_service, db, sample_service
from cg.server.utils import MultiCheckboxField
from cg.store.models import Application
from cg.utils.flask.enum import SelectEnumField


class BaseView(ModelView):
    """Base for the specific views."""

    def is_accessible(self):
        user = db.get_user_by_email(email=session.get("user_email"))
        return bool(google.authorized and user and user.is_admin)

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        return redirect(url_for("google.login", next=request.url))


def view_priority(unused1, unused2, model, unused3):
    """column formatter for priority"""
    del unused1, unused2, unused3
    return Markup("%s" % model.priority.name) if model else ""


def view_flow_cell_internal_id(unused1, unused2, model, unused3):
    """column formatter for priority"""
    del unused1, unused2, unused3
    return Markup("%s" % model.device.internal_id)


def view_flow_cell_model(unused1, unused2, model, unused3):
    """column formatter for priority"""
    del unused1, unused2, unused3
    return Markup("%s" % model.device.model)


def view_smrt_cell_model(unused1, unused2, model, unused3):
    del unused1, unused2, unused3
    return Markup("%s" % model.device.model)


def view_smrt_cell_internal_id(unused1, unused2, model, unused3):
    del unused1, unused2, unused3
    return Markup("%s" % model.device.internal_id)


def view_case_sample_link(unused1, unused2, model, unused3):
    """column formatter to open the case-sample view"""

    del unused1, unused2, unused3

    return Markup(
        "<a href='%s'>%s</a>"
        % (url_for("casesample.index_view", search=model.internal_id), model.internal_id)
    )


def is_external_application(unused1, unused2, model, unused3):
    """column formatter to open this view"""
    del unused1, unused2, unused3
    return model.application_version.application.is_external if model.application_version else ""


def view_order_types(unused1, unused2, model, unused3):
    del unused1, unused2, unused3
    order_type_list = "<br>".join([order_type.order_type for order_type in model.order_types])
    return (
        Markup(f'<div style="display: inline-block; min-width: 200px;">{order_type_list}</div>')
        if model.order_types
        else ""
    )


def view_sample_concentration_minimum(unused1, unused2, model, unused3):
    """Column formatter to append unit"""
    del unused1, unused2, unused3
    return (
        str(model.sample_concentration_minimum) + NG_UL_SUFFIX
        if model.sample_concentration_minimum
        else None
    )


def view_sample_concentration_maximum(unused1, unused2, model, unused3):
    """Column formatter to append unit"""
    del unused1, unused2, unused3
    return (
        str(model.sample_concentration_maximum) + NG_UL_SUFFIX
        if model.sample_concentration_maximum
        else None
    )


def view_sample_concentration_minimum_cfdna(unused1, unused2, model, unused3):
    """Column formatter to append unit"""
    del unused1, unused2, unused3
    return (
        str(model.sample_concentration_minimum_cfdna) + NG_UL_SUFFIX
        if model.sample_concentration_minimum_cfdna
        else None
    )


def view_sample_concentration_maximum_cfdna(unused1, unused2, model, unused3):
    """Column formatter to append unit"""
    del unused1, unused2, unused3
    return (
        str(model.sample_concentration_maximum_cfdna) + NG_UL_SUFFIX
        if model.sample_concentration_maximum_cfdna
        else None
    )


class ApplicationView(BaseView):
    """Admin view for Model.Application"""

    column_list = list(inspect(Application).columns) + ["order_types"]

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
        "sample_concentration_minimum",
        "sample_concentration_maximum",
        "sample_concentration_minimum_cfdna",
        "sample_concentration_maximum_cfdna",
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
    column_formatters = {
        "order_types": view_order_types,
        "sample_concentration_minimum": view_sample_concentration_minimum,
        "sample_concentration_maximum": view_sample_concentration_maximum,
        "sample_concentration_minimum_cfdna": view_sample_concentration_minimum_cfdna,
        "sample_concentration_maximum_cfdna": view_sample_concentration_maximum_cfdna,
    }
    column_filters = ["prep_category", "is_accredited"]
    column_searchable_list = ["tag", "prep_category"]
    form_excluded_columns = ["category", "versions", "order_types"]
    form_extra_fields = {
        "suitable_order_types": MultiCheckboxField(
            "Order Types", choices=[(choice, choice.name) for choice in OrderType]
        )
    }

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

    def on_model_change(self, form: Form, model: Application, is_created: bool):
        """Override to persist entries to the OrderTypeApplication table."""
        super(ApplicationView, self).on_model_change(form=form, model=model, is_created=is_created)
        order_types: list[OrderType] = form["suitable_order_types"].data
        applications_service.update_application_order_types(
            application=model, order_types=order_types
        )

    def edit_form(self, obj=None):
        """Override to prefill the order types according to the current Application entry."""
        form = super(ApplicationView, self).edit_form(obj)

        # Pre-select the existing order types for the application
        if obj and request.method != "POST":
            form.suitable_order_types.data = [
                order_type.order_type for order_type in obj.order_types
            ]

        return form


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
    column_list = (
        "application",
        "version",
        "valid_from",
        "price_standard",
        "price_priority",
        "price_express",
        "price_clinical_trials",
        "price_research",
        "comment",
    )
    column_exclude_list = ["created_at", "updated_at"]
    column_filters = ["version", "application.tag"]
    column_formatters = {"application": ApplicationView.view_application_link}
    column_searchable_list = ["application.tag"]
    edit_modal = True
    create_modal = True
    form_excluded_columns = ["samples", "pools", "microbial_samples"]


class ApplicationLimitationsView(BaseView):
    """Admin view for Model.ApplicationLimitations."""

    column_list = (
        "application",
        "workflow",
        "limitations",
        "comment",
        "created_at",
        "updated_at",
    )
    column_formatters = {"application": ApplicationView.view_application_link}
    column_filters = ["application.tag", "workflow"]
    column_searchable_list = ["application.tag"]
    column_editable_list = ["comment"]
    form_excluded_columns = ["created_at", "updated_at"]
    form_extra_fields = {"workflow": SelectEnumField(enum_class=Workflow)}
    create_modal = True
    edit_modal = True


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
        "lab_contact",
        "loqus_upload",
        "primary_contact",
        "priority",
        "return_samples",
        "scout_access",
    ]
    column_list = [
        "internal_id",
        "name",
        "data_archive_location",
        "comment",
        "primary_contact",
        "delivery_contact",
        "lab_contact",
        "priority",
        "project_account_KI",
        "project_account_kth",
        "return_samples",
        "scout_access",
    ]
    column_filters = ["priority", "scout_access", "data_archive_location"]
    column_searchable_list = ["internal_id", "name"]
    form_excluded_columns = ["families", "samples", "pools", "orders", "invoices"]


class CollaborationView(BaseView):
    """Admin view for Model.CustomerGroup"""

    column_editable_list = ["name"]
    column_filters = []
    column_hide_backrefs = False
    column_list = ("internal_id", "name", "customers")
    column_searchable_list = ["internal_id", "name"]


class CaseView(BaseView):
    """Admin view for Model.Case"""

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
        "internal_id": view_case_sample_link,
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
        "data_analysis": SelectEnumField(enum_class=Workflow),
        "data_delivery": SelectEnumField(enum_class=DataDelivery),
    }

    @staticmethod
    def view_case_link(unused1, unused2, model, unused3):
        """column formatter to open this view"""
        del unused1, unused2, unused3
        markup = ""
        if model.case:
            markup += Markup(
                " <a href='%s'>%s</a>"
                % (url_for("case.index_view", search=model.case.internal_id), model.case)
            )

        return markup

    @action(
        "set_hold",
        "Set action to hold",
        "Are you sure you want to set the action for selected families to hold?",
    )
    def action_set_hold(self, ids: list[str]):
        self.set_action_for_cases(action=CaseActions.HOLD, case_entry_ids=ids)

    @action(
        "set_empty",
        "Set action to Empty",
        "Are you sure you want to set the action for selected families to Empty?",
    )
    def action_set_empty(self, ids: list[str]):
        self.set_action_for_cases(action=None, case_entry_ids=ids)

    def set_action_for_cases(self, action: CaseActions | None, case_entry_ids: list[str]):
        try:
            for entry_id in case_entry_ids:
                case = db.get_case_by_entry_id(entry_id=entry_id)
                if case:
                    case.action = action

            db.session.commit()

            num_families = len(case_entry_ids)
            action_message = (
                f"Families were set to {action}."
                if num_families == 1
                else f"{num_families} families were set to {action}."
            )
            flash(action_message)

        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise

            flash(gettext(f"Failed to set case action. {str(ex)}"))


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
                    (
                        model.invoice.invoiced_at.date()
                        if model.invoice.invoiced_at
                        else "In progress"
                    ),
                )
            )
            if model.invoice
            else ""
        )


class AnalysisView(BaseView):
    """Admin view for Model.Analysis"""

    column_default_sort = ("created_at", True)
    column_editable_list = ["is_primary", "comment"]
    column_filters = ["workflow", "workflow_version", "is_primary"]
    column_formatters = {"case": CaseView.view_case_link}
    column_searchable_list = [
        "case.internal_id",
        "case.name",
    ]
    form_extra_fields = {"workflow": SelectEnumField(enum_class=Workflow)}


class IlluminaFlowCellView(BaseView):
    """Admin view for Model.IlluminaSequencingRun"""

    column_list = (
        "internal_id",
        "model",
        "sequencer_type",
        "sequencer_name",
        "data_availability",
        "has_backup",
        "total_reads",
        "total_undetermined_reads",
        "percent_undetermined_reads",
        "percent_q30",
        "mean_quality_score",
        "total_yield",
        "yield_q30",
        "cycles",
        "demultiplexing_software",
        "demultiplexing_software_version",
        "sequencing_started_at",
        "sequencing_completed_at",
        "demultiplexing_started_at",
        "demultiplexing_completed_at",
        "archived_at",
    )
    column_formatters = {"internal_id": view_flow_cell_internal_id, "model": view_flow_cell_model}
    column_default_sort = ("sequencing_completed_at", True)
    column_filters = ["sequencer_type", "sequencer_name", "data_availability"]
    column_editable_list = ["data_availability"]
    column_searchable_list = ["sequencer_type", "sequencer_name", "device.internal_id"]
    column_sortable_list = [
        ("internal_id", "device.internal_id"),
        "sequencer_type",
        "sequencer_name",
        "data_availability",
        "has_backup",
        "sequencing_started_at",
        "sequencing_completed_at",
        "demultiplexing_started_at",
        "demultiplexing_completed_at",
        "archived_at",
    ]

    @staticmethod
    def view_flow_cell_link(unused1, unused2, model, unused3):
        """column formatter to open this view"""
        del unused1, unused2, unused3
        return (
            Markup(
                "<a href='%s'>%s</a>"
                % (
                    url_for(
                        "illuminasequencingrun.index_view",
                        search=model.instrument_run.device.internal_id,
                    ),
                    model.instrument_run.device.internal_id,
                )
            )
            if model.instrument_run.device
            else ""
        )


class OrganismView(BaseView):
    """Admin view for Model.Organism"""

    column_default_sort = ("created_at", True)
    column_editable_list = ["internal_id", "name", "reference_genome", "comment"]
    column_searchable_list = ["internal_id", "name", "reference_genome"]


class OrderView(BaseView):
    """Admin view for Model.Order"""

    column_default_sort = ("order_date", True)
    column_editable_list = ["is_open"]
    column_searchable_list = ["id", "ticket_id"]
    column_display_pk = True
    create_modal = True
    edit_modal = True


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
        "_phenotype_groups",
        "_phenotype_terms",
    ]
    column_default_sort = ("created_at", True)
    column_editable_list = [
        "comment",
        "downsampled_to",
        "is_tumour",
        "last_sequenced_at",
        "sex",
    ]
    column_filters = [
        "customer.internal_id",
        "priority",
        "sex",
        "application_version.application",
        "capture_kit",
    ]
    column_formatters = {
        "is_external": is_external_application,
        "internal_id": view_case_sample_link,
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
        "invoice",
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
    def cancel_samples(self, entry_ids: list[str]) -> None:
        user_email: str | None = session.get("user_email")
        message: str = sample_service.cancel_samples(
            sample_ids=entry_ids,
            user_email=user_email,
        )
        flash(message)


class DeliveryView(BaseView):
    """Admin view for Model.Delivery"""

    column_default_sort = ("id", True)
    column_filters = ["sample.internal_id"]
    column_formatters = {"sample": SampleView.view_sample_link}
    column_searchable_list = ["sample.internal_id"]
    create_modal = True
    edit_modal = True


class CaseSampleView(BaseView):
    """Admin view for Model.caseSample"""

    column_default_sort = ("created_at", True)
    column_editable_list = ["status"]
    column_filters = ["status"]
    column_formatters = {
        "case": CaseView.view_case_link,
        "sample": SampleView.view_sample_link,
    }
    column_searchable_list = ["case.internal_id", "case.name", "sample.internal_id"]
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


class IlluminaSampleSequencingMetricsView(BaseView):
    column_list = [
        "flow_cell",
        "sample",
        "flow_cell_lane",
        "total_reads_in_lane",
        "base_passing_q30_percent",
        "base_mean_quality_score",
        "yield_",
        "yield_q30",
        "created_at",
    ]
    column_formatters = {
        "flow_cell": IlluminaFlowCellView.view_flow_cell_link,
        "sample": SampleView.view_sample_link,
    }
    column_searchable_list = ["sample.internal_id", "instrument_run.device.internal_id"]


class PacbioSmrtCellView(BaseView):
    """Admin view for Model.PacbioSMRTCell"""

    column_list = (
        "internal_id",
        "run_name",
        "movie_name",
        "well",
        "plate",
        "hifi_reads",
        "hifi_yield",
        "hifi_mean_read_length",
        "hifi_median_read_quality",
        "percent_reads_passing_q30",
        "p0_percent",
        "p1_percent",
        "p2_percent",
        "started_at",
        "completed_at",
        "barcoded_hifi_reads",
        "barcoded_hifi_reads_percentage",
        "barcoded_hifi_yield",
        "barcoded_hifi_yield_percentage",
        "barcoded_hifi_mean_read_length",
    )
    column_formatters = {"internal_id": view_smrt_cell_internal_id, "model": view_smrt_cell_model}
    column_default_sort = ("completed_at", True)
    column_searchable_list = ["device.internal_id", "run_name", "movie_name"]
    column_sortable_list = [
        ("internal_id", "device.internal_id"),
        "started_at",
        "completed_at",
    ]

    @staticmethod
    def view_smrt_cell_link(unused1, unused2, model, unused3):
        """column formatter to open this view"""
        del unused1, unused2, unused3
        return (
            Markup(
                "<a href='%s'>%s</a>"
                % (
                    url_for(
                        "pacbiosequencingrun.index_view",
                        search=model.instrument_run.device.internal_id,
                    ),
                    model.instrument_run.device.internal_id,
                )
            )
            if model.instrument_run.device
            else ""
        )


class PacbioSampleRunMetricsView(BaseView):
    column_list = [
        "smrt_cell",
        "sample",
        "hifi_reads",
        "hifi_yield",
        "hifi_mean_read_length",
        "hifi_median_read_quality",
    ]
    column_formatters = {
        "smrt_cell": PacbioSmrtCellView.view_smrt_cell_link,
        "sample": SampleView.view_sample_link,
    }
    column_searchable_list = ["sample.internal_id", "instrument_run.device.internal_id"]
