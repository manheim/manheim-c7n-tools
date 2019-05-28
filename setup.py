from setuptools import setup, find_packages
from custodian_policygen.version import VERSION, PROJECT_URL

with open('README.rst') as f:
    long_description = f.read()

requires = [
    'c7n',
    'boto3',
    'tabulate>=0.8.0,<0.9.0',
    # In order to work with the "mu" Lambda function management tool,
    # we need PyYAML 3.x, and need it as source and not a wheel
    'pyyaml'
]

classifiers = [
    'Development Status :: 5 - Production/Stable',
    'Environment :: Console',
    'Intended Audience :: Developers',
    'Intended Audience :: Information Technology',
    'Intended Audience :: System Administrators',
    'License :: OSI Approved :: Apache Software License',
    'Natural Language :: English',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Topic :: System :: Distributed Computing',
    'Topic :: System :: Systems Administration',
    'Topic :: Utilities'
]

setup(
    name='custodian-policygen',
    version=VERSION,
    author='Manheim Release Engineering',
    author_email='man-releaseengineering@manheim.com',
    packages=find_packages(),
    url=PROJECT_URL,
    description='c7n policy generation script and related utilities',
    long_description=long_description,
    install_requires=requires,
    keywords="custodian aws c7n policy",
    classifiers=classifiers,
    entry_points={
        'console_scripts': [
            'policygen = custodian_policygen.policygen:main',
            's3-archiver = custodian_policygen.s3_archiver:main',
            'dryrun-diff = custodian_policygen.dryrun_diff:main',
            'mugc = custodian_policygen.vendor.mugc:main'
        ]
    }
)
