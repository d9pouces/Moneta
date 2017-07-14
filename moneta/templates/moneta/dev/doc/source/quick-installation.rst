{% extends 'djangofloor/dev/doc/source/quick-installation.rst' %}

{% block post_application %}    {{ processes.django }} createsuperuser

{% endblock %}
