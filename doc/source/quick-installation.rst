Quick installation
==================

Moneta mainly requires Python (3.5, 3.6, 3.7).

You should create a dedicated virtualenvironment on your system to isolate Moneta.
You can use `pipenv <http://docs.python-guide.org/en/latest/dev/virtualenvs/>`_ or `virtualenvwrapper <https://virtualenvwrapper.readthedocs.io>`_.

For example, on Debian-based systems like Ubuntu:

.. code-block:: bash

    sudo apt-get install python3.6 python3.6-dev build-essential
    sudo apt-get install ruby  # required for Ruby mirrors





On VirtualBox, you may need to install rng-tools to generate enough entropy for GPG keys (otherwise the generation will be very slow):

.. code-block:: bash

    sudo apt-get install rng-tools
    echo "HRNGDEVICE=/dev/urandom" | sudo tee -a /etc/default/rng-tools
    sudo /etc/init.d/rng-tools restart


If these requirements are fullfilled, then you can gon on and install Moneta:

.. code-block:: bash

    pip install moneta --user
    moneta-ctl collectstatic --noinput  # prepare static files (CSS, JS, …)
    moneta-ctl migrate  # create the database (SQLite by default)
    moneta-ctl createsuperuser  # create an admin user
    moneta-ctl check  # everything should be ok




You can easily change the root location for all data (SQLite database, uploaded or temp files, static files, …) by
editing the configuration file.

.. code-block:: bash

    CONFIG_FILENAME=`moneta-ctl config ini -v 2 | grep -m 1 ' - .ini file' | cut -d '"' -f 2`
    # prepare a limited configuration file
    cat << EOF > $FILENAME
    [global]
    data = $HOME/moneta
    EOF

Of course, you must run again the `migrate` and `collectstatic` commands (or moving data to this new folder).




You can launch the server process:

.. code-block:: bash

    moneta-ctl server


Then open http://127.0.0.1:8131 with your favorite browser.



You can install Moneta in your home (with the `--user` option), globally (without this option), or (preferably)
inside a virtualenv.
