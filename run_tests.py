import os
import sys
import unittest
from xmlrunner import XMLTestRunner
import argparse
from wiki import Wiki, MARKDOWN, RST

from tests.page_tests import PageTests


def run_spell_checker(reports_path, pages):
    """
    Check the spelling in a given wiki

    Args
        wiki: The wiki to check
        reports_path: The path to put the test report

    Returns
        True if spelling ok, else False
    """
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()

    # Add spelling test suite a dynamic number of times with an argument of the page name.
    # unittest's test loader is unable to take arguments to test classes by default so have
    # to use the getTestCaseNames() syntax and explicitly add the argument ourselves.
    for page in pages:
        suite.addTests([PageTests(test, page) for test in loader.getTestCaseNames(PageTests)])

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
        wikis = [
            Wiki("ibex_wiki_checker", MARKDOWN),
            Wiki("ibex_developers_manual", MARKDOWN),
            Wiki("IBEX", MARKDOWN),
            Wiki("ibex_user_manual", RST),
        ]

        for wiki in wikis:
            with wiki:
                return_values.append(run_spell_checker(os.path.join(reports_path, wiki.name), wiki.get_pages()))
    else:
        return_values.append(
            run_spell_checker(os.path.join(reports_path, os.path.basename(single_file)), [single_file]))

    with open("new_words.txt", "w") as f:
        f.writelines(sorted(PageTests.FAILED_WORDS))
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
