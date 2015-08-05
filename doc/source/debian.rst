Debian Installation
===================

By default, Moneta is only packaged as a standard Python project, downloadable from `Pypi <https://pypi.python.org>`_.
However, you can create pure Debian packages with `DjangoFloor <http://django-floor.readthedocs.org/en/latest/packaging.html#debian-ubuntu>`_.

The source code provides several Bash scripts:

    * `debian-7-python3.sh`,
    * `debian-8-python3.sh`,
    * `ubuntu-14.04-15.04.sh`.

These scripts are designed to run on basic installation and are split in five steps:

    * update system and install missing packages,
    * create a virtualenv and install all dependencies,
    * package all dependencies,
    * package Moneta,
    * install all packages and Moneta, prepare a simple configuration to test.

If everything is ok, you can copy all the .deb packages to your private mirror or to the destination server.
The configuration is set in `/etc/moneta/settings.ini`.
By default, Moneta is installed with Apache 2.2 (or 2.4) and Supervisor.
You can switch to Nginx or Systemd by tweaking the right `stdeb-XXX.cfg` file.

After installation and configuration, do not forget to create a superuser:

.. code-block:: bash

    sudo -u moneta moneta-manage createsuperuser
