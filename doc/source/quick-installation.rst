Quick installation
==================

You can quickly test Moneta, storing all data in $HOME/moneta:

.. code-block:: bash

    sudo apt-get install python3.5 python3.5-dev build-essential
    pip install moneta
    moneta-manage migrate  # create the database (SQLite by default)
    moneta-manage collectstatic --noinput  # prepare static files (CSS, JS, …)
    moneta-manage createsuperuser
    moneta-manage gpg_gen generate --absent
    KEY_ID=`moneta-manage gpg_gen show --onlyid | tail -n 1`
    CONFIG_FILENAME=`moneta-manage  config ini -v 2 | head -n 1 | grep ".ini" | cut -d '"' -f 2`
    cat << EOF > $CONFIG_FILENAME
    [gnupg]
    keyid = $KEY_ID
    EOF




You can easily change the root location for all data (SQLite database, uploaded or temp files, static files, …) by
editing the configuration file:

.. code-block:: bash

    CONFIG_FILENAME=`moneta-manage  config ini -v 2 | head -n 1 | grep ".ini" | cut -d '"' -f 2`
    # create required folders
    mkdir -p `dirname $FILENAME` $HOME/moneta
    # prepare a limited configuration file
    cat << EOF > $FILENAME
    [global]
    data = $HOME/moneta
    EOF

Of course, you must run again the `migrate` and `collectstatic` commands (or moving data to this new folder).


You can launch the server process:

.. code-block:: bash

    moneta-gunicorn
    


Then open http://127.0.0.1:8131 in your favorite browser.

You should use virtualenv or install Moneta using the `--user` option.