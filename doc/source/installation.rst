Installation
============

Like many Python packages, you can use several methods to install Moneta.
Moneta designed to run with python3.5.x+.
The following packages are also required:

  * setuptools >= 3.0
  * djangofloor >= 0.18.0
  * python-gnupg
  * rubymarshal
  * pyyaml



Of course you can install it from the source, but the preferred way is to install it as a standard Python package, via pip.


Installing or Upgrading
-----------------------

Here is a simple tutorial to install Moneta on a basic Debian/Linux installation.
You should easily adapt it on a different Linux or Unix flavor.

Ruby
----

If you want to use the Ruby mirror functionnality, Ruby is required on the server:

.. code-block:: bash

   sudo apt-get install ruby


Database
--------

PostgreSQL is often a good choice for Django sites:

.. code-block:: bash

   sudo apt-get install postgresql
   echo "CREATE USER moneta" | sudo -u postgres psql -d postgres
   echo "ALTER USER moneta WITH ENCRYPTED PASSWORD '5trongp4ssw0rd'" | sudo -u postgres psql -d postgres
   echo "ALTER ROLE moneta CREATEDB" | sudo -u postgres psql -d postgres
   echo "CREATE DATABASE moneta OWNER moneta" | sudo -u postgres psql -d postgres




Apache
------

I only present the installation with Apache, but an installation behind nginx should be similar.
You cannot use different server names for browsing your mirror. If you use `moneta.example.org`
in the configuration, you cannot use its IP address to access the website.

.. code-block:: bash

    SERVICE_NAME=moneta.example.org
    sudo apt-get install apache2 libapache2-mod-xsendfile
    sudo a2enmod headers proxy proxy_http
    sudo a2dissite 000-default.conf
    # sudo a2dissite 000-default on Debian7
    cat << EOF | sudo tee /etc/apache2/sites-available/moneta.conf
    <VirtualHost *:80>
        ServerName $SERVICE_NAME
        Alias /static/ /var/moneta/static/
        ProxyPass /static/ !
        <Location /static/>
            Order deny,allow
            Allow from all
            Satisfy any
        </Location>
        ProxyPass / http://127.0.0.1:8131/
        ProxyPassReverse / http://127.0.0.1:8131/
        DocumentRoot /var/moneta/static/
        ServerSignature off
        XSendFile on
        XSendFilePath /var/moneta/media/
        # in older versions of XSendFile (<= 0.9), use XSendFileAllowAbove On
    </VirtualHost>
    EOF
    sudo mkdir /var/moneta
    sudo chown -R www-data:www-data /var/moneta
    sudo a2ensite moneta.conf
    sudo apachectl -t
    sudo apachectl restart


If you want to use SSL:

.. code-block:: bash

    sudo apt-get install apache2 libapache2-mod-xsendfile
    PEM=/etc/apache2/`hostname -f`.pem
    # ok, I assume that you already have your certificate
    sudo a2enmod headers proxy proxy_http ssl
    openssl x509 -text -noout < $PEM
    sudo chown www-data $PEM
    sudo chmod 0400 $PEM

    sudo apt-get install libapache2-mod-auth-kerb
    KEYTAB=/etc/apache2/http.`hostname -f`.keytab
    # ok, I assume that you already have your keytab
    sudo a2enmod auth_kerb
    cat << EOF | sudo ktutil
    rkt $KEYTAB
    list
    quit
    EOF
    sudo chown www-data $KEYTAB
    sudo chmod 0400 $KEYTAB

    SERVICE_NAME=moneta.example.org
    cat << EOF | sudo tee /etc/apache2/sites-available/moneta.conf
    <VirtualHost *:80>
        ServerName $SERVICE_NAME
        RedirectPermanent / https://$SERVICE_NAME/
    </VirtualHost>
    <VirtualHost *:443>
        ServerName $SERVICE_NAME
        SSLCertificateFile $PEM
        SSLEngine on
        Alias /static/ /var/moneta/static/
        ProxyPass /static/ !
        <Location /static/>
            Order deny,allow
            Allow from all
            Satisfy any
        </Location>
        ProxyPass / http://127.0.0.1:8131/
        ProxyPassReverse / http://127.0.0.1:8131/
        DocumentRoot /var/moneta/static/
        ServerSignature off
        RequestHeader set X_FORWARDED_PROTO https
        <Location />
            AuthType Kerberos
            AuthName "Moneta"
            KrbAuthRealms EXAMPLE.ORG example.org
            Krb5Keytab $KEYTAB
            KrbLocalUserMapping On
            KrbServiceName HTTP
            KrbMethodK5Passwd Off
            KrbMethodNegotiate On
            KrbSaveCredentials On
            Require valid-user
            RequestHeader set REMOTE_USER %{REMOTE_USER}s
        </Location>
        XSendFile on
        XSendFilePath /var/moneta/media/
        # in older versions of XSendFile (<= 0.9), use XSendFileAllowAbove On
        <Location /core/p/>
            Order deny,allow
            Allow from all
            Satisfy any
        </Location>
        <Location /repo/p/>
            Order deny,allow
            Allow from all
            Satisfy any
        </Location>
    </VirtualHost>
    EOF
    sudo mkdir /var/moneta
    sudo chown -R www-data:www-data /var/moneta
    sudo a2ensite moneta.conf
    sudo apachectl -t
    sudo apachectl restart




Application
-----------

Now, it's time to install Moneta:

.. code-block:: bash

    sudo mkdir -p /var/moneta
    sudo adduser --disabled-password moneta
    sudo chown moneta:www-data /var/moneta
    sudo apt-get install virtualenvwrapper python3.5 python3.5-dev build-essential postgresql-client libpq-dev
    # application
    sudo -u moneta -i
    mkvirtualenv moneta -p `which python3.5`
    workon moneta
    pip install setuptools --upgrade
    pip install pip --upgrade
    pip install moneta psycopg2 gevent
    mkdir -p $VIRTUAL_ENV/etc/moneta
    cat << EOF > $VIRTUAL_ENV/etc/moneta/settings.ini
    [database]
    engine = django.db.backends.postgresql_psycopg2
    host = localhost
    name = moneta
    password = 5trongp4ssw0rd
    port = 5432
    user = moneta
    [global]
    admin_email = admin@moneta.example.org
    bind_address = 127.0.0.1:8131
    data_path = /var/moneta
    debug = True
    default_group = Users
    extra_apps = 
    language_code = fr-fr
    protocol = http
    remote_user_header = HTTP_REMOTE_USER
    secret_key = NEZ6ngWX0JihNG2wepl1uxY7bkPOWrTEo27vxPGlUM3eBAYfPT
    server_name = moneta.example.org
    time_zone = Europe/Paris
    x_accel_converter = False
    x_send_file = True
    [gnupg]
    home = /var/moneta/gpg
    keyid = 1DA759EA7F5EF06F
    path = gpg
    [sentry]
    dsn_url = 
    EOF
    chmod 0400 $VIRTUAL_ENV/etc/moneta/settings.ini
    # required since there are password in this file
    moneta-manage migrate
    moneta-manage collectstatic --noinput
    moneta-manage createsuperuser
    chmod 0700 /var/moneta/gpg
    moneta-manage gpg_gen generate --no-existing-keys
    KEY_ID=`moneta-manage gpg_gen show --only-id | tail -n 1`
    sed -i "s/1DA759EA7F5EF06F/$KEY_ID/" $VIRTUAL_ENV/etc/moneta/settings.ini

On VirtualBox, you may need to install rng-tools to generate enough entropy for GPG keys:

.. code-block:: bash

    sudo apt-get install rng-tools
    echo "HRNGDEVICE=/dev/urandom" | sudo tee -a /etc/default/rng-tools
    sudo /etc/init.d/rng-tools restart



supervisor
----------

Supervisor is required to automatically launch moneta:

.. code-block:: bash


    sudo apt-get install supervisor
    cat << EOF | sudo tee /etc/supervisor/conf.d/moneta.conf
    [program:moneta_gunicorn]
    command = /home/moneta/.virtualenvs/moneta/bin/moneta-gunicorn
    user = moneta
    EOF
    sudo service supervisor stop
    sudo service supervisor start

Now, Supervisor should start moneta after a reboot.


systemd
-------

You can also use systemd to launch moneta:

.. code-block:: bash

    cat << EOF | sudo tee /etc/systemd/system/moneta-gunicorn.service
    [Unit]
    Description=Moneta Gunicorn process
    After=network.target
    [Service]
    User=moneta
    Group=moneta
    WorkingDirectory=/var/moneta/
    ExecStart=/home/moneta/.virtualenvs/moneta/bin/moneta-gunicorn
    ExecReload=/bin/kill -s HUP \$MAINPID
    ExecStop=/bin/kill -s TERM \$MAINPID
    [Install]
    WantedBy=multi-user.target
    EOF
    systemctl enable moneta-gunicorn.service
    sudo service moneta-gunicorn start



