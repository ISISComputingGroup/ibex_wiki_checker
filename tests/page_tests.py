import unittest
import os
import re
import codecs
import requests
import socket

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
    def __init__(self, methodName, ignored_items, wiki_info=None):
        # Boilerplate so that unittest knows how to run these tests.
        super(PageTests, self).__init__(methodName)
        self.page, self.all_pages, self.wiki_dir, self.wiki_url = wiki_info
        self.ignored_words = ignored_items["WORDS"]
        self.ignored_urls = ignored_items["URLS"]

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

    def test_GIVEN_a_page_IF_it_contains_urls_WHEN_url_loaded_THEN_response_is_http_ok(self):
        # Have to open as UTF-8. Opening as ascii causes some encoding errors.
        try:
            with codecs.open(self.page, encoding="utf-8") as wiki_file:
                text = wiki_file.read()
        except Exception:
            self.fail("FAILED TO OPEN {}".format(self.page))

        # Find markdown URLS of the form [Link text](link location)
        urls = re.findall(r'\[.+?\]\(([\S^#]+)\)', text)
        bracketed_urls = re.findall(r'\([^\)]*?\[.+?\]\(([\S^#]+)\)\)', text)
        urls = [url for url in urls if url[:-1] not in bracketed_urls] + bracketed_urls
        folders = next(os.walk(self.wiki_dir))[1]

        filenames = [os.path.basename(f)[:-3].lower() for f in self.all_pages]

        skip_conditions = [
            lambda url: url == "",
            lambda url: url.startswith("ftp"),
            lambda url: any(allowed_url in url for allowed_url in self.ignored_urls),
            lambda url: url.lower().split("/")[0] in filenames,
            lambda url: url.split("/")[0] in folders
        ]
        with requests.Session() as sess:
            for url in urls:
                # If the URL contains a #, only keep the part before the hash sign.
                url = url.split("#")[0].strip()
                if url.lower().startswith("www."):
                    url = "http://"+url
                if not any(condition(url) for condition in skip_conditions):
                    try:
                        response = sess.head(url)
                    except requests.exceptions.MissingSchema:
                        self.fail("Invalid link on page '{}': {}".format(self.page, url))
                    except requests.exceptions.SSLError:
                        self.fail("invalid SSL certificate for {} on page {}".format(url, self.page))
                    except requests.exceptions.ConnectionError:
                        self.fail("Disconnected without response by {} on page {}".format(url, self.page))
                    self.assertTrue(response,
                                    "Could not open URL '{}' in '{}'. Response code = {}"
                                    .format(url, self.page, response.status_code))
                elif skip_conditions[4](url):
                    self.assertTrue(os.path.join(self.wiki_dir, url),
                                    "Could not follow page link {} on page {}"
                                    .format(url, self.page))

