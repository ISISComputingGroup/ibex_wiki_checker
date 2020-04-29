# ibex_wiki_checker

> Note that there is a shell script `sort.sh` which takes `words.txt`, forces all lines to lower case, and sorts alphabetically. This allows one to add new words anywhere, in any case without causing any issues. Ideally should be made a githook 

If you are trying to run the tests on a machine with Python 2 and get an error along the lines of:

```
python.exe run_tests.py --remote
Fatal Python error: Py_Initialize: unable to load the file system codec
  File "c:\Instrument\Apps\EPICS\..\Python\lib\encodings\__init__.py", line 123
    raise CodecRegistryError,\
                            ^
SyntaxError: invalid syntax
```

Try unsetting the python environment variable by running `set PYTHONHOME=` and `set PYTHONPATH=`.