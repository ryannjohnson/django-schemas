import os.path
import re
from setuptools import find_packages, setup


def get_info(var):
    """Get version from the package."""
    with open(os.path.join('django_schemas','__init__.py')) as f:
        content = f.read()
    return re.search(var + r'\s*=\s*["\'](.+?)["\']', content).group(1)


VERSION = get_info('__version__')
LICENSE = get_info('__license__')


setup(
        name="django_schemas",
        description="Postgres schemas for Django.",
        url="https://github.com/ryannjohnson/django-schemas",
        license=LICENSE,
        version=VERSION,
        packages=find_packages('django_schemas'),
        classifiers=[
            'Development Status :: 3 - Alpha',
            'Environment :: Web Environment',
            'Framework :: Django :: 1.8',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
            'Programming Language :: Python :: 3.4',
        ])