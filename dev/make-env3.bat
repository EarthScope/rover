rmdir /q /s env3
virtualenv env3
call env3\Scripts\Activate.bat
pip install --upgrade pip
pip install requests
pip install nose
pip install future
pip install robotframework
pip install setuptools

echo "env3\Scripts\Activate.bat"
