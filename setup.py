#!/usr/bin/env python

from distutils.core import setup

setup(
      name='JSRPC',
      version='0.0.1',
      description='Python to JS RPC (via JSON)',
      author='Barney Gale',
      author_email='barney.gale@gmail.com',
      url='http://github.com/barneygale/JSRPC',
      license='BSD',
      long_description=open('README.md').read(),
      packages=['jsrpc'],
      package_data={'jsrpc': ['*.js']},
     )
