Server is on hetzner.com. Static IP is currently:

    65.21.94.58

# Create user `cmutel`

    adduser cmutel
    usermod -aG sudo cmutel

# SSH

1. Back up existing config:

    sudo cp /etc/ssh/sshd_config{,.bak}

2. Copy my keys to server

    ssh-copy-id -i .ssh/id_rsa.pub cmutel@5.9.116.7

3. Add hetzner config to local `~/.ssh/config`

    Host hetzner3
    Hostname 65.21.94.58

4. Disable SSH root and password login

    sudo nano /etc/ssh/sshd_config

And change to:

    PermitRootLogin no
    PasswordAuthentication no
    ChallengeResponseAuthentication no
    X11Forwarding no

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
# make jupyterlab app default:
sudo tljh-config set user_environment.default_app jupyterlab
sudo tljh-config reload hub
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

`brightcon.link` is managed with the Vultr DNS. 
Hetzner server 3 has:

+ ami.brightcon.link

## HTTPS with certbot

### Add site to nginx config

Following https://www.digitalocean.com/community/tutorials/how-to-install-nginx-on-ubuntu-20-04#step-5-%E2%80%93-setting-up-server-blocks-(recommended) add a file to
`/etc/nginx/sites-available/ami.brightcon.link` with basic http config.

The file is at the repo https://github.com/Depart-de-Sentier/Infrastructure/. This file does not contain _yet_ the actual ssl details it's a http only configuration so that we can have a working nginx when using certbot to generate the certs. It's a template with the required configuration for the forwarding.

Add a link to the sites-enabled:

```
sudo ln -s /etc/nginx/sites-available/ami.brightcon.link /etc/nginx/sites-enabled
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
sudo certbot --nginx -d ami.brightcon.link --agree-tos --email cmutel@gmail.com
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


# Add keycloak as authorization mechanism for tljh

## keycloak side

+ Make sure the client (jupyterhub2) includes "ami.brightcon.link" as vaid post logout and redirect valid urls.

Add the following code to the `/opt/tljh/config/jupyterhub_config.d/keycloak_config.py`

```
# from: https://github.com/jupyterhub/oauthenticator/tree/main/examples/generic
from oauthenticator.generic import GenericOAuthenticator
import os
from urllib.parse import urlencode

keycloak_server = "portunus.brightcon.link"
the_jupyterhub = "ami.brightcon.link"

os.environ["OAUTH2_TOKEN_URL"] = f"https://{keycloak_server}/realms/brightconclasses/protocol/openid-connect/token"
os.environ["OAUTH2_AUTHORIZE_URL"] = f"https://{keycloak_server}/realms/brightconclasses/protocol/openid-connect/auth"
os.environ["OAUTH2_USERDATA_URL"] = f"https://{keycloak_server}/realms/brightconclasses/protocol/openid-connect/userinfo"


c.Application.log_level = "DEBUG"
c.JupyterHub.authenticator_class = GenericOAuthenticator

c.Authenticator.auto_login = False
c.GenericOAuthenticator.oauth_callback_url  = f"https://{the_jupyterhub}/hub/oauth_callback"
c.GenericOAuthenticator.client_id = "jupyterhub2"
# See the logout options at: https://www.keycloak.org/docs/latest/securing_apps/index.html#logout
c.GenericOAuthenticator.logout_redirect_url = f"https://{keycloak_server}/realms/brightconclasses/protocol/openid-connect/logout?" +  urlencode({"post_logout_redirect_uri": f"https://{the_jupyterhub}/hub/", "client_id":"jupyterhub2"})
c.GenericOAuthenticator.client_secret = "THE_SECRET_FROM_THE_APTHE_SECRET_FROM_THE_APPP"
c.GenericOAuthenticator.token_url = f"https://{keycloak_server}/realms/brightconclasses/protocol/openid-connect/token"
c.GenericOAuthenticator.userdata_url = f"https://{keycloak_server}/realms/brightconclasses/protocol/openid-connect/userinfo"
c.GenericOAuthenticator.userdata_params = {"state": "state"}
# the next can be a callable as well, e.g.: lambda t: t.get("complex").get("structure").get("username")
c.GenericOAuthenticator.username_key = "preferred_username"
c.GenericOAuthenticator.login_service = "Keycloak 2022"
c.GenericOAuthenticator.scope = ["openid", "profile"]
```
