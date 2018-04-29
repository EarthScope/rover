#!/bin/bash

# this was an attempt to demonstrate the bug seen with urllib
# however, the test fails to fail!

rm -fr bug-urllib
mkdir bug-urllib
pushd bug-urllib

echo "generating python 3 virtualenv"
virtualenv-3.5 env3
source env3/bin/activate
pip install nose
pip install future
source env3/bin/activate

cat > bug-urllib-3.py <<EOF
from urllib.request import urlretrieve
urlretrieve('http://www.acooke.org', 'acooke.org.html')
EOF
echo "running native python 3 code"
python bug-urllib-3.py

echo "generating python 2 virtualenv"
virtualenv-2.7 env2
source env2/bin/activate
pip install --upgrade pip
pip install nose
pip install future
pip install backports.tempfile
source env2/bin/activate

cat > bug-urllib-2.py <<EOF
from urllib import urlretrieve
urlretrieve('http://www.acooke.org', 'acooke.org.html')
EOF
echo "running python 2 code"
python bug-urllib-2.py

echo "converting python3 to python2"
source env3/bin/activate
cp bug-urllib-3.py bug-urllib-3to2.py
pasteurize -w -n --no-diffs bug-urllib-3to2.py

echo "running 3to2 code"
source env2/bin/activate
python bug-urllib-3to2.py
