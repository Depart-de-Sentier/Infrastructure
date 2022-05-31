server {
    server_name cauldron.ch;
    access_log  /var/log/nginx/cauldron.ch.access.log;

    location / {
        root /home/cmutel/cauldron_website;
        index index.html;
    }
}
