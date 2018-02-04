Python hosting
==============

Heroku
------

First, you need to prepare your Heroku deployment, with a Redis database for efficient caching:

.. code-block:: bash

    mkdir heroku-hosting
    cd heroku-hosting
    APP_NAME=hobby-dev  # use the name of your Heroku app
    pip install pipenv
    heroku login
    heroku addons:create heroku-redis -a $APP_NAME

Now, a few files are required:

.. code-block:: bash

    # create the Pipfile for downloading and installing Moneta
    cat << EOF > Pipfile
    [[source]]
    url = "https://pypi.python.org/simple"
    verify_ssl = true
    [packages]
    moneta = '*'
    django-redis-sessions = "*"
    django-redis = "*"
    psycopg2 = "*"
    [requires]
    python_version = "3.6"
    EOF

    # create a simple manage.py for the automatic collectstatic command
    cat << EOF > manage.py
    #!/usr/bin/env python
    from djangofloor.scripts import django, set_env

    set_env(command_name='moneta-ctl')
    django()
    EOF

    cat << EOF > local_settings.ini
    [global]
    data = ./
    EOF

    # create the Procfile with required processes
    cat << EOF > Procfile
    web: moneta-ctl server
    EOF


Once deployed, you can prepare the database or open Python shell:

.. code-block:: bash

    heroku run moneta-ctl migrate
    heroku run moneta-ctl shell



Gandi
-----

Moneta must be locally installed (in a virtualenv) to prepare the deployment on a Gandi host.

.. code-block:: bash

    mkdir gandi-hosting
    pip install moneta
    cd gandi-hosting
    cat << EOF > gandi.yml
    python:
      version: 3.6
    EOF
    cat << EOF > wsgi.py
    import os
    from djangofloor.scripts import get_application

    os.environ['LC_ALL']="en_US.UTF-8"
    os.environ['LC_LANG']="en_US.UTF-8"
    application = get_application(command_name='moneta-ctl')
    EOF
    cat << EOF > requirements.txt
    moneta
    EOF
    cat << EOF > local_settings.ini
    [global]
    data = ./
    server_url = https://www.example.com/
    EOF
    moneta-ctl collectstatic --noinput
    git add .
    git commit -am 'initial commit'

