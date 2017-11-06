"""Setup file for the Moneta project.
"""
import re
import codecs
import os.path
from setuptools import setup, find_packages

__author__ = 'flanker'


with codecs.open(os.path.join(os.path.dirname(__file__), 'README.md'), encoding='utf-8') as fd:
    long_description = fd.read()
version = None
for line in codecs.open(os.path.join('moneta', '__init__.py'), 'r', encoding='utf-8'):
    matcher = re.match(r"""^__version__\s*=\s*['"](.*)['"]\s*$""", line)
    version = version or matcher and matcher.group(1)

entry_points = {'console_scripts': ['moneta-ctl = djangofloor.scripts:control']}

setup(
    name='moneta',
    version=version,
    description='Emulator for different kinds (Debian/Yum/Pypi/Maven/…) of package repositories on the same server.',
    long_description=long_description,
    author='flanker',
    author_email='flanker@19pouces.net',
    license='CeCILL-B',
    url='https://moneta.readthedocs.io/',
    entry_points=entry_points,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=['setuptools>=1.0', 'djangofloor>=1.0.25', 'python-gnupg', 'rubymarshal', 'pyyaml', 'gunicorn'],
    setup_requires=[],
    classifiers=[],
)
