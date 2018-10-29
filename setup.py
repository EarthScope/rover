
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

module_name = 'rover'

# Extract version string from code
import importlib
mod = importlib.import_module(module_name)
version = mod.__version__

setuptools.setup(
    name=module_name,
    version=version,
    author="IRIS",
    author_email="software-owner@iris.washington.edu",
    description="Tool for the robust retrieval of seismic data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://iris-edu.github.io/rover",
    packages=setuptools.find_packages(),
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
    entry_points={
        'console_scripts': [
            '%s = %s:main' % (module_name,module_name),
        ],
    },
    install_requires=[
        "requests",
        "nose",
        "future",
        "robotframework",
    ]
)
