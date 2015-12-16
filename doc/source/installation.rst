Installing / Upgrading
======================

Here is a simple tutorial to install moneta on a basic Debian/Linux installation.
You should easily adapt it on a different Linux or Unix flavor.

Let's start by defining some variables:

.. code-block:: bash

    SERVICE_NAME=moneta.example.com

Database
--------

PostgreSQL is often a good choice for Django sites:

.. code-block:: bash

   sudo apt-get install postgresql
   echo "CREATE USER moneta" | sudo -u postgres psql -d postgres
   echo "ALTER USER moneta WITH ENCRYPTED PASSWORD 'upd0c-5trongp4ssw0rd'" | sudo -u postgres psql -d postgres
   echo "ALTER ROLE moneta CREATEDB" | sudo -u postgres psql -d postgres
   echo "CREATE DATABASE moneta OWNER moneta" | sudo -u postgres psql -d postgres

Ruby
----

If you want to use the Ruby mirror functionnality, Ruby is required on the server:

.. code-block:: bash

   sudo apt-get install ruby

Apache
------

I only present the installation with Apache, but an installation behind nginx should be similar.

.. code-block:: bash

    sudo apt-get install apache2 libapache2-mod-xsendfile
    sudo a2enmod headers proxy proxy_http
    sudo a2dissite 000-default.conf
    # sudo a2dissite 000-default on Debian7
    SERVICE_NAME=moneta.example.com
    cat << EOF | sudo tee /etc/apache2/sites-available/moneta.conf
    <VirtualHost *:80>
        ServerName $SERVICE_NAME
        Alias /static/ /var/moneta/static/
        Alias /media/ /var/moneta/media/
        ProxyPass /static/ !
        ProxyPass /media/ !
        ProxyPass / http://localhost:8129/
        ProxyPassReverse / http://localhost:8129/
        DocumentRoot /var/moneta/
        ProxyIOBufferSize 65536
        ServerSignature off
        XSendFile on
        XSendFilePath /var/moneta/storage/
        # in older versions of XSendFile (<= 0.9), use XSendFileAllowAbove On
        <Location /static/>
            Order deny,allow
            Allow from all
            Satisfy any
        </Location>
    </VirtualHost>
    EOF
    sudo mkdir /var/moneta/
    sudo chown -R www-data:www-data /var/moneta/
    sudo a2ensite moneta.conf
    sudo apachectl -t
    sudo apachectl restart

If you want Kerberos authentication and SSL:

.. code-block:: bash

    sudo apt-get install apache2 libapache2-mod-xsendfile libapache2-mod-auth-kerb
    PEM=/etc/apache2/`hostname -f`.pem
    KEYTAB=/etc/apache2/http.`hostname -f`.keytab
    # ok, I assume that you already have your certificate and your keytab
    sudo a2enmod auth_kerb headers proxy proxy_http ssl
    openssl x509 -text -noout < $PEM
    cat << EOF | sudo ktutil
    rkt $KEYTAB
    list
    quit
    EOF
    sudo chown www-data $PEM $KEYTAB
    sudo chmod 0400 $PEM $KEYTAB

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
        Alias /media/ /var/moneta/media/
        ProxyPass /static/ !
        ProxyPass /media/ !
        ProxyPass / http://localhost:8129/
        ProxyPassReverse / http://localhost:8129/
        DocumentRoot /var/moneta/
        ProxyIOBufferSize 65536
        ServerSignature off
        RequestHeader set X_FORWARDED_PROTO https
        <Location />
            Options +FollowSymLinks +Indexes
            AuthType Kerberos
            AuthName "moneta"
            KrbAuthRealms INTRANET.com interne.com
            Krb5Keytab $KEYTAB
            KrbLocalUserMapping On
            KrbServiceName HTTP
            KrbMethodK5Passwd Off
            KrbMethodNegotiate On
            KrbSaveCredentials On
            Require valid-user
            RequestHeader set REMOTE_USER %{REMOTE_USER}s
        </Location>
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
        XSendFile on
        XSendFilePath /var/moneta/storage/
        # in older versions of XSendFile (<= 0.9), use XSendFileAllowAbove On
        <Location /static/>
            Order deny,allow
            Allow from all
            Satisfy any
        </Location>
    </VirtualHost>
    EOF
    sudo mkdir /var/moneta/
    sudo chown -R www-data:www-data /var/moneta/
    sudo a2ensite moneta.conf
    sudo apachectl -t
    sudo apachectl restart



Application
-----------

Now, it's time to install moneta (use Python3.2 on Debian 7):

.. code-block:: bash

    sudo mkdir -p /var/moneta
    sudo adduser --disabled-password moneta
    sudo chown moneta:www-data /var/moneta
    sudo apt-get install virtualenvwrapper python3.4 python3.4-dev build-essential postgresql-client libpq-dev
    # application
    sudo -u moneta -i
    SERVICE_NAME=moneta.example.com
    mkvirtualenv moneta -p `which python3.4`
    workon moneta
    pip install setuptools --upgrade
    pip install pip --upgrade
    pip install moneta psycopg2
    mkdir -p $VIRTUAL_ENV/etc/moneta
    cat << EOF > $VIRTUAL_ENV/etc/moneta/settings.ini
    [global]
    server_name = $SERVICE_NAME
    protocol = http
    ; use https if your Apache uses SSL
    bind_address = 127.0.0.1:8129
    data_path = /var/moneta
    admin_email = admin@$SERVICE_NAME
    time_zone = Europe/Paris
    language_code = fr-fr
    x_send_file =  true
    x_accel_converter = false
    remote_user_header = HTTP_REMOTE_USER
    ; leave it blank if you do not use kerberos

    [database]
    engine = django.db.backends.postgresql_psycopg2
    name = moneta
    user = moneta
    password = upd0c-5trongp4ssw0rd
    host = localhost
    port = 5432
    EOF

    moneta-manage migrate
    moneta-manage collectstatic --noinput
    moneta-manage createsuperuser
    chmod 0700 /var/moneta/gpg
    moneta-manage gpg_gen generate --no-existing-keys
    KEY_ID=`moneta-manage gpg_gen show --only-id | tail -n 1 | cut -f 4 -d ' ' | cut -f 1 -d ','`
    cat << EOF >> $VIRTUAL_ENV/etc/moneta/settings.ini
    [gnupg]
    keyid = $KEY_ID
    EOF


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
    sudo /etc/init.d/supervisor restart

Now, Supervisor should start moneta after a reboot.
