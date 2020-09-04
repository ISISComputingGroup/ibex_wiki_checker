import os
import sys
import unittest
from xmlrunner import XMLTestRunner
import argparse
import git

from tests.page_tests import PageTests, DEV_MANUAL, IBEX_MANUAL, USER_MANUAL, TEST_WIKI
from tests.shadow_mirroring_tests import ShadowReplicationTests
from utils.ignored_words import IGNORED_ITEMS
import utils.global_vars



def run_tests_on_pages(reports_path, pages, wiki_dir, test_class):
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()

    # Add spelling test suite a dynamic number of times with an argument of the page name.
    # unittest's test loader is unable to take arguments to test classes by default so have
    # to use the getTestCaseNames() syntax and explicitly add the argument ourselves.
    for page in pages:
        suite.addTests([test_class(test, IGNORED_ITEMS, (page, pages, wiki_dir))
                        for test in loader.getTestCaseNames(test_class)])

    runner = XMLTestRunner(output=str(reports_path), stream=sys.stdout)
    return runner.run(suite).wasSuccessful()


def run_all_tests(single_file, remote):
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

    if remote:
        for wiki in [DEV_MANUAL, IBEX_MANUAL, USER_MANUAL]:
            try:
                with wiki:
                    pages = wiki.get_pages()
                    wiki_dir = wiki.get_path()
                    print("Running spelling tests on {}".format(wiki.name))
                    return_values.append(run_tests_on_pages(
                        os.path.join(reports_path, wiki.name), pages, wiki_dir, test_class=PageTests))
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
                    return_values.append(run_tests_on_pages(
                        os.path.join(reports_path, wiki.name), pages, wiki_dir, test_class=ShadowReplicationTests))
                    print()
            except git.GitCommandError as ex:
                print("FAILED to clone {}: {}".format(wiki.name, str(ex)))
                print("Skipping tests\n")
                return_values.append(0)
                continue
    else:
        return_values.append(run_tests_on_pages(
                os.path.join(reports_path, os.path.basename(single_file)), [single_file], os.path.dirname(single_file),
                test_class=PageTests))

    return all(value for value in return_values)


def main():

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     description="""Runs tests against the IBEX wikis""")
    parser.add_argument("--file", required=False, type=str, default=None,
                        help="The file to scan")
    parser.add_argument("--remote", required=False, action='store_true', default=False,
                        help="Scan all remote wikis (dev manual, user manual, IBEX")
    args = parser.parse_args()
    if not args.file and not args.remote:
        raise(RuntimeError("No arguments specified"))
    elif args.file and args.remote:
        raise(RuntimeError("Cannot specify both a single file and remote run"))

    sys.exit(0 if run_all_tests(args.file, args.remote) else 1)


if __name__ == "__main__":
    main()
