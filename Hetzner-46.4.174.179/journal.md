Server is on hetzner.com. Static IP is currently:

    46.4.174.179

# Create user `cmutel`

    adduser cmutel
    usermod -aG sudo cmutel

# SSH

1. Back up existing config:

    sudo cp /etc/ssh/sshd_config{,.bak}

2. Copy my keys to server

    ssh-copy-id -i .ssh/id_ed25519.pub cmutel@46.4.174.179

3. Add hetzner config to local `~/.ssh/config`

    Host spring
    Hostname 46.4.174.179

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
