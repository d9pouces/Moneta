import subprocess
from django.test import TestCase
import io
import pkg_resources
import yaml
from moneta.repositories.ruby import RubyLoader, RubyGem
from moneta.repositories.tests import RepositoryTestCase

__author__ = 'Matthieu Gallet'

metadata = """--- !ruby/object:Gem::Specification
name: m
version: !ruby/object:Gem::Version
  version: 1.4.0
platform: ruby
authors:
- Nick Quaranto
autorequire:
bindir: bin
cert_chain: []
date: 2015-09-27 00:00:00.000000000 Z
dependencies:
- !ruby/object:Gem::Dependency
  name: method_source
  requirement: !ruby/object:Gem::Requirement
    requirements:
    - - ">="
      - !ruby/object:Gem::Version
        version: 0.6.7
  type: :runtime
  prerelease: false
  version_requirements: !ruby/object:Gem::Requirement
    requirements:
    - - ">="
      - !ruby/object:Gem::Version
        version: 0.6.7
- !ruby/object:Gem::Dependency
  name: appraisal
  requirement: !ruby/object:Gem::Requirement
    requirements:
    - - ">="
      - !ruby/object:Gem::Version
        version: '0'
  type: :development
  prerelease: false
  version_requirements: !ruby/object:Gem::Requirement
    requirements:
    - - ">="
      - !ruby/object:Gem::Version
        version: '0'
description: Run test/unit tests by line number. Metal!
email:
- nick@quaran.to
executables:
- m
extensions: []
extra_rdoc_files: []
files:
- Appraisals
- Gemfile
- Gemfile.lock
- LICENSE
homepage: https://github.com/qrush/m
licenses: []
metadata: {}
post_install_message:
rdoc_options: []
require_paths:
- lib
required_ruby_version: !ruby/object:Gem::Requirement
  requirements:
  - - ">="
    - !ruby/object:Gem::Version
      version: '1.9'
required_rubygems_version: !ruby/object:Gem::Requirement
  requirements:
  - - ">="
    - !ruby/object:Gem::Version
      version: '0'
requirements: []
rubyforge_project:
rubygems_version: 2.4.8
signing_key:
specification_version: 4
summary: Run test/unit tests by line number. Metal!
test_files:
- test/Rakefile
- test/active_support_test.rb
"""


class TestMetadata(TestCase):

    def test_metadata(self):
        stream = io.BytesIO(metadata.encode('utf-8'))
        values = yaml.load(stream, Loader=RubyLoader)
        self.assertEqual('2.4.8', values.values['rubygems_version'])


class TestRubyScript(TestCase):

    def test_script(self):
        filename = pkg_resources.resource_filename('moneta.repositories', 'ruby.rb')
        # p = subprocess.Popen(['ruby'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        # p.communicate()


class TestRubyGem(RepositoryTestCase):

    def test_add_file(self):
        repo = self.create_repository(RubyGem)
        filename = pkg_resources.resource_filename('moneta.repositories.tests', 'm-1.4.0.gem')
        self.add_file_to_repository(repo, filename)

    def test_add_file_2(self):
        repo = self.create_repository(RubyGem)
        filename = pkg_resources.resource_filename('moneta.repositories.tests', 'method_source-0.8.2.gem')
        self.add_file_to_repository(repo, filename)

    def test_generate_index(self):
        repo = self.create_repository(RubyGem)
        filename = pkg_resources.resource_filename('moneta.repositories.tests', 'm-1.4.0.gem')
        self.add_file_to_repository(repo, filename)
        filename = pkg_resources.resource_filename('moneta.repositories.tests', 'method_source-0.8.2.gem')
        self.add_file_to_repository(repo, filename)
        ruby = RubyGem()
        ruby.generate_indexes(repo)
