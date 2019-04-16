# For reference: https://github.com/pypa/sampleproject/blob/master/setup.py

from setuptools import setup, find_packages
from setuptools.command.install import install
from setuptools.command.develop import develop
from io import open
from tempfile import gettempdir
import subprocess
import os
import sys
import zipfile
import glob
import shutil

module_name = 'rover'

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "README.md"), encoding='utf-8') as fh:
    long_description = fh.read()

with open(os.path.join(here, module_name, 'VERSION')) as vf:
    version = vf.read().strip()

# python 2 / 3 compatibility
try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen
    

class InstallBase():
    
    def get_virtualenv_path(self):
        """Used to work out path to install compiled binaries to."""
        return os.path.join(sys.prefix, 'bin')

    def download_mseedindex(self):
        # download mseed index zip ball
        url = 'https://api.github.com/repos/iris-edu/mseedindex/zipball'
        temp_dir = gettempdir()
        mseed_index_zip = os.path.join(temp_dir, "mseedindex.zip")
        f = urlopen(url)
        data = f.read()
        with open(mseed_index_zip, "wb") as fd:
            fd.write(data)
        # extract zip in system temporary directory
        zip_ref = zipfile.ZipFile(mseed_index_zip, 'r')
        exract_path = os.path.join(temp_dir, 'mseedindex')
        zip_ref.extractall(exract_path)
        zip_ref.close()
        # return extracted zip file
        return glob.glob(os.path.join(exract_path, '*'))[0]
    
    def compile_and_install_mseedindex(self, mseedindex_path):
        """Used the subprocess module to compile/install mseedindex."""
        # compile the software
        cmd = "WITHOUTPOSTGRESQL=1 CFLAGS='-O2' make"
        subprocess.check_call(cmd, cwd=mseedindex_path, shell=True)
        
        venv = self.get_virtualenv_path()
        mseedindex_binary = os.path.join(mseedindex_path, 'mseedindex')
        mseedindex_binary_dest = os.path.join(venv, 'mseedindex')
        shutil.copy(mseedindex_binary, mseedindex_binary_dest)
        return mseedindex_binary_dest

    def install_mseedindex(self):
        try:
            mseedindex_path = self.download_mseedindex()
            mseedindex_binary = self.compile_and_install_mseedindex(
                                                        mseedindex_path)
            print("Successfully installed mseedindex at {}"
                  .format(mseedindex_binary))
        except Exception as e:
            raise Exception("Failed to install mseedindex - {}"
                            .format(e))


class DevelopMSeedIndex(develop, InstallBase):
    user_options = develop.user_options + [
        ('mseedindex', None, 'Automatically install mseedindex.'),
    ]

    def initialize_options(self):
        develop.initialize_options(self)
        self.mseedindex = None

    def run(self):
        if self.mseedindex:
            self.install_mseedindex()
        develop.run(self)


class InstallMSeedIndex(install, InstallBase):
    user_options = install.user_options + [
        ('mseedindex', None, 'Automatically install mseedindex.'),
    ]

    def initialize_options(self):
        install.initialize_options(self)
        self.mseedindex = None

    def run(self):
        if self.mseedindex:
            self.install_mseedindex()
        install.run(self)


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
    },
    package_data={
        module_name: ['VERSION']
    },
    cmdclass={'install': InstallMSeedIndex,
              'develop': DevelopMSeedIndex},
)
