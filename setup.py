#coding=utf-8

__author__ = 'flanker'


"""Setup file for the Moneta project.
"""

import codecs
import os.path
import ez_setup
ez_setup.use_setuptools()
from setuptools import setup, find_packages

# get README content from README.rst file
with codecs.open(os.path.join(os.path.dirname(__file__), 'README.rst'), encoding='utf-8') as fd:
    long_description = fd.read()

# get version value from VERSION file
with codecs.open(os.path.join(os.path.dirname(__file__), 'VERSION'), encoding='utf-8') as fd:
    version = fd.read().strip()
entry_points = {'console_scripts': ['moneta-manage = moneta.core.scripts:main',
                                    'moneta-gunicorn = moneta.core.scripts:gunicorn']}

setup(
    name='moneta',
    version=version,
    description='No description yet.',
    long_description=long_description,
    author='flanker',
    author_email='flanker@19pouces.net',
    license='cecill_b',
    url='',
    entry_points=entry_points,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    test_suite='moneta.tests',
    install_requires=['six', 'setuptools>=1.0', 'django>=1.7', 'gunicorn', 'django-bootstrap3',
                      'django-pipeline', 'django-grappelli', 'django-debug-toolbar', 'django-smart-selects',
                      'python-gnupg', ],
    setup_requires=['six', 'setuptools>=1.0', 'django>=1.7', 'gunicorn', 'django-bootstrap3',
                    'django-pipeline', 'django-grappelli', 'django-debug-toolbar', 'django-smart-selects',
                    'python-gnupg'],
    classifiers=[],
)
