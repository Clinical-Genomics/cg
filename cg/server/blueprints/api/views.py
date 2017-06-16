# -*- coding: utf-8 -*-
from flask import abort, Blueprint
from flask_restful import Api, Resource
from webargs import fields
from webargs.flaskparser import use_args

from cg.store import models
from cg.server.ext import db

blueprint = Blueprint('api', __name__, url_prefix='/api/v1')
api = Api(blueprint)

pagination_args = dict(
    page=fields.Int(missing=1),
    per_page=fields.Int(missing=30),
)
user_args = dict(
    name=fields.Str(required=True),
    email=fields.Str(required=True),
)
user_filter_args = dict(
    email=fields.Str(),
)
sample_filter_args = {**pagination_args, **dict(
    sequence=fields.Bool()
)}


class User(Resource):

    @staticmethod
    def get_or_abort(user_id):
        """Get a record or abort."""
        user_obj = db.User.get(user_id)
        if user_obj is None:
            abort(404, message=f"User {user_id} doesn't exist")
        return user_obj

    def get(self, user_id):
        """Return a user."""
        user_obj = self.get_or_abort(user_id)
        return user_obj.to_dict()


class UserList(Resource):

    @use_args(user_filter_args)
    def get(self, args):
        query = db.User
        if args.get('email'):
            query = query.filter_by(email=args['email'])
        return dict(users=[user_obj.to_dict() for user_obj in query])

    @use_args(user_args)
    def post(self, args):
        """Create a new user in the system."""
        new_user = db.add_user(email=args['email'], name=args['name'])
        return new_user.to_dict(), 201


class Sample(Resource):

    def get(self, sample_id):
        """Show a sample."""
        sample_obj = db.Sample.get(sample_id)
        families_data = [family_obj.to_dict() for family_obj in sample_obj.families]
        total_reads = 0
        flowcells_data = []
        for fc_obj in sample_obj.flowcells:
            fc_data = fc_obj.to_dict()
            total_reads += fc_data['reads']
            flowcells_data.append(fc_data)
        sample_data = sample_obj.to_dict()
        sample_data['families'] = families_data
        sample_data['flowcells'] = flowcells_data
        sample_data['total_reads'] = total_reads
        return sample_data


class SampleList(Resource):

    @use_args(sample_filter_args)
    def get(self, args):
        """Show a list of samples."""
        query = db.Sample.order_by(models.Sample.received_at.desc())
        if args.get('sequence'):
            query = query.filter(models.Sample.sequenced_at != None)

        # pagination
        offset = (args['page'] - 1) * args['per_page']
        limit = offset + args['per_page']
        query = query.offset(offset).limit(limit)

        return [sample_obj.to_dict() for sample_obj in query]


class Application(Resource):

    def get(self, app_id):
        """Return all applications."""
        application_obj = db.AdminApplication.get(app_id)
        return application_obj.to_dict()


class ApplicationList(Resource):

    def get(self):
        """Return all applications."""
        query = db.AdminApplication
        return dict(applications=[application.to_dict() for application in query])


api.add_resource(User, '/users/<int:user_id>')
api.add_resource(UserList, '/users')
api.add_resource(Sample, '/samples/<int:sample_id>')
api.add_resource(SampleList, '/samples')
api.add_resource(Application, '/applications/<int:app_id>')
api.add_resource(ApplicationList, '/applications')
