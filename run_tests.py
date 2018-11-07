import os
import sys
import unittest
from xmlrunner import XMLTestRunner
import argparse
from wiki import Wiki, MARKDOWN, RST

from tests.page_tests import PageTests
from tests.shadow_mirroring_tests import ShadowReplicationTests


DEV_MANUAL = Wiki("ibex_developers_manual", MARKDOWN)
IBEX_MANUAL = Wiki("IBEX", MARKDOWN)
USER_MANUAL = Wiki("ibex_user_manual", RST)


def run_tests_on_pages(reports_path, pages, test_class):
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()

    # Add spelling test suite a dynamic number of times with an argument of the page name.
    # unittest's test loader is unable to take arguments to test classes by default so have
    # to use the getTestCaseNames() syntax and explicitly add the argument ourselves.
    for page in pages:
        suite.addTests([test_class(test, page) for test in loader.getTestCaseNames(test_class)])

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

    if remote:
        for wiki in [DEV_MANUAL, IBEX_MANUAL, USER_MANUAL]:
            with wiki:
                print("Running spelling tests")
                return_values.append(run_tests_on_pages(
                    os.path.join(reports_path, wiki.name), wiki.get_pages(), test_class=PageTests))

        for wiki in [DEV_MANUAL, USER_MANUAL]:
            with wiki:
                # Only do shadow replication tests in "remote" mode.
                print("Running shadow replication tests")
                return_values.append(run_tests_on_pages(
                    os.path.join(reports_path, wiki.name), wiki.get_pages(), test_class=ShadowReplicationTests))
    else:
        return_values.append(run_tests_on_pages(
                os.path.join(reports_path, os.path.basename(single_file)), [single_file], test_class=PageTests))

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
