{% extends 'djangofloor/dev/doc/source/index.rst_tpl' %}

{% block description %}
Moneta is a web application emulating different kinds of package repositories.
The goal is not to replace official mirrors like packages.debian.org or mirror.centos.org, but to have a single location
for all your Python/Java/Debian/RedHat private packages.

Repositories are created on-the-fly and you can limit upload rights to some groups of users.

Currently, you can create the following types of repositories:

    * Aptitude for Ubuntu or Debian systems,
    * Yum for CentOS, Fedora or Red Hat systems,
    * Maven for Java or Scala packages,
    * Pypi for Python packages,
    * Jetbrains for IntelliJ/PyCharm/PhpStorm/RubyMine/AppCode/Clion plugins,
    * Gem for Ruby packages,
    * Vagrant for boxes,
    * any binary, versionned files.

{% endblock %}

{% block screenshots %}
.. image:: _static/index.png

.. image:: _static/apt.png

.. image:: _static/package.png
{% endblock %}
