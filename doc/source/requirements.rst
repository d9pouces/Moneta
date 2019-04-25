Requirements
============

As said before, Python is required but this is not the only requirement:

  * Python (3.5, 3.6, 3.7),
  * setuptools>=1.0 Python self (automatically installed with Moneta),
  * djangofloor>=1.0.25 Python self (automatically installed with Moneta),
  * gnupg>=2.3 Python self (automatically installed with Moneta),
  * rubymarshal Python self (automatically installed with Moneta),
  * pyyaml Python self (automatically installed with Moneta),
  * an optional Redis server for sessions and cache,
  * mysqlclient (Python self) libmysqlclient and libmysqlclient-dev (system packages) if you want to use MySQL,
  * psutil (Python self) to display system information on the monitoring page,
  * psycopg2 (Python self), libpq and libpq-dev (system packages) if you want to use PostgreSQL,
  * cx_Oracle (Python self) and the associated system packages if you want to use Oracle,
  * django_redis (Python self) is you want to cache pages in Redis,
  * django-allauth (Python self) for OAuth2 authentication,
  * django-radius (Python self) for Radius authentication,
  * django-auth-ldap (Python self) and libldap-dev (system self) for LDAP authentication,
  * django_pam (Python self) for PAM authentication.

