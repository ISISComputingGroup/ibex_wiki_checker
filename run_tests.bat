set PYTHONIOENCODING=utf-8
%~dp0Python\python.exe -m pip install requests
%~dp0Python\python.exe -m pip install mock
%~dp0Python\python.exe -m pip install pyspellchecker
%~dp0Python\python.exe run_tests.py --remote
