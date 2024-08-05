import os
import shutil
import stat


def rmtree_error(func, path, exc_info):
    try:
        if not os.access(path, os.W_OK):
            os.chmod(path, stat.S_IWUSR)
        func(path)
    except Exception as e:
        print("Unable to delete file: {}".format(e))


def delete_dir(directory):
    if os.path.exists(directory):
        try:
            shutil.rmtree(directory, onerror=rmtree_error)
        except Exception as e:
            print("Unable to delete directory {}: {}".format(directory, e))


def find_files_with_extension(directory, extension):
    matched_files = []
    for root, dirs, files in os.walk(directory):
        for f in files:
            if f.endswith(".{}".format(extension)):
                matched_files.append(os.path.join(root, f))
    return matched_files
