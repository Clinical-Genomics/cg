# -*- coding: utf-8 -*-
import requests


class EMail(object):

    """Interface to Mailgun email API."""

    def __init__(self, config):
        super(EMail, self).__init__()
        self.MAILGUN_API_KEY = config['email']['MAILGUN_API_KEY']
        self.MAILGUN_DOMAIN_NAME = config['email']['MAILGUN_DOMAIN_NAME']

    def send(self, to_addr, subject, text):
        """Send email."""
        url = "https://api.mailgun.net/v3/{}/messages".format(self.MAILGUN_DOMAIN_NAME)
        auth = ('api', self.MAILGUN_API_KEY)
        data = {
            'from': "Mailgun User <mailgun@{}>".format(self.MAILGUN_DOMAIN_NAME),
            'to': to_addr,
            'subject': subject,
            'text': text,
        }
        response = requests.post(url, auth=auth, data=data)
        response.raise_for_status()
        return response

    def deliver(self, ticket_id, family_id):
        """Send delivery email to SupportSystems."""
        to_addr = 'supportsystem@clinicalgenomics.se'
        subject = "[#{}] Delivery to Scout: {}".format(ticket_id, family_id)
        text = """Hello,

        Case {} has been analyzed and uploaded to Scout.

        Your friendly Clinicl Genomics Bot
        """.format(family_id)
        self.send(to_addr, subject, text)
