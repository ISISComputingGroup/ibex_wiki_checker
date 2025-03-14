import argparse
import json
import os
import sys
import unittest
import locale

import git
import requests
from xmlrunner import XMLTestRunner

import utils.global_vars
from tests.page_tests import DEV_MANUAL, IBEX_MANUAL, USER_MANUAL, PageTests
from tests.shadow_mirroring_tests import ShadowReplicationTests
from utils.ignored_words import IGNORED_ITEMS

GITHUB_API_ISSUE_CALL = "https://api.github.com/repos/ISISComputingGroup/IBEX/issues?per_page=1"


def run_tests_on_pages(reports_path, pages, wiki_dir, highest_issue_num, test_class):
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()

    # Add spelling test suite a dynamic number of times with an argument of the page name.
    # unittest's test loader is unable to take arguments to test classes by default so have
    # to use the getTestCaseNames() syntax and explicitly add the argument ourselves.
    for page in pages:
        suite.addTests(
            [
                test_class(test, IGNORED_ITEMS, (page, pages, wiki_dir, highest_issue_num))
                for test in loader.getTestCaseNames(test_class)
            ]
        )

    runner = XMLTestRunner(output=str(reports_path), stream=sys.stdout)
    return runner.run(suite).wasSuccessful()


def run_all_tests(single_file, remote, folder):
    """
    Runs all of the tests

    Returns
        True if all tests pass, else False
    """
    reports_path = os.path.join(os.getcwd(), "test-reports")
    if not os.path.exists(reports_path):
        try:
            os.mkdir(reports_path)
        except OSError as e:
            print("Unable to create test report folder: {}".format(e))
            return [False]

    return_values = []

    #  initialise globals, currently just string of warnings
    utils.global_vars.init()

    top_issue_num = int(json.loads(requests.get(GITHUB_API_ISSUE_CALL).content)[0]["number"])
    if remote:
        for wiki in [DEV_MANUAL, IBEX_MANUAL, USER_MANUAL]:
            try:
                with wiki:
                    pages = wiki.get_pages()
                    wiki_dir = wiki.get_path()
                    print("Running spelling tests on {}".format(wiki.name))
                    return_values.append(
                        run_tests_on_pages(
                            os.path.join(reports_path, wiki.name),
                            pages,
                            wiki_dir,
                            top_issue_num,
                            test_class=PageTests,
                        )
                    )
                    print()
            except git.GitCommandError as ex:
                print("FAILED to clone {}: {}".format(wiki.name, str(ex)))
                print("Skipping tests\n")
                return_values.append(0)
                continue
        print(utils.global_vars.failed_url_string)
        for wiki in [DEV_MANUAL, USER_MANUAL]:
            try:
                with wiki:
                    pages = wiki.get_pages()
                    wiki_dir = wiki.get_path()
                    # Only do shadow replication tests in "remote" mode.
                    print("Running shadow replication tests on {}".format(wiki.name))
                    return_values.append(
                        run_tests_on_pages(
                            os.path.join(reports_path, wiki.name),
                            pages,
                            wiki_dir,
                            top_issue_num,
                            test_class=ShadowReplicationTests,
                        )
                    )
                    print()
            except git.GitCommandError as ex:
                print("FAILED to clone {}: {}".format(wiki.name, str(ex)))
                print("Skipping tests\n")
                return_values.append(0)
                continue
    elif single_file:
        return_values.append(
            run_tests_on_pages(
                os.path.join(reports_path, os.path.basename(single_file)),
                [single_file],
                os.path.dirname(single_file),
                top_issue_num,
                test_class=PageTests,
            )
        )
    elif folder:
        print("Running spelling tests on folder {}".format(folder))
        files = os.listdir(folder)
        files_to_test = []
        for f in files:
            if f.endswith(".md"):
                files_to_test.append(os.path.join(folder, f))
        # The path is listed as an empty string as this hybrid set up ignores it
        return_values.append(
            run_tests_on_pages(
                os.path.join(reports_path, os.path.basename(folder)),
                files_to_test,
                "",
                top_issue_num,
                test_class=PageTests,
            )
        )
        print(utils.global_vars.failed_url_string)

    return all(value for value in return_values)


def main():

    import enchant
    print("TESTTTTTTTT")
    broker = enchant.Broker()
    broker.describe()
    print(broker.list_languages())
    return 0


    locale.setlocale(locale.LC_ALL, 'en_GB.UTF-8')
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="""Runs tests against the IBEX wikis""",
    )
    parser.add_argument("--file", required=False, type=str, default=None, help="The file to scan")
    parser.add_argument(
        "--remote",
        required=False,
        action="store_true",
        default=False,
        help="Scan all remote wikis (dev manual, user manual, IBEX)",
    )
    parser.add_argument(
        "--folder", required=False, type=str, default=None, help="Scan just a local folder"
    )
    args = parser.parse_args()
    if not args.file and not args.remote and not args.folder:
        raise (RuntimeError("No arguments specified"))
    elif (
        (args.file and args.remote) or (args.file and args.folder) or (args.remote and args.folder)
    ):
        raise (RuntimeError("Cannot specify more than one target for the tests"))

    sys.exit(0 if run_all_tests(args.file, args.remote, args.folder) else 1)


if __name__ == "__main__":
    main()
