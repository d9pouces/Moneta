{% extends 'djangofloor/dev/doc/source/conf.py' %}
{% block header %}
os.environ['DJANGO_SETTINGS_MODULE'] = 'pycharm_settings'
{% endblock %}

{% block theme %}
html_theme = 'bizstyle'
{% endblock %}