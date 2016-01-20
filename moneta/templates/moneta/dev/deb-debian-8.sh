{% extends "djangofloor/dev/deb-debian-8.sh" %}
{% block extra_dependencies %}sudo apt-get install --yes python3-gnupg
{% endblock %}