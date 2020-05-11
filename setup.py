from setuptools import setup, find_packages
from manheim_c7n_tools.version import VERSION, PROJECT_URL

with open('README.md') as f:
    long_description = f.read()

requires = [
    'boto3==1.12.47',
    'botocore==1.15.47',
    'docutils>=0.10,<0.16',
    'tabulate>=0.8.0,<0.9.0',
    # In order to work with the "mu" Lambda function management tool,
    # we need PyYAML 3.x, and need it as source and not a wheel
    'pyyaml',
    # @TODO Bump this to a released version once c7n-mailer > 0.6.0 is out.
    # We're pulling in this git branch in order to pull in https://github.com/cloud-custodian/cloud-custodian/pull/5708
    'c7n==0.9.1.0',
    'c7n-mailer==0.6.0',
    # for building generated policy docs
    'sphinx>=1.8.0,<1.9.0',
    'sphinx_rtd_theme',
    'm2r'
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
    name='manheim-c7n-tools',
    version=VERSION,
    author='Manheim Release Engineering',
    author_email='man-releaseengineering@manheim.com',
    packages=find_packages(),
    url=PROJECT_URL,
    description='c7n policy generation script and related utilities',
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=requires,
    keywords="custodian aws c7n policy",
    classifiers=classifiers,
    entry_points={
        'console_scripts': [
            'policygen = manheim_c7n_tools.policygen:main',
            's3-archiver = manheim_c7n_tools.s3_archiver:main',
            'dryrun-diff = manheim_c7n_tools.dryrun_diff:main',
            'mugc = manheim_c7n_tools.vendor.mugc:main',
            'manheim-c7n-runner = manheim_c7n_tools.runner:main',
            'errorscan = manheim_c7n_tools.errorscan:main'
        ]
    }
)
