#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

requisites = []

setup(
    name='pomop',
    version='0.1.5',
    description='(Poor man) pomodoro technique for productivity',
    long_description=open('README.rst').read(),
    author='Viet Hung Nguyen',
    author_email='hvn@familug.org',
    url='https://github.com/hvnsweeting/pomop',
    packages=['pomop'],
    license='MIT',
    classifiers=[
        'Environment :: Console',
    ],
    entry_points={
        'console_scripts': [
            'pomop=pomop.pomop:cli',
        ],
    },
)
