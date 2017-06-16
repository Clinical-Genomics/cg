# -*- coding: utf-8 -*-
from flask import abort, Blueprint, jsonify, request
import jsonschema

from cg.schema import PROJECT_SCHEMAS

blueprint = Blueprint('public', __name__)


@blueprint.route('/')
def index():
    """Public index page."""
    return """<h1>Welcome to Clinical Genomics!</h1>
              Go to <a href="/info">/info</a> for more information!"""


@blueprint.route('/info')
def api_info():
    """Display general API info."""
    return jsonify(**dict(
        name='Clinical Genomics API',
        version='1',
        api_spec=dict(
            help='View API spec for submitting projects using: /info/<project_type>',
            project_types=list(PROJECT_SCHEMAS),
        )
    ))


@blueprint.route('/info/<project_type>')
def api_spec(project_type):
    """Display API spec for project types."""
    project_schema = PROJECT_SCHEMAS.get(project_type)
    if project_schema is None:
        return abort(404, message=f"Project type '{project_type}' not found")
    return jsonify(**project_schema)


@blueprint.route('/api/v1/projects', methods=['POST'])
def projects():
    """Submit a new project of samples to be sequenced and/or analyzed."""
    project_data = request.json
    project_type = request.args.get('type')
    project_schema = PROJECT_SCHEMAS.get(project_type)
    if project_schema is None:
        return abort(404, message=f"unknown project type: {project_type}")
    jsonschema.validate(project_data, project_schema)
    return jsonify(**project_data)
    # lp = LimsProject(lims_api)
    # lims_project = lp.submit(project_data)
