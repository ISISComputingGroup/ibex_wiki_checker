import os
import git
from utils.file_system_utils import delete_dir, find_files_with_extension

RST = "RST"
MARKDOWN = "MARKDOWN"
WIKI_TYPES = [RST, MARKDOWN]


class Wiki(object):
    def __init__(self, name, doc_format):
        """
        Args:
            name: The name of the wiki
            doc_format: The format of the wiki, Markdown or RST
        """
        if doc_format not in WIKI_TYPES:
            raise(TypeError("Wiki {} initialised with invalid type {}".format(name, doc_format)))
        self.name = name
        self.format = doc_format

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
        return find_files_with_extension(self.get_path(), "md" if self.format is MARKDOWN else "rest")
