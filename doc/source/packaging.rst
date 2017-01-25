Debian Installation
===================

By default, Moneta is only packaged as a standard Python project, downloadable from `Pypi <https://pypi.python.org>`_.
However, you can create pure Debian packages with `DjangoFloor <http://django-floor.readthedocs.org/en/latest/packaging.html#debian-ubuntu>`_.

The source code provides one Bash scripts,  `deb-debian-8_ubuntu-14.10-150.10.sh`.

This script is designed to run on basic installation and are split in five steps:

    * update system and install missing packages,
    * create a virtualenv and install all dependencies,
    * package all dependencies,
    * package Moneta,
    * install all packages and Moneta, prepare a simple configuration to test.

If everything is ok, you can copy all the .deb packages to your private mirror or to the destination server.
By default, Moneta is installed with Apache 2.4 and systemd.
You can switch to Nginx or supervisor by tweaking the right `stdeb-XXX.cfg` file.


Configuration
-------------

Default configuration file is `/moneta/settings.ini`.
If you need more complex settings, you can override default values (given in `djangofloor.defaults` and
`moneta.defaults`) by creating a file named `/moneta/settings.py`.
After any change in the database configuration or any upgrade, you must migrate the database to create the required tables.

.. code-block:: bash

    sudo -u moneta moneta-manage migrate


After installation and configuration, do not forget to create a superuser:

.. code-block:: bash

    sudo -u moneta moneta-manage createsuperuser





Launch the service
------------------

The service can be stopped or started via the `service` command. By default, Moneta is not started.

.. code-block:: bash

    sudo service moneta-gunicorn start


If you want Moneta to be started at startup, you have to enable it in systemd:

.. code-block:: bash

    systemctl enable moneta-gunicorn.service


