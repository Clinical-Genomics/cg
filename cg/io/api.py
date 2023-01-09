"""Module to create API requests."""
import requests
from requests import Response


def put(url: str, headers: dict, json: dict) -> Response:
    """Create PUT request."""
    return requests.put(url=url, headers=headers, json=json)


def post(url: str, headers: dict, json: dict) -> Response:
    """Create POST request."""
    return requests.post(url=url, headers=headers, json=json)


def delete(url: str, headers: dict, json: dict) -> Response:
    """Create DELETE request."""
    return requests.delete(url=url, headers=headers, json=json)


def get(url: str, headers: dict, json: dict) -> Response:
    """Create GET request."""
    return requests.get(url=url, headers=headers, json=json)


def patch(url: str, headers: dict, json: dict) -> Response:
    """Create PATCH request."""
    return requests.patch(url=url, headers=headers, json=json)
