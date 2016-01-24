Debian Installation
===================

By default, Moneta is only packaged as a standard Python project, downloadable from `Pypi <https://pypi.python.org>`_.
However, you can create pure Debian packages with `DjangoFloor <http://django-floor.readthedocs.org/en/latest/packaging.html#debian-ubuntu>`_.

The source code provides several Bash scripts:

    * `deb-debian-8-python3.sh`,
    * `deb-ubuntu-14.04-15.10.sh`.

These scripts are designed to run on basic installation and are split in five steps:

    * update system and install missing packages,
    * create a virtualenv and install all dependencies,
    * package all dependencies,
    * package Moneta,
    * install all packages and Moneta, prepare a simple configuration to test.

If everything is ok, you can copy all the .deb packages to your private mirror or to the destination server.
By default, Moneta is installed with Apache 2.4 and systemd.
You can switch to Nginx or Systemd by tweaking the right `stdeb-XXX.cfg` file.


Configuration
-------------

Default configuration file is `/etc/moneta/settings.ini`.
If you need more complex settings, you can override default values (given in `djangofloor.defaults` and
`moneta.defaults`) by creating a file named `/etc/moneta/settings.py`.
After any change in the database configuration or any upgrade, you must migrate the database to create the required tables.

.. code-block:: bash

    sudo -u moneta moneta-manage migrate


After installation and configuration, do not forget to create a superuser:

.. code-block:: bash

    sudo -u moneta moneta-manage createsuperuser





Launch the service
------------------

The service

.. code-block:: bash

    sudo service moneta-gunicorn start


If you want Moneta to be started at startup, you have to enable it in systemd:

.. code-block:: bash

    systemctl enable moneta-gunicorn.service




Backup
------

A complete Moneta installation is made a different kinds of files:

    * the code of your application and its dependencies (you should not have to backup them),
    * static files (as they are provided by the code, you can lost them),
    * configuration files (you can easily recreate it, or you must backup it),
    * database content (you must backup it),
    * user-created files (you must also backup them).

Many backup strategies exist, and you must choose one that fits your needs. We can only propose general-purpose strategies.

We use logrotate to backup the database, with a new file each day.

.. code-block:: bash

  sudo mkdir -p /var/backups/moneta
  sudo chown -r moneta: /var/backups/moneta
  sudo -u moneta -i
  cat << EOF > /etc/moneta/backup_db.conf
  /var/backups/moneta/backup_db.sql.gz {
    daily
    rotate 20
    nocompress
    missingok
    create 640 moneta moneta
    postrotate
    myproject-manage dumpdb | gzip > /var/backups/moneta/backup_db.sql.gz
    endscript
  }
  EOF
  touch /var/backups/moneta/backup_db.sql.gz
  crontab -e
  MAILTO=admin@moneta.example.org
  0 1 * * * /usr/local/bin/moneta-manage clearsessions
  0 2 * * * logrotate -f /etc/moneta/backup_db.conf


Backup of the user-created files can be done with rsync, with a full backup each month:
If you have a lot of files to backup, beware of the available disk place!

.. code-block:: bash

  sudo mkdir -p /var/backups/moneta/media
  sudo chown -r moneta: /var/backups/moneta
  cat << EOF > /etc/moneta/backup_media.conf
  /var/backups/moneta/backup_media.tar.gz {
    monthly
    rotate 6
    nocompress
    missingok
    create 640 moneta moneta
    postrotate
    tar -C /var/backups/moneta/media/ -czf /var/backups/moneta/backup_media.tar.gz .
    endscript
  }
  EOF
  touch /var/backups/moneta/backup_media.tar.gz
  crontab -e
  MAILTO=admin@moneta.example.org
  0 3 * * * rsync -arltDE /var/moneta/data/media/ /var/backups/moneta/media/
  0 5 0 * * logrotate -f /etc/moneta/backup_media.conf

Restoring a backup
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

  cat /var/backups/moneta/backup_db.sql.gz | gunzip | /usr/local/bin/moneta-manage dbshell
  tar -C /var/moneta/data/media/ -xf /var/backups/moneta/backup_media.tar.gz





Monitoring
----------


Nagios or Shinken
~~~~~~~~~~~~~~~~~

You can use Nagios checks to monitor several points:

  * connection to the application server (gunicorn or uwsgi):
  * connection to the database servers (PostgreSQL),
  * connection to the reverse-proxy server (apache or nginx),
  * the validity of the SSL certificate (can be combined with the previous check),
  * creation date of the last backup (database and files),
  * living processes for gunicorn, postgresql, apache,
  * standard checks for RAM, disk, swap…

Here is a sample NRPE configuration file:

.. code-block:: bash

  cat << EOF | sudo tee /etc/nagios/nrpe.d/moneta.cfg
  command[moneta_wsgi]=/usr/lib/nagios/plugins/check_http -H 127.0.0.1 -p 8131
  command[moneta_database]=/usr/lib/nagios/plugins/check_tcp -H localhost -p 5432
  command[moneta_reverse_proxy]=/usr/lib/nagios/plugins/check_http -H moneta.example.org -p 80 -e 401
  command[moneta_backup_db]=/usr/lib/nagios/plugins/check_file_age -w 172800 -c 432000 /var/backups/moneta/backup_db.sql.gz
  command[moneta_backup_media]=/usr/lib/nagios/plugins/check_file_age -w 3024000 -c 6048000 /var/backups/moneta/backup_media.sql.gz
  command[moneta_gunicorn]=/usr/lib/nagios/plugins/check_procs -C python -a '/usr/local/bin/moneta-gunicorn'
  EOF

Sentry
~~~~~~

For using Sentry to log errors, you must add `raven.contrib.django.raven_compat` to the installed apps.

.. code-block:: ini

  [global]
  extra_apps = raven.contrib.django.raven_compat
  [sentry]
  dsn_url = https://[key]:[secret]@app.getsentry.com/[project]

Of course, the Sentry client (Raven) must be separately installed, before testing the installation:

.. code-block:: bash

  sudo -u moneta -i
  moneta-manage raven test




