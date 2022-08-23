# ibex_wiki_checker

The `words.txt` file is lowercased and sorted within the python check script, so a new word can be added anywhere in the file.

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

## Local Usage
For more information on usage, please see the [wiki page](https://github.com/ISISComputingGroup/ibex_developers_manual/wiki/Wiki-Checks).
