from functools import wraps
from flask import flash, redirect, url_for
from keycloak import KeycloakAuthenticationError, KeycloakConnectionError, KeycloakGetError
from pydantic import ValidationError

from cg.services.authentication.exc import TokenIntrospectionError, UserNotFoundError, UserRoleError


def handle_auth_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        """Catch all authentication related errors and provide a sensible error message.
        Redirects the user to the auth.logout endpoint and clears the session.
        """
        try:
            return func(*args, **kwargs)

        except KeycloakConnectionError as error:
            flash(f"Cannot establish connection with Keycloak. Contact sys-dev: {error}")
            # If no connection to keycloak can be established return to admin view
            return redirect(url_for("admin.index"))

        except KeycloakGetError as error:
            flash(f"Wrong information send to Keycloak. Contact sys-dev: {error}")
            # If no connection to keycloak can be established return to admin view
            return redirect(url_for("admin.index"))
        
        except TokenIntrospectionError as error:
            flash(f"Cannot parse token introspection. Contact sys-dev. If realm_access is missing the user has no assigned roles! Reason: {error}")
            return redirect(url_for("admin.index"))

        except (KeycloakAuthenticationError, UserRoleError) as error:
            flash(f"Unauthorised: {error}")
            return redirect(url_for("admin.index"))

        except UserNotFoundError as error:
            flash(f"Forbidden access: {error}")
            return redirect(url_for("admin.index"))

        except ValidationError as error:
            flash(f"Parsing of authentication models failed. Contact sys-dev: {error}")
            return redirect(url_for("admin.index"))

        except Exception as error:
            flash(f"An unexpected error occured. Contact sys-dev: {error}")
            return redirect(url_for("admin.index"))
    return wrapper
