# -*- coding: utf-8 -*-


class MutationsHandler:

    def add_user(self, email, name):
        """Add user."""
        new_user = self.User.save(dict(email=email, name=name))
        return new_user

    def add_customer(self, internal_id, name):
        """Add a new customer to the database."""
        new_customer = self.Customer.save(dict(internal_id=internal_id, name=name))
        return new_customer

    def add_sample(self, customer, internal_id, name, received_at=None):
        """Add a new sample to the database."""
        data = dict(internal_id=internal_id, name=name, customer=customer, received_at=received_at)
        new_sample = self.Sample.save(data)
        return new_sample

    def add_family(self, customer, internal_id, name, samples=None):
        """Add a new family."""
        data = dict(internal_id=internal_id, name=name, customer=customer)
        if samples:
            data['samples'] = samples
        new_family = self.Family.save(data)
        return new_family

    def add_flowcell(self, name, samples=None):
        """Add a new flowcell."""
        data = dict(name=name)
        if samples:
            data['samples'] = samples
        new_flowcell = self.Flowcell.save(data)
        return new_flowcell

    def add_flowcell_sample(self, flowcell, sample, reads):
        """Add demux results for a sample on a flowcell."""
        data = dict(flowcell=flowcell, sample=sample, reads=reads)
        new_flowcell_sample = self.FlowcellSample.save(data)
        return new_flowcell_sample

    def add_analysis(self, family, pipeline):
        """Add a new analysis."""
        data = dict(pipeline=pipeline, family=family)
        new_model = self.Analysis.save(data)
        return new_model

    def finish_analysis(self, analysis, pipeline_version, analyzed_at):
        """Finish an analysis."""
        analysis.pipeline_version = pipeline_version
        analysis.analyzed_at = analyzed_at
        self.Analysis.save(analysis)
