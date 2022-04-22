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

Install using the user `conda` (i.e. not the TLJH one):

```
miniconda3/bin/conda create -n pandarus_remote python=3.9 pandarus_remote
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

Set up to run under systemd by creating `/etc/systemd/system/rq-worker.service`:

```
[Unit]
Description=RQ worker

[Service]
ExecStart=/home/cmutel/miniconda3/envs/pandarus_remote/bin/rq worker

[Install]
WantedBy=multi-user.target
```

Then enable and start:

```
systemctl daemon-reload
systemctl enable rq-worker.service
systemctl start rq-worker.service
```

## Setting up `pandarus.brightway.dev`

Site config in `sites-available`. DNS A name added pointing to Hetzner server.

```
sudo mv pandarus.brightway.dev /etc/nginx/sites-available/
sudo chown root:root /etc/nginx/sites-available/pandarus.brightway.dev
sudo ln -s /etc/nginx/sites-available/pandarus.brightway.dev /etc/nginx/sites-enabled/
sudo certbot --nginx -d pandarus.brightway.dev --agree-tos --email cmutel@gmail.com
```


## [Waitress WSGI server](https://docs.pylonsproject.org/projects/waitress/en/latest/)

```
miniconda3/bin/conda create -n waitress waitress
```

Create a runner Python program:

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
ExecStart=/home/cmutel/miniconda3/envs/pandarus_remote/bin/python /home/cmutel/pr/pr_runner.py

[Install]
WantedBy=multi-user.target
```

Then enable and start:

```
systemctl daemon-reload
systemctl enable pr-worker.service
systemctl start pr-worker.service
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
