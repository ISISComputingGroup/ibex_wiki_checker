setlocal
set PYTHONIOENCODING=utf-8
set PYTHONUNBUFFERED=TRUE
if exist "test-reports" del /s /q test-reports\*.xml

REM Create local python environment from genie python on share
if exist "ibex_utils" rd /q /s ibex_utils 
git clone https://github.com/ISISComputingGroup/ibex_utils.git
CALL ibex_utils\installation_and_upgrade\define_latest_genie_python.bat
@echo on
%LATEST_PYTHON% -m venv venv
CALL venv\Scripts\activate.bat

REM Clean local python environment and install requirements
python -m pip freeze --local > toberemoved.txt 
python -m pip uninstall -r toberemoved.txt -y
python -m pip install -r requirements.txt

REM make a python3.exe to avoid being terminated
REM by stop_ibex_server
copy venv\Scripts\python.exe venv\Scripts\python3.exe 
REM run tests
python3 -u run_tests.py --remote
