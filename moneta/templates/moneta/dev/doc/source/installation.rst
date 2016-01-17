{% extends 'djangofloor/dev/doc/source/installation.rst' %}
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
{% block webserver_xsendfilepath %}        XSendFile on
        XSendFilePath {{ LOCAL_PATH }}/storage
        # in older versions of XSendFile (<= 0.9), use XSendFileAllowAbove On
{% endblock %}

{% block webserver_ssl_media %}{% endblock %}
{% block webserver_ssl_xsendfilepath %}        XSendFile on
        XSendFilePath {{ LOCAL_PATH }}/storage
        # in older versions of XSendFile (<= 0.9), use XSendFileAllowAbove On
{% endblock %}


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

{% block post_application %}    moneta-manage createsuperuser
    chmod 0700 /var/moneta/gpg
    moneta-manage gpg_gen generate --no-existing-keys
    KEY_ID=`moneta-manage gpg_gen show --only-id | tail -n 1`
    sed -i '' 's/{{ GNUPG_KEYID }}/$KEY_ID/' $VIRTUAL_ENV/etc/moneta/settings.ini

On VirtualBox, you may need to install rng-tools to generate enough entropy for GPG keys:

.. code-block:: bash

    sudo apt-get install rng-tools
    echo "HRNGDEVICE=/dev/urandom" | sudo tee -a /etc/default/rng-tools
    sudo /etc/init.d/rng-tools restart
{% endblock %}
