import codecs
import requests
import unittest
import os
import re

from enchant.checker import SpellChecker
from enchant.tokenize import URLFilter, EmailFilter, WikiWordFilter, MentionFilter, Filter


def get_ignored_words():
    # We're finding it easier to work with ignored words ourselves rather than using Enchant's in-built
    with open("words.txt", "r") as f:
        words = f.read().split()
    return words


class PageTests(unittest.TestCase):

    IGNORED_WORDS = get_ignored_words()

    def __init__(self, methodName, page=None, all_pages=None):
        # Boilerplate so that unittest knows how to run these tests.
        super(PageTests, self).__init__(methodName)
        self.page = page
        self.all_pages = all_pages

    def setUp(self):
        # Class has to have an __init__ that accepts one argument for unittest's test loader to work properly.
        # However it should never be the default (None) when actually running the tests.
        self.assertIsNotNone(self.page, "Cannot test if no page provided")
        self.assertTrue(os.path.exists(self.page))

    def test_GIVEN_a_page_THEN_its_spelling_conforms_to_UK_English(self):

        def filter_upper_case(words):
            return set(w for w in words if w.upper() != w)

        def replace_selected_specials_with_whitespace(text):
            # This gets around certain issues recognising Github links as URLs
            altered_text = text
            for character in ["[", "]", "(", ")"]:
                altered_text = altered_text.replace(character, " ")
            return altered_text

        def strip_code_blocks(text):
            expression = r"(?:(?<!\\)((?:\\{2})+)(?=`+)|(?<!\\)(`+)(.+?)(?<!`)\2(?!`))"
            return re.sub(expression, "", text)

        with open(self.page, "r", encoding="utf-8") as wiki_file:
            text = strip_code_blocks(replace_selected_specials_with_whitespace(wiki_file.read()))

        filters = [URLFilter, EmailFilter, MentionFilter, WikiWordFilter]
        checker = SpellChecker("en_UK", filters=filters, text=text)

        failed_words = filter_upper_case(
            {err.word for err in checker if err.word.lower() not in PageTests.IGNORED_WORDS})

        if len(failed_words) > 0:
            self.fail("The following words were spelled incorrectly in file {}: \n    {}".format(
                self.page, "\n    ".join(failed_words)
            ))

    def test_GIVEN_a_page_IF_it_contains_urls_WHEN_url_loaded_THEN_response_is_http_ok(self):
        # Have to open as UTF-8. Opening as ascii causes some encoding errors.
        try:
            with codecs.open(self.page, encoding="utf-8") as wiki_file:
                text = wiki_file.read()
        except Exception:
            self.fail("FAILED TO OPEN {}".format(self.page))

        # Find markdown URLS of the form [Link text](link location)
        urls = re.findall(r'\[.+\]\(([\S^#]+)\)', text)

        # Get first part of filename. Split off the extension (e.g. .MD)
        filenames = [os.path.basename(f).split(".")[0].lower() for f in self.all_pages]

        allowed_urls = [
            "facilities.rl.ac.uk",  # Errors if not signed in
            "control-svcs.isis.cclrc.ac.uk",  # requests module doesn't like the self-signed SSL certificate???
            "github.com/ISISComputingGroup/EPICS",  # Private repo. 404's for non-signed-in users.
        ]

        # If any of these conditions are true, don't attempt to check the URL (treat it as valid)
        skip_conditions = [
            lambda url: any(url.lower().endswith(ext) for ext in ["png", "jpeg", "jpg", "gif"]),
            lambda url: url == "",
            lambda url: url.startswith("ftp"),
            lambda url: any(allowed_url in url for allowed_url in allowed_urls),
            lambda url: url.lower() in filenames,
        ]

        for url in urls:
            # If the URL contains a #, only keep the part before the hash sign.
            url = url.split("#")[0].strip()

            if not any(condition(url) for condition in skip_conditions):
                try:
                    response = requests.get(url)
                except requests.exceptions.MissingSchema:
                    self.fail("Invalid link on page '{}': {}".format(self.page, url))

                self.assertTrue(response.ok,
                                "Could not open URL '{}' in '{}'. Response code = {}"
                                .format(url, self.page, response.status_code))
