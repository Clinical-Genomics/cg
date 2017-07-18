# -*- coding: utf-8 -*-
import click


class UserImporter():

    def __init__(self, db, admin):
        self.db = db
        self.admin = admin

    @staticmethod
    def convert(record):
        return {
            'name': record.name,
            'email': record.email,
            'admin': record.is_admin,
            'customer': record.customers[0].customer_id if record.customers else 'cust999',
        }

    def status(self, data):
        customer_obj = self.db.customer(data['customer'])
        new_record = self.db.User(
            email=data['email'],
            name=data['name'],
            admin=data['admin'],
        )
        new_record.customer = customer_obj
        return new_record

    def records(self):
        query = self.admin.User
        count = query.count()
        with click.progressbar(query, length=count, label='users') as progressbar:
            for admin_record in progressbar:
                data = self.convert(admin_record)
                if not self.db.user(data['email']):
                    new_record = self.status(data)
                    self.db.add(new_record)
        self.db.commit()
