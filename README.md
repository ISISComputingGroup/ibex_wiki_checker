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

## Running the Wiki Checker locally

In order to run them locally, you need to change directory to `C:\Instrument\Dev\ibex_wiki_checker` and then execute `run_tests.bat`.

### Running the Wiki Checker locally for a single file

Executing `python -u run_tests.py --file <FILE>`, in the `ibex_wiki_checker` folder, and substituting `<FILE>` for the file name (including the path) will run the tests on a single file.

### Running the Wiki Checker locally for a folder
Executing `python -u run_tests.py --folder <FOLDER>`, in the `ibex_wiki_checker` folder, and substituting `<FOLDER>` for the folder path will run the tests on all files ending `.md` in the folder.

### Running the Wiki Checker for other wikis

In order to run the wiki check tests for another Github Wiki, you need to locally check out the `ibex_wiki_checker` repository and locally change the line https://github.com/ISISComputingGroup/ibex_wiki_checker/blob/5c4a77057d0e480373115db27f983ccb5827c3f0/wiki.py#L31 to point to the URL of the wiki you want.
