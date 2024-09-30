setlocal
set PYTHONIOENCODING=utf-8
set PYTHONUNBUFFERED=TRUE
if exist "test-reports" del /s /q test-reports\*.xml

REM Create local python environment from genie python on share
if exist "ibex_utils" rd /q /s ibex_utils 
git clone https://github.com/ISISComputingGroup/ibex_utils.git
CALL ibex_utils\installation_and_upgrade\define_latest_genie_python.bat
@echo on
if exist "my_venv" rd /q /s my_venv 
REM this needs to be LATEST_PYTHON not LATEST_PYTHON3
echo %LATEST_PYTHON_DIR%
%LATEST_PYTHON% -m venv %~dp0my_venv
REM make a python3.exe to avoid being terminated
REM by stop_ibex_server
copy my_venv\Scripts\python.exe my_venv\Scripts\python3.exe 
CALL my_venv\Scripts\activate.bat

where python3.exe
where python311.dll

REM Clean local python environment and install requirements
python3.exe -m pip freeze --local > toberemoved.txt 
python3.exe -m pip uninstall -r toberemoved.txt -y
python3.exe -m pip install -r requirements.txt

REM run tests
python3.exe -u run_tests.py --remote

if %errorlevel% neq 0 (
    @echo ERROR: Python exited with code %errorlevel%
    CALL ibex_utils\installation_and_upgrade\remove_genie_python.bat %LATEST_PYTHON_DIR%
    EXIT /b %errorlevel%
)

CALL ibex_utils\installation_and_upgrade\remove_genie_python.bat %LATEST_PYTHON_DIR%
