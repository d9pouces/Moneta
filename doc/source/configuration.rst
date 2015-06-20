Complete configuration
======================

You can look current settings with the following command::

    moneta-manage config

Here is the complete list of settings::

    [global]
    server_name = moneta.19pouces.net
    protocol = https
    bind_address = 127.0.0.1:8129
    data_path = /var/updoc
    admin_email = admin@updoc.19pouces.net
    time_zone = Europe/Paris
    language_code = fr-fr
    x_send_file =  true
    x_accel_converter = false
    public_bookmarks = true
    public_proxies = true
    public_index = true
    public_docs = true
    remote_user_header = HTTP_REMOTE_USER

    [database]
    engine =
    name =
    user =
    password =
    host =
    port =

If you need more complex settings, you can override default values (given in `djangofloor.defaults` and `moneta.defaults`) by creating a file named `[prefix]/etc/moneta/settings.py`.
