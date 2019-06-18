# -*- coding: utf-8 -*-
from flask import redirect, url_for, request, session
from flask_admin.contrib.sqla import ModelView
from flask_dance.contrib.google import google
from markupsafe import Markup

from cg.server.ext import db


class BaseView(ModelView):
    def is_accessible(self):
        user_obj = db.user(session.get('user_email'))
        return True if (google.authorized and user_obj and user_obj.is_admin) else False

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        return redirect(url_for('google.login', next=request.url))


class ApplicationView(BaseView):
    """Admin view for Model.Application"""
    column_exclude_list = [
        'minimum_order',
        'sample_amount',
        'sample_volume',
        'details',
        'limitations',
        'percent_kth',
        'created_at',
        'updated_at',
        'category',
    ]
    column_searchable_list = ['tag', 'prep_category']
    column_filters = ['prep_category', 'is_accredited']
    column_editable_list = ['description', 'is_accredited', 'target_reads', 'comment',
                            'prep_category', 'sequencing_depth', 'is_external']
    form_excluded_columns = ['category']

    @staticmethod
    def view_application_link(unused1, unused2, model, unused3):
        """column formatter to open this view"""
        del unused1, unused2, unused3
        return Markup(
            u"<a href='%s'>%s</a>" % (
                url_for('application.index_view', search=model.application.tag),
                model.application.tag
            )
        ) if model.application else u""


class ApplicationVersionView(BaseView):
    """Admin view for Model.ApplicationVersion"""
    column_exclude_list = [
        'created_at',
        'updated_at',
    ]
    column_searchable_list = ['application.tag']
    column_filters = ['version', 'application.tag']
    column_editable_list = ['valid_from']
    edit_modal = True

    column_formatters = {
        'application': ApplicationView.view_application_link
    }
    

class CustomerView(BaseView):
    """Admin view for Model.Customer"""
    column_exclude_list = [
        'agreement_date',
        'organisation_number',
        'invoice_address'
    ]
    column_searchable_list = ['internal_id', 'name']
    column_filters = ['priority', 'scout_access']
    column_editable_list = ['name', 'scout_access', 'loqus_upload', 'return_samples', 'priority',
                            'customer_group']
    

class CustomerGroupView(BaseView):
    """Admin view for Model.CustomerGroup"""

    column_exclude_list = [

    ]
    column_searchable_list = ['internal_id', 'name']
    column_filters = []
    column_editable_list = ['name']


class FamilyView(BaseView):
    """Admin view for Model.Family"""

    column_exclude_list = ['created_at']
    column_searchable_list = ['internal_id', 'name', 'customer.internal_id']
    column_filters = ['customer.internal_id', 'priority', 'action']
    column_editable_list = ['action']

    @staticmethod
    def view_family_link(unused1, unused2, model, unused3):
        """column formatter to open this view"""
        del unused1, unused2, unused3
        return Markup(
            u"<a href='%s'>%s</a>" % (
                url_for('family.index_view', search=model.family.internal_id),
                model.family
            )
        ) if model.family else u""


class AnalysisView(BaseView):
    """Admin view for Model.Analysis"""

    column_searchable_list = ['family.internal_id', 'family.name']
    column_filters = ['pipeline', 'pipeline_version', 'is_primary']
    column_editable_list = ['is_primary']

    column_formatters = {
        'family': FamilyView.view_family_link,
    }


class FlowcellView(BaseView):
    """Admin view for Model.Flowcell"""

    column_searchable_list = ['name']
    column_filters = ['sequencer_type', 'sequencer_name']
    column_editable_list = ['status']


class InvoiceView(BaseView):
    """Admin view for Model.Invoice"""

    column_searchable_list = ['customer_id', 'id']
    column_list = (
        'id', 'customer_id', 'created_at', 'updated_at', 'invoiced_at', 'comment', 'discount',
        'price')

    @staticmethod
    def view_invoice_link(unused1, unused2, model, unused3):
        """column formatter to open this view"""
        del unused1, unused2, unused3
        return Markup(
            u"<a href='%s'>%s</a>" % (
                url_for('invoice.index_view', search=model.invoice.id),
                model.invoice.id
            )
        ) if model.invoice else u""


class MicrobialOrderView(BaseView):
    """Admin view for Model.MicrobialOrder"""

    column_searchable_list = ['internal_id', 'name', 'ticket_number']
    column_editable_list = ['ticket_number', 'comment']
    column_filters = ['customer.internal_id']


class MicrobialSampleView(BaseView):
    """Admin view for Model.MicrobialSample"""

    column_searchable_list = ['internal_id', 'name', 'microbial_order.ticket_number']
    column_editable_list = ['reads', 'comment', 'reference_genome']
    column_filters = ['microbial_order', 'microbial_order.customer']
    column_default_sort = ('created_at', True)

    column_formatters = {
        'invoice': InvoiceView.view_invoice_link,
    }


class OrganismView(BaseView):
    """Admin view for Model.Organism"""

    column_searchable_list = ['internal_id', 'name', 'reference_genome']
    column_editable_list = ['internal_id', 'name', 'reference_genome', 'comment']
    column_default_sort = ('created_at', True)


class PanelView(BaseView):
    """Admin view for Model.Panel"""

    column_searchable_list = ['customer.internal_id', 'name', 'abbrev']
    column_filters = ['customer.internal_id']
    column_editable_list = ['current_version', 'name']
    create_modal = True
    edit_modal = True


class PoolView(BaseView):
    """Admin view for Model.Pool"""

    column_searchable_list = ['name', 'order', 'ticket_number', 'customer.internal_id']
    column_filters = ['customer.internal_id', 'application_version.application']
    column_editable_list = ['sequenced_at', 'ticket_number']

    column_formatters = {
        'invoice': InvoiceView.view_invoice_link,
    }


class SampleView(BaseView):
    """Admin view for Model.Sample"""

    column_exclude_list = ['is_external']
    column_searchable_list = ['internal_id', 'name', 'ticket_number', 'customer.internal_id']
    column_filters = ['customer.internal_id', 'sex', 'application_version.application']
    column_editable_list = ['sex', 'downsampled_to', 'sequenced_at', 'ticket_number']
    form_excluded_columns = ['is_external']

    column_formatters = {
        'invoice': InvoiceView.view_invoice_link,
    }

    @staticmethod
    def view_sample_link(unused1, unused2, model, unused3):
        """column formatter to open this view"""
        del unused1, unused2, unused3
        return Markup(
            u"<a href='%s'>%s</a>" % (
                url_for('sample.index_view', search=model.sample.internal_id),
                model.sample
            )
        ) if model.sample else u""


class DeliveryView(BaseView):
    """Admin view for Model.Delivery"""

    column_searchable_list = ['sample.internal_id']
    column_filters = ['sample.internal_id']
    create_modal = True
    edit_modal = True

    column_formatters = {
        'sample': SampleView.view_sample_link
    }


class FamilySampleView(BaseView):
    """Admin view for Model.FamilySample"""

    column_searchable_list = ['family.internal_id', 'family.name', 'sample.internal_id']
    column_filters = ['status']
    column_editable_list = ['status']
    create_modal = True
    edit_modal = True

    column_formatters = {
        'family': FamilyView.view_family_link,
        'sample': SampleView.view_sample_link
    }


class UserView(BaseView):
    """Admin view for Model.User"""

    column_searchable_list = ['name', 'email', 'customer.internal_id']
    column_filters = ['customer.internal_id']
    column_editable_list = ['customer', 'is_admin']
    create_modal = True
    edit_modal = True
