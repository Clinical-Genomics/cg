# -*- coding: utf-8 -*-
import datetime

from sqlalchemy import types, Column, orm, Table, ForeignKey, UniqueConstraint

from .core import Base, Model


class AdminCustomer(Base, Model):

    __tablename__ = 'admin_customer'

    customer_id = Column(ForeignKey('customer.id', ondelete='CASCADE'))
    customer = orm.relationship('Customer', uselist=False, backref='admin')

    agreement_date = Column(types.Date)
    agreement_registration = Column(types.String(32))
    scout_access = Column(types.Boolean)
    primary_contact_id = Column(ForeignKey('user.id'))
    delivery_contact_id = Column(ForeignKey('user.id'))
    uppmax_account = Column(types.String(32))
    project_account_ki = Column(types.String(32))
    project_account_kth = Column(types.String(32))
    organisation_number = Column(types.String(32))
    invoice_address = Column(types.Text)
    invoice_reference = Column(types.String(32))
    invoice_contact_id = Column(ForeignKey('user.id'))

    primary_contact = orm.relationship('User', foreign_keys=[primary_contact_id])
    delivery_contact = orm.relationship('User', foreign_keys=[delivery_contact_id])
    invoice_contact = orm.relationship('User', foreign_keys=[invoice_contact_id])


class AdminMethod(Base, Model):

    __tablename__ = 'admin_method'
    __table_args__ = (UniqueConstraint('document', 'document_version',
                                       name='_document_version_uc'),)

    name = Column(types.String(128), nullable=False)
    document = Column(types.Integer, nullable=False)
    document_version = Column(types.Integer, nullable=False)
    description = Column(types.Text, nullable=False)
    limitations = Column(types.Text)

    last_updated = Column(types.DateTime, onupdate=datetime.datetime.now)
    comment = Column(types.Text)

    @property
    def full_name(self):
        """Return the full name with number and version."""
        return "{this.document}:{this.document_version} {this.name}".format(this=self)


class AdminApplication(Base, Model):

    __tablename__ = 'admin_application'

    code = Column(types.String(64), nullable=False, unique=True)
    description = Column(types.Text, nullable=False)
    detailed_description = Column(types.Text)
    limitations = Column(types.Text)
    library_prep = Column(types.Text)
    automated_library_prep = Column(types.Text)
    sample_amount = Column(types.Text)
    sequencing_depth = Column(types.Text)
    misc = Column(types.Text)
    delivery = Column(types.Text)
    is_accredited = Column(types.Boolean, default=False)
    response_time = Column(types.Integer)
