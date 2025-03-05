from functools import wraps
from flask import flash, redirect, url_for
from keycloak import KeycloakAuthenticationError, KeycloakConnectionError, KeycloakGetError
from pydantic import ValidationError

def handle_auth_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeycloakGetError as error:
            flash(f"Wrong information send to Keycloak: {error}")
            return (redirect(url_for("admin.index")))
        except KeycloakConnectionError as error:
            flash(f"Cannot establish connection with Keycloak contact Sysdev: {error}")
            return (redirect(url_for("admin.index")))
        except KeycloakAuthenticationError as error:
            flash(f"Unauthorized: {error}")
            return (redirect(url_for("admin.index")))
        except ValidationError as error:
            flash(f"Parsing of authentication models failed: {error}")
            return (redirect(url_for("admin.index")))
        except Exception as error:
            flash(f"An unexpected error occured: {error}")
            return (redirect(url_for("admin.index")))

    return wrapper