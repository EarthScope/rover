
call dev/install-py3-in-env3.bat
call env3/Scripts/Activate.bat
robot -F robot robot
call dev/make-env3.bat
