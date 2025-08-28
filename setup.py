# -*- coding: utf-8 -*-
"""Installer for the Products.CPUtils package."""

from setuptools import find_packages
from setuptools import setup


long_description = (
    open('README.rst').read()
    + '\n\n' +
    open('CHANGES.rst').read()
    + '\n')


setup(
    name='Products.CPUtils',
    version='1.26',
    description="Some plone utilities as external methods, monkey patches, etc.",
    long_description=long_description,
    # Get more from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Development Status :: 6 - Mature",
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: 4.3",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
    ],
    keywords='plone imio utils',
    author='Stephan Geulette',
    author_email='s.geulette@imio.be',
    url='http://pypi.python.org/pypi/Products.CPUtils',
    license='GPL',
    packages=find_packages('src', exclude=['ez_setup']),
    namespace_packages=['Products'],
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'imio.helpers',
        'imio.pyutils>=1.0.0',
        'plone.api',
        'setuptools',
    ],
    extras_require={
        'test': [
            'plone.app.testing',
            'plone.app.robotframework',
            'Products.PloneGazette',
            'Products.PloneTestCase',
        ],
    },
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    """,
)
