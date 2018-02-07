import unittest
import os
import re
from enchant.checker import SpellChecker
from enchant.tokenize import URLFilter, EmailFilter, WikiWordFilter, MentionFilter, Filter


def get_ignored_words():
    # We're finding it easier to work with ignored words ourselves rather than using Enchant's in-built
    with open("words.txt", "r", encoding="utf-8") as f:
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

        def replace_selected_specials_with_whitespace(text):
            # This gets around certain issues recognising Github links as URLs
            altered_text = text
            for character in ["[", "]", "(", ")"]:
                altered_text = altered_text.replace(character, " ")
            return altered_text

        def strip_triple_dash_code_blocks(text):
            expression = r"```"
            triple_quote_positions = [m.start() for m in re.finditer(expression, text)]
            if len(triple_quote_positions) == 0:
                new_text = text
            elif len(triple_quote_positions) % 2 != 0:
                print("Uneven number of triple quotes detected. Doing nothing to be safe")
                new_text = text
            else:
                new_text = text[0:triple_quote_positions[0]]
                for i in range(1, len(triple_quote_positions)-1, 2):
                    new_text += text[triple_quote_positions[i] + 3: triple_quote_positions[i+1]]
                new_text += text[triple_quote_positions[-1] + 3: len(text)]
            return new_text

        def strip_inline_code_blocks(text):
            expression = r"(?:(?<!\\)((?:\\{2})+)(?=`+)|(?<!\\)(`+)(.+?)(?<!`)\2(?!`))"
            return re.sub(expression, "", text)

        def remove_bold_and_italics(text):
            return text.replace("*", "")

        with open(self.page, "r", encoding="utf-8") as wiki_file:
            text = remove_bold_and_italics(
                replace_selected_specials_with_whitespace(
                    strip_inline_code_blocks(
                        strip_triple_dash_code_blocks(
                            wiki_file.read()
                        )
                    )
                )
            )

        filters = [URLFilter, EmailFilter, MentionFilter, WikiWordFilter]
        checker = SpellChecker("en_UK", filters=filters, text=text)

        failed_words = filter_upper_case(
            {err.word for err in checker if err.word.lower() not in PageTests.IGNORED_WORDS})

        if len(failed_words) > 0:
            self.fail("The following words were spelled incorrectly in file {}: \n    {}".format(
                self.page, "\n    ".join(failed_words)
            ))
