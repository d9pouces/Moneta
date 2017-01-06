{% extends 'djangofloor/dev/doc/source/quick-installation.rst' %}

{% block post_application %}    {{ processes.django }} createsuperuser
    {{ processes.django }} gpg_gen generate --absent
    KEY_ID=`{{ processes.django }} gpg_gen show --onlyid | tail -n 1`
    CONFIG_FILENAME=`{{ processes.django }}  config ini -v 2 | head -n 1 | grep ".ini" | cut -d '"' -f 2`
    cat << EOF > $CONFIG_FILENAME
    [gnupg]
    keyid = $KEY_ID
    EOF

{% endblock %}
