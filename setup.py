import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.md')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'ott.utils',
    'ott.boundary',

    'pyramid',
    'pyramid_tm',
    'pyramid_exclog',
    'waitress',
]

extras_require = dict(
    dev=[
      '' if os.name == 'nt' or os.name == 'posix' else 'linesman'
    ],
)

setup(
    name='pelias.adapter',
    version='0.1.0',
    description='Open Transit Tools - Web API / Controller',
    long_description=README + '\n\n' + CHANGES,
    classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    author="Open Transit Tools",
    author_email="info@opentransittools.org",

    dependency_links = [
        'git+https://github.com/OpenTransitTools/utils.git#egg=ott.utils-0.1.0',
        'git+https://github.com/OpenTransitTools/boundary.git#egg=ott.boundary-0.1.0',
    ],

    license="Mozilla-derived (http://opentransittools.com)",
    url='http://opentransittools.com',
    keywords='ott, otp, services, transit',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
    extras_require=extras_require,
    tests_require=requires,
    test_suite="pelias.adapter.tests",
    entry_points="""\
        [paste.app_factory]
        main = pelias.adapter.pyramid.app:main
    """,
)
