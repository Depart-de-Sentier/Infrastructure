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

After the database container has started, initialise the schema:

    # podman exec compose_uwsgi_1 indico db prepare
    # podman exec compose_uwsgi_1 indico db --all-plugins upgrade

(The official postgres image already creates the role and database from
`POSTGRES_USER` / `POSTGRES_DB`; the `unaccent` and `pg_trgm` extensions are
installed by `postgresql/indico.sh` on first init. `indico db --all-plugins
upgrade` applies migrations for every enabled plugin in `indico.conf`.)

Start the containers using `podman compose`:

    # podman compose up

To verify a specific plugin is active (Indico 3.x has no `plugin list`
CLI command):

    # echo 'from indico.core.plugins import plugin_engine; print({n: p.title for n, p in plugin_engine.get_active_plugins().items()})' \
        | podman exec -i compose_uwsgi_1 indico shell

Local dev (sandbox)
-------------------

This stack is designed for `podman compose` on podman 4.x+. If you are stuck
on an older podman (e.g. Ubuntu 22.04's apt podman 3.4.4) you can still run
db + redis + uwsgi for plugin smoke tests, but a few things will not work
out of the box:

* **nginx will not build.** `nginx/Containerfile` uses BuildKit
  `additional_contexts` to copy static assets out of the uwsgi image, which
  requires podman ≥ 4.1. Skip the nginx service; run uwsgi in HTTP mode
  directly (see below).
* **The `compose_default` network's CNI config is rejected.** podman-compose
  writes `cniVersion: 1.0.0` and includes the `firewall` plugin, both
  unsupported by podman 3.4.4. Patch the conflist after each `up`:

      $ python3 -c "
      import json
      p = '$HOME/.config/cni/net.d/compose_default.conflist'
      with open(p) as f: d = json.load(f)
      d['cniVersion'] = '0.4.0'
      d['plugins'] = [pl for pl in d['plugins'] if pl.get('type') != 'firewall']
      with open(p, 'w') as f: json.dump(d, f, indent=3)
      "

  Containers also land on the default `podman` network instead of
  `compose_default` due to the `--network=name:alias=` syntax (needs podman
  4.0+). Reattach them manually:

      # podman network connect --alias db    compose_default compose_db_1
      # podman network connect --alias redis compose_default compose_redis_1

* **Running uwsgi without nginx.** Replace the `podman compose up uwsgi`
  with a manual `podman run` that publishes port 8000 in HTTP mode and
  serves static assets directly via `--static-map`:

      # DB_IP=$(podman inspect compose_db_1 \
          --format '{{range $k,$v:=.NetworkSettings.Networks}}{{if eq $k "compose_default"}}{{$v.IPAddress}}{{end}}{{end}}')
      # REDIS_IP=$(podman inspect compose_redis_1 \
          --format '{{range $k,$v:=.NetworkSettings.Networks}}{{if eq $k "compose_default"}}{{$v.IPAddress}}{{end}}{{end}}')
      # podman run -d \
          --name compose_uwsgi_1 \
          --network compose_default \
          --add-host db:$DB_IP --add-host redis:$REDIS_IP \
          --env-file .env \
          --user 0:0 \
          --mount type=tmpfs,destination=/tmp/indico/log \
          --mount type=tmpfs,destination=/tmp/indico/tmp \
          -v "$(pwd)/uwsgi/indico.conf:/opt/indico/etc/indico.conf:ro" \
          -v compose_indico_cache:/tmp/indico/cache \
          -p 8000:8000 \
          --entrypoint /bin/sh \
          localhost/compose_uwsgi \
            -c "chown -R 9997 /tmp/indico/log /tmp/indico/tmp /tmp/indico/cache \
                && exec uwsgi --uid 9997 --gid 9999 --plugin python3 \
                  --http-socket :8000 \
                  --wsgi-file /opt/indico/web/indico.wsgi \
                  --virtualenv /opt/indico/.venv \
                  --processes 4 --master \
                  --buffer-size 20480 --enable-threads \
                  --static-map /dist=/opt/indico/web/static/dist \
                  --static-map /css=/opt/indico/web/static/css \
                  --static-map /images=/opt/indico/web/static/images \
                  --static-map /fonts=/opt/indico/web/static/fonts"

  `--add-host` works around the fact that the container's `/etc/resolv.conf`
  is set at creation time, so a later `network connect` does not give it the
  CNI `dnsname` resolver. `--user 0:0 ... chown ... exec uwsgi --uid` is the
  workaround for `--tmpfs uid=` not being supported on podman 3.4.4.

  Then browse `http://localhost:8000/` — the first hit redirects to
  `/bootstrap` to create the initial admin.

These workarounds are not required on podman 4.x+; install a current podman
and the plain `podman compose up` flow from above just works.

[installation]: https://docs.getindico.io/en/stable/installation/production/deb/nginx/
