
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="rover",
    version="0.0.0",
    author="IRIS",
    author_email="software-owner@iris.washington.edu",
    description="Retrieval of Various Experiment data Robustly",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/iris-edu/rover",
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
            'rover = rover:main',
        ],
    },
    install_requires=[
        "requests",
        "nose",
        "future",
        "robotframework",
    ]
)
