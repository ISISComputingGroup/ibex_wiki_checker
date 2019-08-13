import os
import git
from utils.file_system_utils import delete_dir, find_files_with_extension


class Wiki(object):
    def __init__(self, name):
        """
        Args:
            name: The name of the wiki
        """
        self.name = name

    def __enter__(self):
        self.clean_source()
        self.clone_wiki_from_web()

    def __exit__(self, *args):
        self.clean_source()

    def get_path(self):
        return os.path.join(os.getcwd(), "source", self.name)

    def clean_source(self):
        delete_dir(self.get_path())

    def clone_wiki_from_web(self):
        repo_path = self.get_path()
        if not os.path.exists(repo_path):
            os.makedirs(repo_path)
        git.Git(repo_path).clone("https://github.com/ISISComputingGroup/{}.wiki.git".format(self.name), repo_path)

    def get_pages(self):
        files = find_files_with_extension(self.get_path(), "md")
        files.extend(find_files_with_extension(self.get_path(), "rest"))
        return files
