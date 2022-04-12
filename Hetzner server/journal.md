Server is on hetzner.com. Static IP is:

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

# TLJH (https://tljh.jupyter.org/)

    sudo apt install python3 python3-dev git curl
    curl -L https://tljh.jupyter.org/bootstrap.py | sudo -E python3 - --admin cmutel

## TLJH networking

Change `traefik` to only listen to localhost by editing `/opt/tljh/state/traefik.toml`:

    [entryPoints.http]
    address = "127.0.0.1:8100"


# NGINX

Follow instructions from https://www.digitalocean.com/community/tutorials/how-to-install-nginx-on-ubuntu-18-04#step-5-setting-up-server-blocks-(recommended)

    sudo apt update
    sudo apt-get upgrade
    sudo apt install nginx

Check it is running:

    systemctl status nginx

Check configuration

    nginx -c /etc/nginx/nginx.conf -t

Restart command:

    sudo systemctl restart nginx

# DNS entries

`brightway.dev` is managed with the Vultr DNS. Currently I point only `hub.brightway.dev` at the Hetzner server.

**Note: the following is from a previous install ~1.5 years ago. Maybe there are easier ways now**

## HTTPS with certbot

Follow instructions from https://www.digitalocean.com/community/tutorials/how-to-secure-nginx-with-let-s-encrypt-on-ubuntu-18-04

Wildcard instructions from https://medium.com/@saurabh6790/generate-wildcard-ssl-certificate-using-lets-encrypt-certbot-273e432794d7

    sudo add-apt-repository ppa:certbot/certbot
    sudo apt install python-certbot-nginx

Test NGINX config with

    sudo nginx -t

To get this to work, I had to delete all https from all initial site configs.

Generate wildcard certificates:

    sudo certbot -d *.brightwaylca.org -d *.docs.brightwaylca.org -d brightwaylca.org --manual --agree-tos --preferred-challenges=dns --email cmutel@gmail.com certonly
    sudo certbot -d *.dorfsteig.ch -d dorfsteig.ch --manual --agree-tos --preferred-challenges=dns --email cmutel@gmail.com certonly
    sudo certbot -d *.mutel.org -d mutel.org --manual --agree-tos --preferred-challenges=dns --email cmutel@gmail.com certonly
    sudo certbot -d *.brightcon.link -d brightcon.link --manual --agree-tos --preferred-challenges=dns --email cmutel@gmail.com certonly

In each case, one needs to add one or more TXT DNS records, but this is easy.

Can get info on current certificates with

    sudo certbot certificates

Certbot adds stuff to `/etc/nginx/sites-enabled/default`, clean this file and move useful stuff to the relevant site configs manually.

Renew certificates:

    sudo certbot renew
