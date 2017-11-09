# https://packaging.python.org/tutorials/distributing-packages/
# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='django-diverse',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version='.'.join(map(str, __import__('eavkit').VERSION)),

    description = ('Application for extended files management,'
                   ' based on builtins File/Image Django database'
                   ' fields.'),
    long_description=long_description,

    # The project's main homepage.
    url='https://github.com/sakkada/django-diverse',

    # Author details
    author='Murat Guchetl',
    author_email='gmurka@gmail.com',

    # Choose your license
    license='MIT',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Database',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 1.9',
        'Framework :: Django :: 1.10',
        'Framework :: Django :: 1.11',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],

    # What does your project relate to?
    keywords='django form model fields files images versions',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    #   packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    packages=[
        'diverse',
        'diverse.fields',
        'diverse.processors',
        'diverse.processors.imagekit',
    ],

    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=['django>=1.8.0,<=1.11.99',],

    # Extras (optional features with their own dependencies)
    extras_require={'pilkit': ['pilkit',],},

    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, <4',
)
