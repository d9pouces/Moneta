Installation
============

Here is a simple tutorial to install Moneta on a basic Debian/Linux installation.
You should easily adapt it on a different Linux or Unix flavor.

Like many Python packages, you can use several methods to install Moneta.
Of course you can install it from source, but the preferred way is to install it as a standard Python package, via pip.


Upgrading
---------

If you want to upgrade an existing installation, just install the new version (with the `--upgrade` flag for `pip`) and run
the `collectstatic` and `migrate` commands (for updating both static files and the database).


Ruby
----

If you want to use the Ruby mirror functionnality, Ruby is required on the server:

.. code-block:: bash

   sudo apt-get install ruby


Preparing the environment
-------------------------

.. code-block:: bash

    sudo adduser --disabled-password moneta
    sudo chown moneta:www-data $DATA_ROOT
    sudo apt-get install virtualenvwrapper python3.6 python3.6-dev build-essential postgresql-client libpq-dev
    sudo -u moneta -H -i
    mkvirtualenv moneta -p `which python3.6`
    workon moneta


Database
--------

PostgreSQL is often a good choice for Django sites:

.. code-block:: bash

   sudo apt-get install postgresql
   echo "CREATE USER moneta" | sudo -u postgres psql -d postgres
   echo "ALTER USER moneta WITH ENCRYPTED PASSWORD '5trongp4ssw0rd'" | sudo -u postgres psql -d postgres
   echo "ALTER ROLE moneta CREATEDB" | sudo -u postgres psql -d postgres
   echo "CREATE DATABASE moneta OWNER moneta" | sudo -u postgres psql -d postgres


Moneta can use Redis for caching pages and storing sessions:

.. code-block:: bash

    sudo apt-get install redis-server





Apache
------

Only the Apache installation is presented, but an installation behind nginx should be similar.
Only the chosen server name (like `moneta.example.org`) can be used for accessing your site. For example, you cannot use its IP address.



.. code-block:: bash

    SERVICE_NAME=moneta.example.org
    sudo apt-get install apache2 libapache2-mod-xsendfile
    sudo a2enmod headers proxy proxy_http xsendfile
    sudo a2dissite 000-default.conf
    # sudo a2dissite 000-default on Debian7
    cat << EOF | sudo tee /etc/apache2/sites-available/moneta.conf
    <VirtualHost *:80>
        ServerName $SERVICE_NAME
        Alias /static/ $DATA_ROOT/static/
        ProxyPass /static/ !
        <Location /static/>
            Order deny,allow
            Allow from all
            Satisfy any
        </Location>
        # CAUTION: THE FOLLOWING LINES ALLOW PUBLIC ACCESS TO ANY UPLOADED CONTENT
        Alias /media/ $DATA_ROOT/media/
        # the right value is provided by "moneta-ctl config python | grep MEDIA_ROOT"
        ProxyPass /media/ !
        <Location /media/>
            Order deny,allow
            Allow from all
            Satisfy any
        </Location>
        ProxyPass / http://127.0.0.1:8131/
        ProxyPassReverse / http://127.0.0.1:8131/
        DocumentRoot $DATA_ROOT/static/
        # the right value is provided by "moneta-ctl config python | grep STATIC_ROOT"
        ServerSignature off
        # the optional two following lines are useful
        # for keeping uploaded content  private with good performance
        XSendFile on
        XSendFilePath $DATA_ROOT/media/
        # the right value is provided by "moneta-ctl config python | grep MEDIA_ROOT"
        # in older versions of XSendFile (<= 0.9), use XSendFileAllowAbove On
    </VirtualHost>
    EOF
    sudo mkdir $DATA_ROOT
    sudo chown -R www-data:www-data $DATA_ROOT
    sudo a2ensite moneta.conf
    sudo apachectl -t
    sudo apachectl restart





If you want HTTP authentication, be sure to ensure that `/core/p/` and `/repo/p/` are publicly available.
These URLs are used by packaging tools that do not use such authentication.



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
        Alias /static/ $DATA_ROOT/static/
        ProxyPass /static/ !
        <Location /static/>
            Order deny,allow
            Allow from all
            Satisfy any
        </Location>
        # CAUTION: THE FOLLOWING LINES ALLOW PUBLIC ACCESS TO ANY UPLOADED CONTENT
        Alias /media/ $DATA_ROOT/media/
        # the right value is provided by "moneta-ctl config python | grep MEDIA_ROOT"
        ProxyPass /media/ !
        <Location /media/>
            Order deny,allow
            Allow from all
            Satisfy any
        </Location>
        ProxyPass / http://127.0.0.1:8131/
        ProxyPassReverse / http://127.0.0.1:8131/
        DocumentRoot $DATA_ROOT/static/
        # the right value is provided by "moneta-ctl config python | grep STATIC_ROOT"
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
        # the optional two following lines are useful
        # for private uploaded content and good performance
        XSendFile on
        XSendFilePath $DATA_ROOT/media/
        # the right value is provided by "moneta-ctl config python | grep MEDIA_ROOT"
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
    sudo mkdir $DATA_ROOT
    sudo chown -R www-data:www-data $DATA_ROOT
    sudo a2ensite moneta.conf
    sudo apachectl -t
    sudo apachectl restart




Application
-----------

Now, it's time to install Moneta:

.. code-block:: bash

    pip install setuptools --upgrade
    pip install pip --upgrade
    pip install moneta psycopg2
    mkdir -p $VIRTUAL_ENV/etc/moneta
    cat << EOF > $VIRTUAL_ENV/etc/moneta/settings.ini
    [global]
    data = $HOME/moneta
    [database]
    db = moneta
    engine = postgresql
    host = localhost
    password = 5trongp4ssw0rd
    port = 5432
    user = moneta
    EOF
    chmod 0400 $VIRTUAL_ENV/etc/moneta/settings.ini
    # protect passwords in the config files from by being readable by everyone
    moneta-ctl collectstatic --noinput
    moneta-ctl migrate
    moneta-ctl createsuperuser


On VirtualBox, you may need to install rng-tools to generate enough entropy for GPG keys:

.. code-block:: bash

    sudo apt-get install rng-tools
    echo "HRNGDEVICE=/dev/urandom" | sudo tee -a /etc/default/rng-tools
    sudo service rng-tools restart



supervisor
----------

Supervisor can be used to automatically launch moneta:

.. code-block:: bash


    sudo apt-get install supervisor
    cat << EOF | sudo tee /etc/supervisor/conf.d/moneta.conf
    [program:moneta_aiohttp]
    command = $VIRTUAL_ENV/bin/moneta-ctl server
    user = moneta
    EOF
    sudo service supervisor stop
    sudo service supervisor start

Now, Supervisor should start moneta after a reboot.


systemd
-------

You can also use systemd in most modern Linux distributions to launch moneta:

.. code-block:: bash

    cat << EOF | sudo tee /etc/systemd/system/moneta-web.service
    [Unit]
    Description=Moneta web process
    After=network.target

    [Service]
    User=moneta
    Group=moneta
    WorkingDirectory=$DATA_ROOT/
    ExecStart=$VIRTUAL_ENV/bin/moneta-ctl server
    ExecReload=/bin/kill -s HUP \$MAINPID
    ExecStop=/bin/kill -s TERM \$MAINPID
    Restart=on-failure

    [Install]
    WantedBy=multi-user.target
    EOF
    systemctl enable moneta-web.service
    sudo service moneta-web



