import string
import unittest
import os
from enchant.checker import SpellChecker
from enchant.tokenize import URLFilter, EmailFilter, WikiWordFilter, MentionFilter


def get_ignored_words():
    # We're finding it easier to work with ignored words ourselves rather than using Enchant's in-built
    with open("words.txt", "r") as f:
        words = f.read().split()
    return words


class PageTests(unittest.TestCase):

    IGNORED_WORDS = get_ignored_words()

    def __init__(self, methodName, page=None):
        # Boilerplate so that unittest knows how to run these tests.
        super(PageTests, self).__init__(methodName)
        self.page = page

    def setUp(self):
        # Class has to have an __init__ that accepts one argument for unittest's test loader to work properly.
        # However it should never be the default (None) when actually running the tests.
        self.assertIsNotNone(self.page, "Cannot test if no page provided")
        self.assertTrue(os.path.exists(self.page))

    def test_GIVEN_a_page_THEN_its_spelling_conforms_to_UK_English(self):

        def filter_upper_case(words):
            return set(w for w in words if w.upper() != w)

        with open(self.page, "r", encoding="utf-8") as wiki_file:
            text = wiki_file.read()
            
        checker = SpellChecker("en_UK", filters=[URLFilter, EmailFilter, MentionFilter, WikiWordFilter], text=text)

        failed_words = filter_upper_case(
            {err.word for err in checker if err.word.lower() not in PageTests.IGNORED_WORDS})

        if len(failed_words) > 0:
            self.fail("The following words were spelled incorrectly in file {}: \n    {}".format(
                self.page, "\n    ".join(failed_words)
            ))
