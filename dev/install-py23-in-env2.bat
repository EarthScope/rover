
call dev\make-env2.bat
call env2\Scripts\Activate.bat
call dev\translate-py3-to-py23.bat
cd ..\rover23
python setup.py install
del /q /s build
del /q /s dist
del /q rover.egg-info
cd ..\rover
