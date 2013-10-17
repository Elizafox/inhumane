#!/usr/bin/env python3
# coding: UTF-8
#
# Copyright © 2012, Elizabeth J. Myers, et al. All rights reserved.
# License terms can be found in the LICENSE file at the top level of the source
# tree.

from setuptools import setup, find_packages

PKGNAME='inhumane'

setup(name=PKGNAME,
      description='A game engine for the popular card game, Cards Against Humanity',
      author='Elizabeth Myers',
      author_email='elizabeth@interlinked.me',
      url='http://github.com/Elizacat/inhumane',
      license='BSD',
      version='0.01-alpha',
      keywords=['cards against humanity', 'game', 'game engine'],
      packages=find_packages(),
      include_package_data = True,
      setup_requires = [ "setuptools_git >= 0.3", ],
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Developers',
          'License :: Public Domain',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 3',
          'Topic :: Games/Entertainment',
          'Topic :: Games/Entertainment :: Turn Based Strategy',
          'Topic :: Software Development :: Libraries :: Python Modules',
      ]
)
