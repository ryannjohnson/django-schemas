import os
import os.path
import re
from setuptools import setup


def get_info(var):
    """Get version from the package."""
    with open(os.path.join('django_schemas','__init__.py')) as f:
        content = f.read()
    return re.search(var + r'\s*=\s*["\'](.+?)["\']', content).group(1)


def get_packages(package):
    """
    Taken from https://github.com/tomchristie/django-rest-framework/blob/master/setup.py
    """
    return [dirpath
            for dirpath, dirnames, filenames in os.walk(package)
            if os.path.exists(os.path.join(dirpath, '__init__.py'))]


def get_package_data(package):
    """
    Taken from https://github.com/tomchristie/django-rest-framework/blob/master/setup.py
    """
    walk = [(dirpath.replace(package + os.sep, '', 1), filenames)
            for dirpath, dirnames, filenames in os.walk(package)
            if not os.path.exists(os.path.join(dirpath, '__init__.py'))]

    filepaths = []
    for base, filenames in walk:
        filepaths.extend([os.path.join(base, filename)
                          for filename in filenames])
    return {package: filepaths}


VERSION = get_info('__version__')
LICENSE = get_info('__license__')


setup(
        name="django_schemas",
        description="Postgres schemas for Django.",
        url="https://github.com/ryannjohnson/django-schemas",
        license=LICENSE,
        version=VERSION,
        packages=get_packages('django_schemas'),
        classifiers=[
            'Development Status :: 4 - Beta',
            'Environment :: Web Environment',
            'Framework :: Django :: 1.9',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
        ],
        install_requires=[
            'Django >= 1.9.0',
            'psycopg2',
        ])