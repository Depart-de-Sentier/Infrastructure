indico
======

Based on the [official documentation][installation].

Create a `.env` file:

    $ cat > .env <<'EOF'
    POSTGRES_PASSWORD=…
    POSTGRES_USER=indico
    POSTGRES_DB=indico
    INDICO_CONFIG=/opt/indico/etc/indico.conf
    EOF

Build the container images:

    # podman compose build

These steps currently have to be executed manually:

    # podman exec compose_db_1 createuser indico
    # podman exec compose_db_1 createdb -O indico indico
    # podman exec compose_db_1 \
        psql indico -c 'CREATE EXTENSION unaccent; CREATE EXTENSION pg_trgm;'
    # podman exec compose_uwsgi_1 indico db prepare

Start the containers using `podman compose`:

    # podman compose up

[installation]: https://docs.getindico.io/en/stable/installation/production/deb/nginx/
