from flask import Flask, redirect, url_for, Blueprint


INDEX_BLUEPRINT = Blueprint("index", __name__)


@INDEX_BLUEPRINT.route("/")
def index():
    return redirect(url_for("admin.index"))
