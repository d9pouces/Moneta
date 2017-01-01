#!/usr/bin/env bash
mkdir -p /var/moneta/gpg/
chown -R moneta: /var/moneta/
chmod 0700 /var/moneta/gpg/
sudo -u moneta moneta-manage gpg_gen generate
KEY_ID=`sudo -u moneta moneta-manage gpg_gen show | tail -n 1 | cut -f 4 -d ' ' | cut -f 1 -d ','`
sed -i "s/1DA759EA7F5EF06F/$KEY_ID/g" /etc/moneta/settings.ini
