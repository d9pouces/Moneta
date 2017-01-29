{% extends 'djangofloor/dev/doc/source/installation.rst_tpl' %}
{% block post_dependencies %}
  * python-gnupg
  * rubymarshal
  * pyyaml
{% endblock %}

{% block pre_install_step %}
Ruby
----

If you want to use the Ruby mirror functionnality, Ruby is required on the server:

.. code-block:: bash

   sudo apt-get install ruby
{% endblock %}
{% block webserver_media %}{% endblock %}
{% block webserver_ssl_media %}{% endblock %}

{% block webserver_ssl_extra %}        <Location /core/p/>
            Order deny,allow
            Allow from all
            Satisfy any
        </Location>
        <Location /repo/p/>
            Order deny,allow
            Allow from all
            Satisfy any
        </Location>
{% endblock %}

{% block ini_configuration %}    [global]
    data = $HOME/{{ DF_MODULE_NAME }}
    [database]
    db = {{ DF_MODULE_NAME }}
    engine = postgresql
    host = localhost
    password = 5trongp4ssw0rd
    port = 5432
    user = {{ DF_MODULE_NAME }}
    [gnupg]
    home = /var/moneta/gpg/
    keyid = {{ GNUPG_KEYID }}
    path = gpg
{% endblock %}

{% block post_application %}    {{ processes.django }} createsuperuser
    chmod 0700 /var/moneta/gpg/
    {{ processes.django }} gpg_gen generate --absent
    KEY_ID=`{{ processes.django }} gpg_gen show --onlyid | tail -n 1`
    sed -i "s/{{ GNUPG_KEYID }}/$KEY_ID/" $VIRTUAL_ENV/etc/moneta/settings.ini

On VirtualBox, you may need to install rng-tools to generate enough entropy for GPG keys:

.. code-block:: bash

    sudo apt-get install rng-tools
    echo "HRNGDEVICE=/dev/urandom" | sudo tee -a /etc/default/rng-tools
    sudo /etc/init.d/rng-tools restart
{% endblock %}
