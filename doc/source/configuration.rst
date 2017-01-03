
Complete configuration
======================


Configuration options
---------------------

You can look current settings with the following command:

.. code-block:: bash

    moneta-manage config

Here is the complete list of settings:

.. code-block:: ini

  [database]
  db = moneta
  engine = postgresql
  host = localhost
  password = 5trongp4ssw0rd
  port = 5432
  user = moneta
  
  [email]
  host = localhost
  password = 
  port = 25
  use_ssl = False
  use_tls = False
  user = 
  
  [global]
  admin_email = admin@moneta.example.org
  data = /var/moneta
  language_code = fr-fr
  listen_address = 127.0.0.1:8131
  log_remote_url = 
  secret_key = secret_key
  server_url = http://moneta.example.org
  time_zone = Europe/Paris
  use_apache = True
  use_nginx = False
  
  [gnupg]
  home = /var/moneta/gpg/
  keyid = 1DA759EA7F5EF06F
  path = gpg
  



If you need more complex settings, you can override default values (given in `djangofloor.defaults` and
`moneta.defaults`) by creating a file named `/moneta/settings.py`.



Debugging
---------

If something does not work as expected, you can look at logs (in /var/log/supervisor if you use supervisor)
or try to run the server interactively:

.. code-block:: bash

  sudo service supervisor stop
  sudo -u moneta -i
  workon moneta
  moneta-manage config
  moneta-manage runserver
  moneta-gunicorn




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
  cat << EOF > /moneta/backup_db.conf
  /var/backups/moneta/backup_db.sql.gz {
    daily
    rotate 20
    nocompress
    missingok
    create 640 moneta moneta
    postrotate
    moneta-manage dumpdb | gzip > /var/backups/moneta/backup_db.sql.gz
    endscript
  }
  EOF
  touch /var/backups/moneta/backup_db.sql.gz
  crontab -e
  MAILTO=admin@moneta.example.org
  0 1 * * * /moneta-manage clearsessions
  0 2 * * * logrotate -f /moneta/backup_db.conf


Backup of the user-created files can be done with rsync, with a full backup each month:
If you have a lot of files to backup, beware of the available disk place!

.. code-block:: bash

  sudo mkdir -p /var/backups/moneta/media
  sudo chown -r moneta: /var/backups/moneta
  cat << EOF > /moneta/backup_media.conf
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
  0 3 * * * rsync -arltDE /var/moneta/media/ /var/backups/moneta/media/
  0 5 0 * * logrotate -f /moneta/backup_media.conf

Restoring a backup
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

  cat /var/backups/moneta/backup_db.sql.gz | gunzip | /moneta-manage dbshell
  tar -C /var/moneta/media/ -xf /var/backups/moneta/backup_media.tar.gz





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
  command[moneta_wsgi]=/usr/lib/nagios/plugins/check_http -H moneta.example.org -p 443
  command[moneta_reverse_proxy]=/usr/lib/nagios/plugins/check_http -H moneta.example.org -p 80 -e 401
  command[moneta_backup_db]=/usr/lib/nagios/plugins/check_file_age -w 172800 -c 432000 /var/backups/moneta/backup_db.sql.gz
  command[moneta_backup_media]=/usr/lib/nagios/plugins/check_file_age -w 3024000 -c 6048000 /var/backups/moneta/backup_media.sql.gz
  command[moneta_gunicorn]=/usr/lib/nagios/plugins/check_procs -C python -a '/moneta-gunicorn'
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





LDAP groups
-----------

There are two possibilities to use LDAP groups, with their own pros and cons:

  * on each request, use an extra LDAP connection to retrieve groups instead of looking in the SQL database,
  * regularly synchronize groups between the LDAP server and the SQL servers.

The second approach can be used without any modification in your code and remove a point of failure
in the global architecture (if you allow some delay during the synchronization process).
A tool exists for such synchronization: `MultiSync <https://github.com/d9pouces/Multisync>`_.
