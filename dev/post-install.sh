#!/bin/sh

set -e

USER_EXISTS=`getent passwd moneta || :`
if [ -z "${USER_EXISTS}" ]; then
    useradd moneta -b /var/ -U -r
fi


mkdir -p /opt/moneta/var/media
mkdir -p /opt/moneta/var/data
mkdir -p /opt/moneta/var/log
chown -R : /opt/moneta


set +e

