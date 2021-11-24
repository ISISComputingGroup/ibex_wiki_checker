setlocal
set PYTHONIOENCODING=utf-8
set PYTHONUNBUFFERED=TRUE
del /s /q test-reports\*.xml
"%~dp0Python\python.exe" -m pip install requests
"%~dp0Python\python.exe" -m pip install mock
"%~dp0Python\python.exe" -u run_tests.py --remote
