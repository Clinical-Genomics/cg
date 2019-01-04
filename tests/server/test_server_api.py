"""Tests for routes in api.py"""

from flask import url_for


def test_root(client):
    # GIVEN the api is callable

    # WHEN calling the applications route
    response = client.get('api')

    # THEN all should be fine
    assert response.status_code == 200


def test_analyses(client):
    # GIVEN the api is callable

    # WHEN calling the analyses route

    # THEN it should be hidden behind authorization
    assert client.get('/api/v1/analyses').status_code == 403


def test_applications(client):
    # GIVEN the api is callable

    # WHEN calling the applications route
    response = client.get(url_for('/api/v1/applications'))

    # THEN all should be fine
    assert response.status_code == 200
