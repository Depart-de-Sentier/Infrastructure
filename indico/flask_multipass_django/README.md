flask_multipass_django
======================

Authentication/identity providers for [`flask-multipass`][flask_multipass] using
an external data base created by a [Django][django] application.

Installation
------------

Simply install the package via `pip`.

    $ pip install flask_multipass_django

The providers are automatically registers in `flask-multipass` using [entry
points][entry_points].

**Warning**: registration via entry points does not work correctly if the
package is installed using `pip`'s "editable" mode (`-e` / `--editable`).

Configuration
-------------

Configuration is done as for any other [local provider][local_provider]:

    MULTIPASS_AUTH_PROVIDERS = {"django": {"type": "django"}}
    MULTIPASS_IDENTITY_PROVIDERS = {"django": {"type": "django"}}
    MULTIPASS_PROVIDER_MAP = {"django": "django"}

The authentication provider accepts the following options (which should be put
in the configuration dictionary alongside the `type` key):

- `sqlalchemy_url`: use a data base other than the one used by Indico.  A
  separate SQLAlchemy engine will be created specifically for the provider.
- `sqlalchemy_bind`: use a `flask-sqlalchemy` bind (see the
  [documentation][sqlalchemy_bind]) to connect to the data base.  Make sure
  there is a corresponding entry in `SQLALCHEMY_BINDS` in the Flask
  configuration.
- `user_table`: use a different table name than the default (`user`).
- `password_hashers`: use a different set of password hashers when verifying the
  password.  This should match the `PASSWORD_HASHERS` setting used by the Django
  application which generated the user data base (see the [Django
  documentation][password_hashers]).

Indico
------

The following configuration can be used to activate these providers in Indico
(where `provider_name` is an arbitrary string which will be displayed in the
log-in page):

    AUTH_PROVIDERS = {
        "provider_name": {
            "type": "django",
            "sqlalchemy_url": "…",
        },
    }
    IDENTITY_PROVIDERS = {
        "provider_name": {
            "type": "django",
            "trusted_email": True,
            "synced_fields": ["email", "first_name", "last_name"],
        },
    }
    PROVIDER_MAP = {"provider_name": "provider_name"}

`sqlalchemy_url` has to be used since there is no way to configure SQLAlchemy
binds.  `trusted_email` and `synced_fields` are used to automatically accept the
emails in the data base without going through email verification and to
synchronize all user data automatically (see the [reference][indico_auth] for
more information).

[django]: https://www.djangoproject.com
[entry_points]: https://setuptools.pypa.io/en/latest/userguide/entry_point.html
[flask_multipass]: https://github.com/indico/flask-multipass.git
[indico_auth]: https://docs.getindico.io/en/latest/config/auth/#identity-providers
[local_provider]: https://flask-multipass.readthedocs.io/en/latest/quickstart/#local-providers
[password_hashers]: https://docs.djangoproject.com/en/5.2/topics/auth/passwords/#how-django-stores-passwords
[sqlalchemy_bind]: https://flask-sqlalchemy.readthedocs.io/en/stable/binds/
