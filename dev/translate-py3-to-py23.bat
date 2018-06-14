
call env3\Scripts\Activate.bat

cd ..
rmdir /q /s rover23
mkdir rover23
xcopy /s /e /i rover\rover rover23\rover
xcopy /s /e /i rover\tests rover23\tests

cd rover23
pasteurize -w -n --no-diffs .
cd ..

xcopy /s /e /i rover\docs rover23\docs
xcopy rover\setup.py rover23
xcopy rover\README.md rover23
xcopy rover\LICENSE rover23

cd rover23
del /q /s *.pyc
rmdir /q /s rover23\__pycache__
cd ..
cd rover
