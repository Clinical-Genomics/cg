from flask import request, redirect, session, Blueprint

from cg.server.ext import auth_service



AUTH_BLUEPRINT = Blueprint('auth', __name__, url_prefix='/auth')

@AUTH_BLUEPRINT.route('/login')
def login():
    """Redirect the user to the auth service login page."""
    auth_url = auth_service.get_auth_url()
    return redirect(auth_url)

@AUTH_BLUEPRINT.route('/callback')
def callback():
    code = request.args.get('code')
    if code:
        token = auth_service.get_token(code)
        session['token'] = token
        userinfo = auth_service.get_user_info(token)
        session['userinfo'] = userinfo
        return redirect('/')
    return 'Authentication failed', 401

@AUTH_BLUEPRINT.route('/logout')
def logout():
    """Logout the user from the auth service."""
    token = session.get('token')
    if token:
        auth_service.logout_user(token)
    session.clear()
    return redirect('/')