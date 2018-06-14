rmdir /q /s env2
virtualenv -p C:\Python27\python.exe env2
call env2\Scripts\Activate.bat
pip install --upgrade pip
pip install requests
pip install nose
pip install future
pip install robotframework
pip install backports.tempfile

echo "env2\Scripts\Activate.bat"
