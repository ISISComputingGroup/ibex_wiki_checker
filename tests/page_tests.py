import unittest
import os
from enchant.checker import SpellChecker
from enchant import DictWithPWL
from enchant.tokenize import get_tokenizer, URLFilter, EmailFilter, WikiWordFilter


class PageTests(unittest.TestCase):

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

        print("Checking the spelling in file: {}".format(self.page))
        with open(self.page, "r") as wiki_file:
            text = wiki_file.read()

        ibex_dict = DictWithPWL("en_UK")

        ibex_terminonoly = ("ioc", "opi", "css")
        github_terminology = ("wiki", "git", "github")

        for word in ibex_terminonoly + github_terminology:
            ibex_dict.add(word)

        tokenizer = get_tokenizer("en_UK", [EmailFilter, URLFilter, WikiWordFilter])
        checker = SpellChecker(ibex_dict, tokenize=tokenizer)
        checker.set_text(text)
        failed_words = {err.word for err in checker}
        if len(failed_words) > 0:
            self.fail("The following words were spelled incorrectly in file {}: \n    {}".format(
                self.page, "\n    ".join(failed_words)
            ))


