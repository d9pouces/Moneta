
Complete configuration
======================


Configuration options
---------------------

You can look current settings with the following command:

.. code-block:: bash

    moneta-manage config ini -v 2

You can also display the actual list of Python settings

.. code-block:: bash

    moneta-manage config python -v 2


Here is the complete list of settings:

.. code-block:: ini

  [database]
  db = moneta 
  	# Main database name (or path of the sqlite3 database)
  engine = postgresql 
  	# Main database engine ("mysql", "postgresql", "sqlite3", "oracle", or the dotted name of the Django backend)
  host = localhost 
  	# Main database host
  password = 5trongp4ssw0rd 
  	# Main database password
  port = 5432 
  	# Main database port
  user = moneta 
  	# Main database user
  
  [email]
  host = localhost 
  	# SMTP server
  password =  
  	# SMTP password
  port = 25 
  	# SMTP port (often 25, 465 or 587)
  use_ssl = False 
  	# "true" if your SMTP uses SSL (often on port 465)
  use_tls = False 
  	# "true" if your SMTP uses STARTTLS (often on port 587)
  user =  
  	# SMTP user
  
  [global]
  admin_email = admin@moneta.example.org 
  	# e-mail address for receiving logged errors
  data = $VIRTUALENV/var/moneta 
  	# where all data will be stored (static/uploaded/temporary files, …)If you change it, you must run the collectstatic and migrate commands again.
  language_code = fr-fr 
  	# default to fr_FR
  listen_address = 127.0.0.1:8131 
  	# address used by your web server.
  log_remote_url =  
  	# Send logs to a syslog or systemd log daemon.  
  	# Examples: syslog+tcp://localhost:514/user, syslog:///local7,syslog:///dev/log/daemon, logd:///project_name
  server_url = http://moneta.example.org 
  	# Public URL of your website.  
  	# Default to "http://listen_address" but should be ifferent if you use a reverse proxy like Apache or Nginx. Example: http://www.example.org.
  time_zone = Europe/Paris 
  	# default to Europe/Paris
  use_apache = True 
  	# Apache only. Set it to "true" or "false"
  use_nginx = False 
  	# Nginx only. Set it to "true" or "false"
  
  [gnupg]
  home = $VIRTUALENV/var/moneta/gpg/ 
  	# Path of the GnuPG secret data
  keyid = 1DA759EA7F5EF06F 
  	# ID of the GnuPG key
  path = gpg 
  	# Path of the gpg binary
  



If you need more complex settings, you can override default values (given in `djangofloor.defaults` and
`moneta.defaults`) by creating a file named `/moneta/settings.py`.



Optional components
-------------------

Efficient page caching
~~~~~~~~~~~~~~~~~~~~~~

You just need to install `django-redis-sessions`. Settings are automatically changed for using a local Redis server (of course, you can change it in your config file).

.. code-block:: bash

  pip install django-redis-sessions

Faster session storage
~~~~~~~~~~~~~~~~~~~~~~

You just need to install `redis-sessions` for storing sessions into user sessions in Redis instead of storing them in the main database.
Redis is not designed to be backuped; if you loose your Redis server, sessions are lost and all users must login again.
However, Redis is faster than your main database server and sessions take a huge place if they are not regularly cleaned.
Settings are automatically changed for using a local Redis server (of course, you can change it in your config file).

.. code-block:: bash

  pip install redis-sessions

Optimized media files
~~~~~~~~~~~~~~~~~~~~~

You can use `Django-Pipeline <https://django-pipeline.readthedocs.io/en/latest/configuration.html>`_ to merge all media files (CSS and JS) for a faster site.

.. code-block:: bash

  pip install django-pipeline

Optimized JavaScript files are currently deactivated due to syntax errors in generated files (not my fault ^^).



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
  cat << EOF > /etc/moneta/backup_db.conf
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
  0 1 * * * moneta-manage clearsessions
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
  0 3 * * * rsync -arltDE $VIRTUALENV/var/moneta/media/ /var/backups/moneta/media/
  0 5 0 * * logrotate -f /etc/moneta/backup_media.conf

Restoring a backup
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

  cat /var/backups/moneta/backup_db.sql.gz | gunzip | moneta-manage dbshell
  tar -C $VIRTUALENV/var/moneta/media/ -xf /var/backups/moneta/backup_media.tar.gz






LDAP groups
-----------

There are two possibilities to use LDAP groups, with their own pros and cons:

  * on each request, use an extra LDAP connection to retrieve groups instead of looking in the SQL database,
  * regularly synchronize groups between the LDAP server and the SQL servers.

The second approach can be used without any modification in your code and remove a point of failure
in the global architecture (if you can afford regular synchronizations instead of instant replication).
At least one tool exists for such synchronization: `MultiSync <https://github.com/d9pouces/Multisync>`_.
