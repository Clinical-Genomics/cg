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
        
        except KeycloakGetError as error:
            flash(f"Wrong information send to Keycloak: {error}")
            return (redirect(url_for("auth.logout")))
        
        except KeycloakConnectionError as error:
            flash(f"Cannot establish connection with Keycloak contact Sysdev: {error}")
            return (redirect(url_for("auth.logout")))
        
        except TokenIntrospectionError as error:
            flash(f"Cannot parse token introspection. Does the user have roles?")
            redirect(url_for("auth.logout"))
        
        except (KeycloakAuthenticationError, UserRoleError) as error:
            flash(f"Unauthorized: {error}")
            return (redirect(url_for("auth.logout")))
        
        except UserNotFoundError as error:
            flash(f"Forbidden access: {error}")
            return
        
        except ValidationError as error:
            flash(f"Parsing of authentication models failed: {error}")
            return (redirect(url_for("auth.logout")))
        
        except Exception as error:
            flash(f"An unexpected error occured: {error}")
            return (redirect(url_for("auth.logout")))

    return wrapper