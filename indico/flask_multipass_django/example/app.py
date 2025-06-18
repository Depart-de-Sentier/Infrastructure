from flask import Flask, current_app, g, render_template, session
from flask_multipass import Multipass
from flask_sqlalchemy import SQLAlchemy

app = Flask("test")
app.config.from_pyfile("example.cfg")
db = SQLAlchemy()
multipass = Multipass()


@multipass.identity_handler
def identity_handler(identity_info):
    session["user"] = {"name": identity_info.identifier}


@app.before_request
def load_user_from_session():
    data = session.get("user")
    if data is None:
        return
    provider = current_app.extensions["multipass"].auth_providers["django"]
    g.user = provider.get_user(data["name"])


@app.route("/")
def index():
    return render_template("index.html")


db.init_app(app)
multipass.init_app(app)
