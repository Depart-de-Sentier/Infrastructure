from django.conf import settings
from django.contrib.auth.hashers import check_password

import sqlalchemy
from sqlalchemy.orm import declarative_base

from flask import current_app
from flask_multipass import (
    AuthenticationFailed,
    AuthInfo,
    AuthProvider,
    IdentityInfo,
    IdentityProvider,
)
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField
from wtforms.validators import DataRequired

try:
    from typing import override
except ImportError:

    def override(f):
        return f


class AuthProvider(AuthProvider):
    """Authentication provider which uses an existing Django data base."""

    class Form(FlaskForm):
        username = StringField("Username", [DataRequired()])
        password = PasswordField("Password", [DataRequired()])

    def __init__(self, multipass, name, settings):
        super().__init__(multipass, name, settings)
        self.engine, self.User = self._init_db(settings)
        self._configure(settings.get("password_hashers"))

    def _init_db(self, settings):
        engine = db = None
        sqlalchemy_url = settings.get("sqlalchemy_url")
        if sqlalchemy_url is None:
            db = current_app.extensions["sqlalchemy"]
        else:
            engine = sqlalchemy.create_engine(sqlalchemy_url)
        return engine, self._create_user_model(
            db,
            settings.get("user_table"),
            settings.get("sqlalchemy_bind"),
        )

    @staticmethod
    def _create_user_model(db, table_name=None, bind_key=None):
        """Creates model for the user table for a given SQLAlchemy instance."""
        table_name = table_name if table_name is not None else "user"
        if db is None:
            db, base = sqlalchemy, declarative_base()
        else:
            base = db.Model

        class DjangoUser(base):
            __tablename__ = table_name
            if bind_key is not None:
                __bind_key__ = bind_key
            id = db.Column(db.Integer, primary_key=True)
            username = db.Column(db.String)
            password = db.Column(db.String)
            email = db.Column(db.String)
            first_name = db.Column(db.String)
            last_name = db.Column(db.String)

        return DjangoUser

    @staticmethod
    def _configure(hashers):
        d = {}
        if hashers is not None:
            d["PASSWORD_HASHERS"] = hashers
        settings.configure(**d)

    def get_user(self, username):
        q = self.User.username == username
        if self.engine is None:
            return self.User.query.filter(q).one_or_none()
        with self.engine.begin() as session:
            stmt = sqlalchemy.select(self.User).filter(q)
            return session.execute(stmt).one_or_none()

    @override
    def login_form(self):
        return self.Form()

    @override
    def process_local_login(self, data):
        user = self.get_user(data["username"])
        if user is None or not check_password(data["password"], user.password):
            raise AuthenticationFailed("invalid username or password")
        return self.multipass.handle_auth_success(
            AuthInfo(
                self,
                username=user.username,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
            ),
        )


class IdentityProvider(IdentityProvider):
    """Required implementation of the identity provider, adds no extra data."""

    supports_get = False

    @override
    def get_identity_from_auth(self, auth_info):
        return IdentityInfo(self, auth_info.data["username"], **auth_info.data)
