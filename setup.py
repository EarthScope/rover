# For reference: https://github.com/pypa/sampleproject/blob/master/setup.cfg

from setuptools import setup, find_packages
from os import path
from io import open

module_name = 'rover'

here = path.abspath(path.dirname(__file__))

with open(path.join(here, "README.md"), encoding='utf-8') as fh:
    long_description = fh.read()

with open(path.join(here, module_name, 'VERSION')) as vf:
    version = vf.read().strip()

setup(
    name=module_name,
    version=version,
    author="IRIS",
    author_email="software-owner@iris.washington.edu",
    description="Tool for the robust retrieval of seismic data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://iris-edu.github.io/rover",
    packages=find_packages(),
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, <4',
    classifiers=(
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: Unix",
        "Operating System :: MacOS",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ),
    install_requires=["requests", "future"],
    extras_require={
        'dev': ["nose", "robotframework"]
    },
    entry_points={
        'console_scripts': [
            '%s = %s:main' % (module_name,module_name),
        ],
    }
)
