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


def strip_between_tags(expression, text):
    if text is None:
        return text
    matches = list(re.finditer(expression, text))
    if len(matches) == 0:
        new_text = text
    elif len(matches) % 2 != 0:
        print("Uneven number of {} detected. Doing nothing to be safe".format(expression))
        new_text = text
    else:
        new_text = text[0:matches[0].start()]
        for i in range(1, len(matches) - 1, 2):
            new_text += text[matches[i].end(): matches[i + 1].start()]
        new_text += text[matches[-1].end(): len(text)]
    return new_text


class PageTests(unittest.TestCase):
    def __init__(self, methodName, ignored_words, page=None):
        # Boilerplate so that unittest knows how to run these tests.
        super(PageTests, self).__init__(methodName)
        self.page = page
        self.ignored_words = ignored_words

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

        def strip_pre_tag_blocks(text):
            return strip_between_tags(r"<pre>|</pre>", text)

        def strip_code_tag_blocks(text):
            return strip_between_tags(r"<code>|</code>", text)

        def strip_triple_dash_code_blocks(text):
            return strip_between_tags(r"```", text)

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
                            strip_pre_tag_blocks(
                                strip_code_tag_blocks(
                                    wiki_file.read()
                                )
                            )
                        )
                    )
                )
            )

        filters = [URLFilter, EmailFilter, MentionFilter, WikiWordFilter]
        checker = SpellChecker("en_UK", filters=filters, text=text)

        failed_words = filter_upper_case(
            {err.word for err in checker if err.word.lower() not in self.ignored_words})

        if len(failed_words) > 0:
            self.fail("The following words were spelled incorrectly in file {}: \n    {}".format(
                self.page, "\n    ".join(failed_words)
            ))
