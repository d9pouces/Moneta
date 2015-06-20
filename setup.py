# coding=utf-8

__author__ = 'flanker'

"""Setup file for the Moneta project.
"""

import codecs
import os.path

from setuptools import setup, find_packages

with codecs.open(os.path.join(os.path.dirname(__file__), 'README.rst'), encoding='utf-8') as fd:
    long_description = fd.read()
from moneta import __version__ as version
entry_points = {'console_scripts': ['moneta-manage = djangofloor.scripts:manage',
                                    'moneta-gunicorn = djangofloor.scripts:gunicorn']}

setup(
    name='moneta',
    version=version,
    description='Moneta is an emulator for different kinds (Aptitude/Yum/Pypi/Maven) of package repositories on the same server.',
    long_description=long_description,
    author='flanker',
    author_email='flanker@19pouces.net',
    license='cecill_b',
    url='',
    entry_points=entry_points,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=['setuptools>=1.0', 'djangofloor', 'django-grappelli', 'django-smart-selects', 'python-gnupg', ],
    setup_requires=[],
    classifiers=[],
)
