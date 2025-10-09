Server is on hetzner.com. Static IP is currently:

    46.4.174.178

# Create user `cmutel`

    adduser cmutel
    usermod -aG sudo cmutel

# SSH

1. Back up existing config:

    sudo cp /etc/ssh/sshd_config{,.bak}

2. Copy my keys to server

    ssh-copy-id -i .ssh/id_ed25519.pub cmutel@46.4.174.178

3. Add hetzner config to local `~/.ssh/config`

    Host fall
    Hostname 46.4.174.178

4. Disable SSH root and password login

    sudo nano /etc/ssh/sshd_config

And change to:

    PermitRootLogin no
    PasswordAuthentication no
    KbdInteractiveAuthentication no

Restart ssh:

    sudo systemctl restart ssh

# Upgrade packages

    sudo apt update && sudo apt upgrade -y

# Add other admins

    sudo adduser tomas
    sudo usermod -aG sudo tomas

    sudo mkdir /home/tomas/.ssh
sudo nano /home/tomas/.ssh/authorized_keys
sudo chown tomas:tomas /home/tomas/.ssh
sudo chown tomas:tomas /home/tomas/.ssh/authorized_keys
sudo chmod 0700 /home/tomas/.ssh
sudo chmod 0600 /home/tomas/.ssh/authorized_keys

# TLJH

Follow:
https://tljh.jupyter.org/en/latest/install/custom-server.html 

```bash
# apt install python3 python3-dev git curl
# cd /opt
# curl -L https://tljh.jupyter.org/bootstrap.py | sudo -E python3 - --admin tomas
```
## config nginx
+ add site-available for fall.brightcon.link
+ configure the site to forward to localhost:

```
map $http_upgrade $connection_upgrade { 
    default upgrade;
    ''      close;                  
}
server {
    server_name fall.brightcon.link;
    access_log  /var/log/nginx/fall.brightcon.link.access.log;                                                                                             
    server_tokens        off;

    client_max_body_size 100m;

    location / {
        proxy_pass http://localhost:8100;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # websocket headers
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header X-Scheme $scheme;
        proxy_buffering off;
        # For the SameSite error
        #add_header 'Set-Cookie' 'SameSite=None; Secure';
        #proxy_cookie_path ~^/(.+)$ "/$1; SameSite=none";

    }
```


## config traefik (from tljh)
make the `/opt/tljh/state/traefik.toml` file look as follows:
(change the entrypoints to another port, because we manage SSL with nginx and certbot

```
[api]

[log]
level = "INFO"

[accessLog]
format = "json"

[providers]
providersThrottleDuration = "0s"

[accessLog.filters]
statusCodes = [ "500-999",]

[entryPoints.http]
address = "localhost:8100"

[entryPoints.auth_api]
address = "localhost:8099"

[providers.file]
directory = "/opt/tljh/state/rules"
watch = true

[accessLog.fields.headers.names]
Authorization = "redact"
Cookie = "redact"
Set-Cookie = "redact"
X-Xsrftoken = "redact"

[entryPoints.http.transport.respondingTimeouts]
idleTimeout = "10m"

```

