call dev\make-env3.bat
call env3\Scripts\Activate.bat
python setup.py install
del /q build
del /q dist
del /q rover.egg-info
echo "env3\Scripts\Activate.bat"
