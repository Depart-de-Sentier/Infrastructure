Server is on hetzner.com. Static IP is currently:

    176.9.61.115

# Create user `cmutel`

    adduser cmutel
    usermod -aG sudo cmutel

# SSH

1. Back up existing config:

    sudo cp /etc/ssh/sshd_config{,.bak}

2. Copy my keys to server

    ssh-copy-id -i .ssh/id_rsa.pub cmutel@176.9.61.115

3. Add hetzner config to local `~/.ssh/config`

    Host hetzner
    Hostname 176.9.61.115

4. Disable SSH root and password login

    sudo nano /etc/ssh/sshd_config

And change to:

    PermitRootLogin no
    PasswordAuthentication no
    ChallengeResponseAuthentication no

Restart ssh:

    sudo systemctl restart ssh

# Upgrade packages

    sudo apt update && sudo apt upgrade -y

# Profile

Copy `.profile` or similar using scp.

Install necessary packages:

    sudo apt install bash-completion

# Miniconda

    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
    bash Miniconda3-latest-Linux-x86_64.sh

We will have multiple `conda` installs; to get this conda command working, you can source this script:

```
source miniconda3/etc/profile.d/conda.sh
```

# TLJH (https://tljh.jupyter.org/)

    sudo apt install python3 python3-dev git curl
    curl -L https://tljh.jupyter.org/bootstrap.py | sudo -E python3 - --admin cmutel

## TLJH networking

Change `traefik` to only listen to localhost by editing `/opt/tljh/state/traefik.toml`:

    [entryPoints.http]
    address = "127.0.0.1:8100"

## Configuring TLJH

```
sudo tljh-config set limits.memory 16G
sudo tljh-config set limits.cpu 4
sudo tljh-config reload
```

# NGINX

```
    sudo apt update
    sudo apt-get upgrade
    sudo apt install nginx
```

Check it is running:

    systemctl status nginx

Check configuration

    nginx -c /etc/nginx/nginx.conf -t

Add nginx unit to boot
   
    sudo systemctl enable nginx

Restart command:

    sudo systemctl restart nginx

## DNS entries

`brightway.dev` is managed with the Vultr DNS. Currently I point only `hub.brightway.dev` at the Hetzner server.

## HTTPS with certbot

### Add site to nginx config

Following https://www.digitalocean.com/community/tutorials/how-to-install-nginx-on-ubuntu-20-04#step-5-%E2%80%93-setting-up-server-blocks-(recommended) add a file to
`/etc/nginx/sites-available/hub.brightway.dev` with basic http config. 

The file is at the repo https://github.com/Depart-de-Sentier/Infrastructure/blob/main/Hetzner%20server/sites-available/hub.brightway.dev. This file does not contain _yet_ the actual ssl details it's a http only configuration so that we can have a working nginx when using certbot to generate the certs. It's a template with the required configuration for the forwarding.

Add a link to the sites-enabled:

```
sudo ln -s /etc/nginx/sites-available/hub.brightway.dev /etc/nginx/sites-enabled
```

### Make sure jupyterhub, traefik and nginx systemd units start on boot

```
sudo systemctl enable jupyterhub
sudo systemctl enable traefik
sudo systemctl enable nginx
sudo systemctl daemon-reload
```

### Add certs with certbot

Follow instructions from https://www.digitalocean.com/community/tutorials/how-to-secure-nginx-with-let-s-encrypt-on-ubuntu-20-04

```
sudo apt install certbot python3-certbot-nginx
```

**There is no firewall running for the moment in the server, so "step 3" of the guide is not implemented**

```
sudo certbot --nginx -d hub.brightway.dev --agree-tos --email cmutel@gmail.com
```

Use opton _2_ to redirect all traffic to https.

### Automatic cert renewal

Make sure the renewal is automatic thanks to the systemd unit installed with certbot at the first step:

```
sudo systemctl status certbot.timer
```

Should yield something like:

```
● certbot.timer - Run certbot twice daily
     Loaded: loaded (/lib/systemd/system/certbot.timer; enabled; vendor preset: enabled)
     Active: active (waiting) since Wed 2022-04-13 05:59:59 CEST; 32min ago
    Trigger: Wed 2022-04-13 13:03:42 CEST; 6h left
   Triggers: ● certbot.service

Apr 13 05:59:59 Ubuntu-2004-focal-64-minimal systemd[1]: Started Run certbot twice daily.
```

### Troubleshooting

Can get info on current certificates with

```
sudo certbot certificates
```

The nginx config file for the hub should look more or less like follows (after being modified by certbot):

```
server {
    server_name hub.brightway.dev;
    access_log  /var/log/nginx/hub.brightway.dev.access.log;


    location / {
        proxy_pass http://localhost:8100;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
	proxy_set_header Connection "upgrade";
	proxy_set_header Upgrade $http_upgrade;

    }

    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/hub.brightway.dev/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/hub.brightway.dev/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot

}
server {
    if ($host = hub.brightway.dev) {
        return 301 https://$host$request_uri;
    } # managed by Certbot


    listen 80;
    server_name hub.brightway.dev;
    return 404; # managed by Certbot


}
```

The `upgrade` part seems to be important for the websocket.

# [pandarus_remote](https://github.com/cmutel/pandarus_remote)

## Installation

Download `micromamba` to a user environment. Create a suitable environment:

```
micromamba create -n pandarus -c conda-forge -c cmutel -c defaults pandarus_remote rq redis
```

Version 2.0 of `pandarus` requires `exactextract`, which is not making life simple (nothing is on pypi). One needs to do the following:

```console
micromamba activate pandarus
micromamba install appdirs fiona gdal geopandas geos numpy pybind11 rasterio rasterstats Rtree shapely -c conda-forge
git clone https://github.com/isciences/exactextract
cd exactextract
mkdir cmake-build-release
cd cmake-build-release
micromamba run -n pandarus cmake -DCMAKE_BUILD_TYPE=Release -DGDAL_INCLUDE_DIR=/home/cmutel/micromamba/envs/pandarus/include -DBUILD_CLI:=OFF -DBUILD_DOC:=OFF -DCMAKE_BUILD_TYPE=Release ..
make
cd ../python/
pip install --no-deps .
```

And then:

```console
cd $HOME
git clone https://github.com/cmutel/pandarus.git
pip install --no-deps .
```

## Redis

Following https://www.digitalocean.com/community/tutorials/how-to-install-and-secure-redis-on-ubuntu-20-04.

```
sudo apt install redis-server
```

Edit the config file:

```
sudo nano /etc/redis/redis.conf
```

Change `supervised no` to `supervised systemd`.

```
sudo systemctl restart redis.service
sudo systemctl status redis
```

## [RQ](https://python-rq.org/)

Set up to run under systemd by creating `/etc/systemd/system/rq-worker@.service`:

```
[Unit]
Description=RQ Worker Number %i
After=network.target

[Service]
Type=simple
User=cmutel
Group=www-data
WorkingDirectory=/home/cmutel/pr
ExecStart=/home/cmutel/.local/bin/micromamba run -n pandarus rq worker

ExecReload=/bin/kill -s HUP $MAINPID
ExecStop=/bin/kill -s TERM $MAINPID
PrivateTmp=true
Restart=always

[Install]
WantedBy=multi-user.target
```

See https://python-rq.org/patterns/systemd/.

Then enable and start:

```
sudo systemctl daemon-reload
sudo systemctl start rq-worker@{1..8}.service
sudo systemctl start rq-worker@1.service
systemctl status rq-worker@1
```

## Setting up `pandarus.brightway.dev`

Site config in `sites-available`. DNS A name added pointing to Hetzner server.

```
server {
    server_name pandarus.brightway.dev;
    access_log  /var/log/nginx/pandarus.brightway.dev.access.log;
    server_tokens        off;

    client_max_body_size 300m;

    location / {
        proxy_pass http://localhost:8281;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Connection "upgrade";
        proxy_set_header Upgrade $http_upgrade;
    }

    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/pandarus.brightway.dev/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/pandarus.brightway.dev/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
server {
    if ($host = pandarus.brightway.dev) {
        return 301 https://$host$request_uri;
    } # managed by Certbot
    server_tokens        off;

    server_name pandarus.brightway.dev;
    listen 80;
    return 404; # managed by Certbot
```

Set up file and certificate:

```
sudo chown root:root /etc/nginx/sites-available/pandarus.brightway.dev
sudo ln -s /etc/nginx/sites-available/pandarus.brightway.dev /etc/nginx/sites-enabled/
sudo certbot --nginx
```

## [Waitress WSGI server](https://docs.pylonsproject.org/projects/waitress/en/latest/)

Create a runner Python program: `run_pr.py`

```
import os
os.environ['PANDARUS_CPUS'] = "4"

from pandarus_remote import pr_app
from waitress import serve
serve(pr_app, host='127.0.0.1', port=8281)
```

Make sure it is executable.

Set up to run under systemd by creating `/etc/systemd/system/pr-worker.service`:

```
[Unit]
Description=Waitress running pandarus_remote
After=network.target

[Service]
User=cmutel
Group=www-data
WorkingDirectory=/home/cmutel/pr
ExecStart=/home/cmutel/.local/bin/micromamba run -n pandarus python /home/cmutel/pr/pr_runner.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then enable and start:

```
sudo systemctl daemon-reload
sudo systemctl enable pr-worker.service
sudo systemctl start pr-worker.service
systemctl status pr-worker
```

### Debugging PR jobs

Get into the conda environment, e.g.

```
source miniconda3/etc/profile.d/conda.sh
conda activate pandarus_remote
```

Then get the exception information (in Python shell):

```
from redis import Redis
from rq import Queue
from rq.registry import FailedJobRegistry
from rq.job import Job

redis = Redis()
queue = Queue(connection=redis)
registry = FailedJobRegistry(queue=queue)
for job_id in registry.get_job_ids():
    job = Job.fetch(job_id, connection=redis)
    print(job_id, job.exc_info)
```

## files.brightway.dev

Config file in sites-available, install as other sites above.

```
sudo ln -s /etc/nginx/sites-available/files.brightway.dev /etc/nginx/sites-enabled/
sudo certbot --nginx -d files.brightway.dev --agree-tos --email cmutel@gmail.com
```

## Automatic website deployment

### On our server

Create user `websites`. Cloned brightcon website to their home directory.

Create SSH keypair for this user:

```
ssh-keygen -t ed25519
```

Add public key to authorized_keys by copying its contents.

### On Github

In the repository you want cloned, create the file `.github/workflows/<something>.yaml`. Example content using https://github.com/appleboy/ssh-action:

```
name: Sync latest website content
on: [push]
jobs:

  synnc-website-content:
    name: Sync website content SSH
    runs-on: ubuntu-latest
    steps:
    - name: executing remote ssh command
      uses: appleboy/ssh-action@master
      with:
        host: ${{ secrets.HOST }}
        username: ${{ secrets.USERNAME }}
        key: ${{ secrets.KEY }}
        port: ${{ secrets.PORT }}
        script: cd brightcon && git pull https://github.com/Depart-de-Sentier/brightcon.git
```

In the Github web UI, add the `HOST` (176.9.61.115), `USERNAME` (`websites`), `PORT` (22), and `KEY` (private key) secrets.

## Postgres 16

Our server is running Ubuntu Jammy Jellyfish. To install Postgres 16, I did:

- Create `/etc/apt/sources.list.d/pgdg.list` and add the line:

```console
deb http://apt.postgresql.org/pub/repos/apt jammy-pgdg main
```

- Add the signing key:

```console
curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/postgresql.gpg
```

- Install the software

```console
sudo apt update
sudo apt install postgresql-16 postgresql-contrib-16
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

- Edit `/etc/postgresql/16/main/postgresql.conf` to allow for password logins on local socket connections:

```console
local   all             all                                     md5
```

(and restart the service)

## Typesense

- Get the typesense package

```console
curl -O https://dl.typesense.org/releases/28.0/typesense-server-28.0-amd64.deb
sudo dpkg -i typesense-server-28.0-amd64.deb
```

This creates a system service file at `/etc/systemd/system/typesense-server.service` and a typesense config file at `/etc/typesense/typesense-server.ini` (with the API key needed for PyST configuration). It also starts the server.

## Vocab.sentier.dev

- Login to `psql` and create the user `pyst`:

```console
CREATE USER pyst WITH CREATEDB PASSWORD <secret>
```

- Create the units database:

```console
CREATE DATABASE units_vocab_sentier_dev OWNER pyst;
```

These needs to happen separately for each database. Usually there is a separate pyst deployment per database.

### py-semantic-taxonomy

We will have multiple PyST instances running; at least one each for process, product, and unit, with more to come.

The server is running Jammy, which has Python 3.10 as default. To avoid potential conflicts we install `uv` to get a safe virtualenv.

After creating and activating a virtualenv, install pyst:

```console
uv pip install py-semantic-taxonomy
```

We will use the following ports:

* 8201: Units

Python script (`/home/cmutel/pyst/pyst_units.py`):

```python
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "py_semantic_taxonomy.app:create_app",
        host="127.0.0.1",
        port=8201,
        log_level="info",
        workers=8,
    )
```

Service file (`/etc/systemd/system/pyst-units.service`)

```console
# /etc/systemd/system/pyst-units.service
[Unit]
Description=PyST Units
After=network.target

[Service]
Type=simple
User=cmutel
WorkingDirectory=/home/cmutel
ExecStart=/home/cmutel/venvs/pyst/bin/python /home/cmutel/pyst/pyst_units.py
Restart=always
Environment=PyST_db_user="pyst"
Environment=PyST_db_pass="<secret>"
Environment=PyST_db_host="localhost"
Environment=PyST_db_port=5432
Environment=PyST_db_name="units_vocab_sentier_dev"
Environment=PyST_auth_token="<secret>"
Environment=PyST_typesense_url="http://localhost:8108"
Environment=PyST_typesense_api_key="<secret>"
Environment=PyST_typesense_embedding_model="ts/multilingual-e5-large"
Environment=PyST_typesense_prefix="units"

[Install]
WantedBy=multi-user.target
```

`PyST_typesense_api_key` comes from `/etc/typesense/typesense-server.ini`; the other secrets are in our secret store.

## Fuseki

Installation of Fuseki from Java release

Following instructions from https://github.com/NatLibFi/Skosmos/wiki/InstallTutorial.

```console
wget https://dlcdn.apache.org/jena/binaries/apache-jena-fuseki-5.4.0.tar.gz
cd /opt
sudo ln -s apache-jena-fuseki-5.4.0 fuseki
./fuseki/fuseki-server --version
```

Run as `fuseki` user:

```console
sudo adduser --system --home /opt/fuseki --no-create-home fuseki
```

Fuskei layout:

* Fuseki code (the server distribution) goes into /opt/fuseki (symlink)
* databases go under /var/lib/fuseki
* log files go under /var/log/fuseki
* configuration files go under /etc/fuseki

Get the necessary directories created with correct permissions:

```console
cd /var/lib
sudo mkdir -p fuseki/{backups,databases,system,system_files}
sudo chown -R fuseki fuseki

cd /var/log
sudo mkdir fuseki
sudo chown fuseki fuseki

cd /etc
sudo mkdir fuseki
sudo chown fuseki fuseki

cd /etc/fuseki
sudo ln -s /var/lib/fuseki/* .
sudo ln -s /var/log/fuseki logs
```

Create systemd service script `/etc/systemd/system/fuseki.service`:

```console
[Unit]
Description=Fuseki
[Service]
Environment=FUSEKI_HOME=/opt/fuseki
Environment=FUSEKI_BASE=/etc/fuseki
Environment=JVM_ARGS=-Xmx8G
User=fuseki
ExecStart=/opt/fuseki/fuseki-server
Restart=on-failure
RestartSec=15
[Install]
WantedBy=multi-user.target
```

Enable the service:

```console
sudo systemctl enable fuseki
```

Add `fuseki.d-d-s.ch` DNS entry pointing to our server address in Hostpoint.

Create Nginx site proxy `/etc/nginx/sites-available/fuseki.d-d-s.ch`:

```console
server {
    server_name fuseki.d-d-s.ch;
    access_log  /var/log/nginx/fuseki.d-d-s.ch.access.log;
    server_tokens        off;

    location / {
        proxy_pass http://localhost:3030;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Connection "upgrade";
        proxy_set_header Upgrade $http_upgrade;
    }
}
```

Enable the site:

```console
sudo ln -s /etc/nginx/sites-available/fuseki.d-d-s.ch /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

Get HTTPS certificates:

```console
sudo certbot --nginx -d fuseki.d-d-s.ch --agree-tos --email cmutel@gmail.com
```

### Load the data

First, create the main database:

```console
curl --data "dbName=skosmos&dbType=tdb2" http://localhost:3030/$/datasets
```

Installing via the web interface is possible in theory, but difficult. Easier to [install via the command line](https://github.com/NatLibFi/Skosmos/wiki/InstallTutorial#b-loading-data-using-the-command-line):

```console
sudo apt install ruby
```

The ruby `s-put` script isn't bundled with the Fuseki release, so copy the contents of https://github.com/apache/jena/blob/main/jena-cmds/src/main/ruby/s-put into a file `s-put`, and make that executable.

Then install the TTL input files into their correct graphs. For example for units:

```console
./s-put http://localhost:3030/skosmos/data https://vocab.sentier.dev/units/ qudt-sentier-dev.ttl
```

# Indico

Following instructions from https://docs.getindico.io/en/stable/installation/production/deb/nginx/

* Install some dependencies (Postgres already installed for PyST):

```console
sudo apt install -y --install-recommends postgresql-16 libpq-dev nginx libxslt1-dev libxml2-dev libffi-dev libpcre3-dev libyaml-dev libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev libncurses5-dev libncursesw5-dev xz-utils liblzma-dev uuid-dev build-essential redis-server git libpango1.0-dev libjpeg-turbo8-dev
systemctl start postgresql.service redis-server
```

* Create the Postgresql database:

```sql
CREATE USER indico WITH PASSWORD <secret>;
CREATE DATABASE indico OWNER indico;
CREATE EXTENSION unaccent; CREATE EXTENSION pg_trgm;
```

* Create indico user:

```console
sudo useradd -rm -g www-data -d /opt/indico -s /bin/bash indico
```

* Install indico

While *running as the indico user*, install UV and create a virtual env at `virtualenvs/indico`. Then install the software:

```console
uv pip install uwsgi indico
```

Run the setup wizard:

```console
indico setup wizard
```

And create the database schema:

```console
indico db prepare
```

You can now *logout the indico user*.

* Create services and config files

Create `/etc/uwsgi-indico.ini`:

```ini
[uwsgi]
uid = indico
gid = www-data
umask = 027

processes = 4
enable-threads = true
chmod-socket = 770
chown-socket = indico:www-data
socket = /opt/indico/web/uwsgi.sock
stats = /opt/indico/web/uwsgi-stats.sock
protocol = uwsgi

master = true
auto-procname = true
procname-prefix-spaced = indico
disable-logging = true

single-interpreter = true

touch-reload = /opt/indico/web/indico.wsgi
wsgi-file = /opt/indico/web/indico.wsgi
virtualenv = /opt/indico/virtualenvs/indico

vacuum = true
buffer-size = 20480
memory-report = true
max-requests = 2500
harakiri = 900
harakiri-verbose = true
reload-on-rss = 2048
evil-reload-on-rss = 8192
```

Indico uwsgi service `/etc/systemd/system/indico-uwsgi.service`:

```
[Unit]
Description=Indico uWSGI
After=network.target

[Service]
ExecStart=/opt/indico/virtualenvs/indico/bin/uwsgi --ini /etc/uwsgi-indico.ini
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
SyslogIdentifier=indico-uwsgi
User=indico
Group=www-data
UMask=0027
Type=notify
NotifyAccess=all
KillMode=mixed
KillSignal=SIGQUIT
TimeoutStopSec=300

[Install]
WantedBy=multi-user.target
```

Celery task runner service ``:

```
[Unit]
Description=Indico Celery
After=network.target

[Service]
ExecStart=/opt/indico/virtualenvs/indico/bin/indico celery worker -B
Restart=always
SyslogIdentifier=indico-celery
User=indico
Group=www-data
UMask=0027
Type=simple
KillMode=mixed
TimeoutStopSec=300

[Install]
WantedBy=multi-user.target
```

* Create the website configs

Create the file `/etc/nginx/sites-available/indico.d-d-s.ch`:

First, populate it with dummy data:

```nginx
server {
  listen 80;
  server_name indico.d-d-s.ch;
}
```

And get the letsencrypt certificates:

```console
sudo systemctl restart nginx
sudo certbot --nginx -d indico.d-d-s.ch --agree-tos --email cmutel@gmail.com
```

Then edit `/etc/nginx/sites-available/indico.d-d-s.ch` to include the following. You may need to adjust the SSL settings:

```nginx
server {
  listen 80;
  listen [::]:80;
  server_name indico.d-d-s.ch;
  return 301 https://$server_name$request_uri;
}

server {
  listen       *:443 ssl http2;
  listen       [::]:443 ssl http2 default ipv6only=on;
  server_name  indico.d-d-s.ch;

  ssl_certificate /etc/letsencrypt/live/indico.d-d-s.ch/fullchain.pem; # managed by Certbot
  ssl_certificate_key /etc/letsencrypt/live/indico.d-d-s.ch/privkey.pem; # managed by Certbot
  include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
  ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot

  access_log            /opt/indico/log/nginx/access.log combined;
  error_log             /opt/indico/log/nginx/error.log;

  if ($host != $server_name) {
    rewrite ^/(.*) https://$server_name/$1 permanent;
  }

  location /.xsf/indico/ {
    internal;
    alias /opt/indico/;
  }

  location ~ ^/(images|fonts)(.*)/(.+?)(__v[0-9a-f]+)?\.([^.]+)$ {
    alias /opt/indico/web/static/$1$2/$3.$5;
    access_log off;
  }

  location ~ ^/(css|dist|images|fonts)/(.*)$ {
    alias /opt/indico/web/static/$1/$2;
    access_log off;
  }

  location /robots.txt {
    alias /opt/indico/web/static/robots.txt;
    access_log off;
  }

  location / {
    root /var/empty/nginx;
    include /etc/nginx/uwsgi_params;
    uwsgi_pass unix:/opt/indico/web/uwsgi.sock;
    uwsgi_param UWSGI_SCHEME $scheme;
    uwsgi_read_timeout 15m;
    uwsgi_buffers 32 32k;
    uwsgi_busy_buffers_size 128k;
    uwsgi_hide_header X-Sendfile;
    client_max_body_size 1G;
  }
}
```

* Start the services

```
sudo systemctl daemon-reload
sudo systemctl start indico-celery
sudo systemctl start indico-uwsgi
systemctl start nginx indico-celery indico-uwsgi
systemctl enable nginx postgresql redis-server indico-celery indico-uwsgi
```

Can check if services started with e.g. `systemctl status indico-celery`

* Restart web server and get certificates

```console
sudo ln -s /etc/nginx/sites-available/indico.d-d-s.ch /etc/nginx/sites-enabled/
```

* Put the `favicon.ico` in the right place

```console
sudo cp /var/www/registration/static/favicon.ico /opt/indico/web/static/images/
```

Edit `/opt/indico/etc/indico.conf` and add `FAVICON_URL='https://indico.d-d-s.ch/images/favicon.ico'`

* Add logos

- Copy cropped logo from `https://github.com/Depart-de-Sentier/dds-logo/blob/main/PNG/White%20Logo%402x.png` to `/opt/indico/web/static/images/logo.png`.
- Set permissions: `chown indico:www-data /opt/indico/web/static/images/logo.png`
- Edit `/opt/indico/etc/indico.conf` and add `LOGO_URL='https://indico.d-d-s.ch/images/logo.png'.
- Copy cropped logo from `https://github.com/Depart-de-Sentier/dds-logo/blob/main/PNG/Green%20Logo%402x.png` to `/opt/indico/web/static/images/login.png`.
- Set permissions: `chown indico:www-data /opt/indico/web/static/images/login.png`
- Edit `/opt/indico/etc/indico.conf` and add `LOGIN_LOGO_URL='https://indico.d-d-s.ch/images/login.png'.
- Restart indico: `sudo systemctl restart indico-uwsgi`

* Configure the email backend:

Add the following to `/opt/indico/etc/indico.conf`

`EMAIL_BACKEND='django_gsuite_token.GSuiteEmailBackend'`

Install and configure https://github.com/Depart-de-Sentier/django-gsuite-token (i.e. need to provide `token.json`).

## Django authentication

Authentication using the Django user data base is done using the
`flask_multipass_django` providers, currently at:

https://github.com/bbguimaraes/dds-infrastructure/tree/indico/indico/flask_multipass_django

* Build the plugin (can be done in another machine):

    $ cd /path/to/flask_multipass_django/
    $ python -m build

* Install it.

    $ su -l indico
    $ export VIRTUAL_ENV=virtualenvs/indico
    $ uv pip install /path/to/flask_multipass_django-0.0.0.tar.gz

* Add authentication/identity provider configuration:

    # /opt/indico/etc/indico.conf
    LOCAL_REGISTRATION = False
    LOCAL_IDENTITIES = False
    EXTERNAL_REGISTRATION_URL = "events.d-d-s.ch"
    AUTH_PROVIDERS = {
        "events.d-d-s.ch": {
            "type": "django",
            "title": "your events.d-d-s.ch account",
            "user_table": "dds_registration_user",
            "sqlalchemy_url": "sqlite:////home/registration/registration/db.sqlite3",
        },
    }
    IDENTITY_PROVIDERS = {
        "events.d-d-s.ch": {
            "type": "django",
            "trusted_email": True,
            "synced_fields": ["email", "first_name", "last_name"],
        },
    }
    PROVIDER_MAP = {"events.d-d-s.ch": "events.d-d-s.ch"}

* Add the `indico` user to the `registration` group so it can read the data base
  file:

  # /etc/group
  registration:x:1266:indico

* Signal `uwsgi` to reload its configuration:

  $ systemctl reload indico-uwsgi.service

# OpenMetadata

Installation using `docker-compose`:

https://docs.open-metadata.org/latest/quick-start/local-docker-deployment

## Deployment

    # mkdir ~/openmetadata/
    # cd ~/openmetadata/

Download the deployment file from the desired release in GitHub:

https://github.com/open-metadata/OpenMetadata/releases/

    # curl --location \
        --output docker-compose.yml \
        https://github.com/open-metadata/OpenMetadata/releases/download/1.8.6-release/docker-compose-postgres.yml

Fix database user configuration:

```diff
--- podman-compose.yml
+++ podman-compose.yml
@@ -22,8 +22,8 @@
     restart: always
     command: "--work_mem=10MB"
     environment:
-      POSTGRES_USER: postgres
-      POSTGRES_PASSWORD: password
+      POSTGRES_USER: ${DB_USER:-openmetadata_user}
+      POSTGRES_PASSWORD: ${DB_USER_PASSWORD:-openmetadata_password}
     expose:
       - 5432
     ports:
@@ -34,7 +34,7 @@
     networks:
       - app_net
     healthcheck:
-      test: psql -U postgres -tAc 'select 1' -d openmetadata_db
+      test: psql -U $DB_USER -tAc 'select 1' -d $OM_DATABASE
       interval: 15s
       timeout: 10s
       retries: 10
```

Remove public ports from the deployment:

```diff
--- podman-compose.yml
+++ podman-compose.yml
@@ -26,8 +26,6 @@
       POSTGRES_PASSWORD: ${DB_USER_PASSWORD:-openmetadata_password}
     expose:
       - 5432
-    ports:
-      - "5432:5432"
     volumes:
      - ./docker-volume/db-data-postgres:/var/lib/postgresql/data
     
@@ -48,9 +46,6 @@
       - xpack.security.enabled=false
     networks:
       - app_net
-    ports:
-      - "9200:9200"
-      - "9300:9300"
     healthcheck:
       test: "curl -s http://localhost:9200/_cluster/health?pretty | grep status | grep -qE 'green|yellow' || exit 1"
       interval: 15s
@@ -475,8 +470,8 @@
       - 8585
       - 8586
     ports:
-      - "8585:8585"
-      - "8586:8586"
+      - "127.0.0.1:8585:8585"
+      - "127.0.0.1:8586:8586"
     depends_on:
       elasticsearch:
         condition: service_healthy
@@ -524,8 +519,6 @@
       - "/opt/airflow/ingestion_dependency.sh"
     expose:
       - 8080
-    ports:
-      - "8080:8080"
     networks:
       - app_net
     volumes:
```

Add a configuration file (the empty `OIDC_CUSTOM_PARAMS` entry is required
because the parser cannot handle the default value in the official `compose`
file):

    # cat > env <<'EOF'
    AUTHORIZER_ADMIN_PRINCIPALS=[admin,bruno,cmutel]
    AUTHORIZER_PRINCIPAL_DOMAIN=d-d-s.ch
    DB_USER=openmetadata
    DB_USER_PASSWORD=…
    OM_DATABASE=openmetadata
    OIDC_CUSTOM_PARAMS=
    EOF

Start services:

    # docker compose --env-file env up --detach

**Note** : if using `podman` before 5.6.0 to test locally, a bug in transitive
dependency handling prevents the server from starting (see
https://github.com/containers/podman-compose/issues/921).  The services can be
started manually:

```
[openmetadata-server] | Error: unable to start container 99f10d87f9676a18491beffb90912cde164bfe16e5bb50de8c49892c04f78d0f: generating dependency graph for container 99f10d87f9676a18491beffb90912cde164bfe16e5bb50de8c49892c04f78d0f: container 017d3c34f92aa376f74fe99ec6b80fe3eaa9162cb3cfcd7df33c9eb37fea9e56 depends on container 2194e5ce1d59d0701f86ef3cbdf2fe1289beb295f4a4092dc18700fdb94fa9d2 not found in input list: no such container
```

```console
# podman compose \
    --env-file env \
    up --detach --no-deps ingestion openmetadata-server
```

Test that services are working correctly using an SSH tunnel:

    $ ssh -NL 8000:localhost:8585 176.9.61.115
