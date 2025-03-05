import codecs
import concurrent.futures
import os
import re
import time
import unittest

import requests
from enchant.checker import SpellChecker
from enchant.tokenize import EmailFilter, MentionFilter, URLFilter, WikiWordFilter

import utils.global_vars
from wiki import Wiki

IBEX_ISSUES = "IBEX/issues/"

DEV_MANUAL = Wiki("ibex_developers_manual")
IBEX_MANUAL = Wiki("IBEX")
USER_MANUAL = Wiki("ibex_user_manual")
TEST_WIKI = Wiki("ibex_wiki_checker")
WIKI_INCLUDELIST = [USER_MANUAL, IBEX_MANUAL, DEV_MANUAL, TEST_WIKI]


def strip_between_tags(self, expression, text):
    if text is None:
        return text
    matches = list(re.finditer(expression, text))
    if len(matches) == 0:
        new_text = text
    elif len(matches) % 2 != 0:
        self.fail("Uneven number of {} detected in file {}.".format(expression, self.page))
    else:
        new_text = text[0 : matches[0].start()]
        for i in range(1, len(matches) - 1, 2):
            new_text += text[matches[i].end() : matches[i + 1].start()]
        new_text += text[matches[-1].end() : len(text)]
    return new_text


class PageTests(unittest.TestCase):
    def __init__(self, method_name, ignored_items, wiki_info: tuple[str, list[str], str, int]):
        """

        :param method_name: Name of the test you want to run
        :param ignored_items: For spellchecker, ignored words. For Link checker, ignored URLs.
        :param wiki_info: A tuple containing the page to be tested, a list of all pages on the wiki and the wiki's
        directory
        """
        # Boilerplate so that unittest knows how to run these tests.
        super(PageTests, self).__init__(method_name)
        self.page, self.all_pages, self.wiki_dir, self.top_issue_num = wiki_info
        self.ignored_words = ignored_items["WORDS"]
        self.ignored_urls = ignored_items["URLS"]
        self.isSinglePageTest = [os.path.join(self.wiki_dir, self.page)] == self.all_pages

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
            return strip_between_tags(self, r"<pre>|</pre>", text)

        def strip_code_tag_blocks(text):
            return strip_between_tags(self, r"<code>|</code>", text)

        def strip_triple_dash_code_blocks(text):
            return strip_between_tags(self, r"```", text)

        def strip_urls_from_links(text):
            # replace "[text](link)" with "text"
            expression = r"\[(.+?)\]\([\S]+\)"
            return re.sub(expression, r"\1", text)

        def strip_inline_code_blocks(text):
            expression = r"(?:(?<!\\)((?:\\{2})+)(?=`+)|(?<!\\)(`+)(.+?)(?<!`)\2(?!`))"
            return re.sub(expression, "", text)

        def strip_img_html_tags(text):
            expression = r"(<img )([a-zA-Z=\"0-9\/\-\s\.:]+)(>)"
            return re.sub(expression, "", text)

        def remove_bold_and_italics(text):
            return text.replace("*", "")

        with open(self.page, "r", encoding="utf-8") as wiki_file:
            text = strip_code_tag_blocks(wiki_file.read())
            text = strip_pre_tag_blocks(text)
            text = strip_triple_dash_code_blocks(text)
            text = strip_urls_from_links(text)
            text = strip_inline_code_blocks(text)
            text = replace_selected_specials_with_whitespace(text)
            text = remove_bold_and_italics(text)
            text = strip_img_html_tags(text)

        filters = [URLFilter, EmailFilter, MentionFilter, WikiWordFilter]
        checker = SpellChecker("en_UK", filters=filters, text=text)

        failed_words = filter_upper_case(
            {err.word for err in checker if err.word.lower() not in self.ignored_words}
        )

        if len(failed_words) > 0:
            self.fail(
                "The following words were spelled incorrectly in file {}: \n    {}".format(
                    self.page, "\n    ".join(failed_words)
                )
            )

    def test_GIVEN_a_page_IF_it_contains_urls_WHEN_url_loaded_THEN_response_is_http_ok(self):
        def get_urls_from_text(text):
            if os.path.splitext(self.page)[1] == ".md":
                # Find markdown URLS of the form [Link text](link location) with no whitespace in the curved brackets.
                # Return all characters within brackets.
                urls = re.findall(r"\[.+?\]\(([\S^#]+)\)", text)
                # As above, except this time check whether the whole block is within brackets or not. The text must
                # start with "(", not have a ")" before the link, then end with a ")" immediately after the trailing
                # ")" of the link. This stops text like "(for more detail, see [link](url))" from returning "url)"
                # while allowing "look at this link [wikipedia is full of](urls_(like_these))" to return "urls_(
                # like_these)"
                bracketed_urls = re.findall(r"\([^)]*?\[.+?\]\(([\S^#]+)\)\)", text)
                # The second set of urls takes precedence over the first, if the url appears WITHOUT a trailing ")" in
                # the bracket url list, use the entry from the bracketed list instead
                urls = [url for url in urls if url[:-1] not in bracketed_urls] + bracketed_urls
                return urls
            elif os.path.splitext(self.page)[1] == ".rest":
                # Links to pages are of the form "[[page name]]", but pages are stored as "page-name"
                # Some links are "[[text|link]]", so need to omit everything before a "|"
                page_links = re.findall(r"\[\[.*?([^]|]+)\]\]", text)
                urls = [link.strip().replace(" ", "-") for link in page_links]
                # Image links point to the file given by ":target: filename.png"
                image_links = re.findall(r":target: (\S+)", text)
                urls.extend(image_links)
                # website urls are of the form "`text text text <url>`_" with a required space before the "<"
                web_links = re.findall(r"`[^`<]+ <(\S+)>`_", text)
                urls.extend(web_links)
                return urls

        def short_check_skip_conditions(url, filenames):
            skip_conditions = [
                # Don't try to check empty strings
                lambda url: url == "",
                # Don't try to open ftp links
                lambda url: url.startswith("ftp"),
                # Some urls just won't work with this link checker, ignore them
                lambda url: any(allowed_url in url for allowed_url in self.ignored_urls),
                # Links to another page on the wiki
                lambda url: url.lower() in filenames,
            ]
            return any(condition(url) for condition in skip_conditions)

        def check_skip_conditions(url, filenames, folders):
            # Extra condition checks if it links to a file location on the wiki
            return short_check_skip_conditions(url, filenames) or url.split("/")[0] in folders

        def try_to_connect(url, session):
            nonlocal wiki_name, page_name
            try:
                response = session.head(url, timeout=5)
                if not response:
                    return "Could not open URL, got response code {} for {}\n".format(
                        response.status_code, get_url_basename(url)
                    ), url
            except (requests.exceptions.MissingSchema, requests.exceptions.InvalidURL):
                return "Invalid link: {}\n".format(get_url_basename(url)), url
            except requests.exceptions.SSLError:
                return "Invalid SSL certificate for: {}\n".format(get_url_basename(url)), url
            except requests.exceptions.ConnectionError:
                return "Disconnected without response by {}\n".format(get_url_basename(url)), url
            except requests.exceptions.Timeout:
                return "Connection Timeout by {}\n".format(get_url_basename(url)), url

        def check_if_link_to_wiki_page(url, filenames, folders):
            # If link is to a file in the wiki and shouldn't be otherwise skipped, check that the file actually exists
            if url.split("/")[0] in folders and not short_check_skip_conditions(url, filenames):
                if not os.path.isfile(os.path.join(self.wiki_dir, url)):
                    return True
            return False

        def create_failure_message(failed_urls):
            nonlocal wiki_name, page_name
            if failed_urls and not self.isSinglePageTest:
                self.fail(
                    "The page {} in the wiki {} had the following errors in its links: \n    {}".format(
                        page_name, wiki_name, "\n    ".join(failed_urls)
                    )
                )
            elif failed_urls:
                self.fail(
                    (
                        "The page {} had the following errors in its links: \n    {} \n\n    "
                        "Some of these may be due to this file being checked independent of its wiki"
                    ).format(self.page, "\n    ".join(failed_urls))
                )

        def fix_formatting(url):
            url = url.split("#")[0].strip()
            if url.lower().startswith("www."):
                url = "http://{}".format(url)
            return url

        def write_to_file(fail_text):
            """

            :param fail_text: error message received when trying to connect
            :return:
            """
            nonlocal message_lock
            error, url = fail_text
            while message_lock:
                time.sleep(1)
            message_lock = True
            message_contents = utils.global_vars.failed_url_string.splitlines(True)

            msg_index = [
                i for i in range(len(message_contents)) if message_contents[i] == error
            ]  # index of error

            if msg_index:
                # Write page location at the top of the list if error is already present in the file
                message_contents.insert(
                    msg_index[0] + 2, "  {}/{}: {}\n".format(wiki_name, page_name, url)
                )
            else:
                # Make a new entry at the end of the file if error has not been seen before
                message_contents.append(
                    "{}On the following pages:\n  {}/{}: {}\n".format(
                        error, wiki_name, page_name, url
                    )
                )

            utils.global_vars.failed_url_string = "".join(message_contents)
            message_lock = False

        def get_url_basename(url):
            """

            :param url: URL to find basename of
            :return: content between e.g. "http://" and first "/"
            """
            if url.count("/") >= 2:
                return url.split("/")[2]
            else:
                return url

        def check_link(link, session, filenames, folders):
            if not check_skip_conditions(link, filenames, folders):
                if get_url_basename(link) == "github.com":
                    if IBEX_ISSUES in link:
                        # The link is to an IBEX issue, so check if its number is less than the total number of issues
                        issue_num = int(
                            re.search(r"\d+", link)[0]
                        )  # Get the issue number in the URL
                        if not issue_num <= self.top_issue_num:
                            return "Invalid IBEX issue number: {}".format(issue_num)
                        return
                    if any([f"{wiki.name}/wiki" in link for wiki in WIKI_INCLUDELIST]):
                        # Get the wiki page name and append .md to it to check if the file exists in the local wiki repo
                        _page_file_name = f"{link.split('/')[-1]}.md"
                        return check_if_link_to_wiki_page(_page_file_name, filenames, folders)
                failure = try_to_connect(link, session)
                if failure:
                    write_to_file(failure)
            elif check_if_link_to_wiki_page(link, filenames, folders):
                return "Could not follow page link {}".format(link)

        # Have to open as UTF-8. Opening as ascii causes some encoding errors.
        try:
            with codecs.open(self.page, encoding="utf-8") as wiki_file:
                text = wiki_file.read()
        except Exception as e:
            self.fail(
                "FAILED TO OPEN {} because {} : {}".format(self.page, e.__class__.__name__, e)
            )

        message_lock = False
        wiki_name = self.wiki_dir.split("\\")[-1]
        page_name = self.page.split("\\")[-1]
        links = get_urls_from_text(text)
        folders = os.listdir(self.wiki_dir) if self.wiki_dir else []
        filenames = [os.path.splitext(os.path.basename(f))[0].lower() for f in self.all_pages]
        with requests.Session() as sess:
            # Some websites don't respond correctly with the default requests user agent, so the firefox user agent
            # is being used instead
            sess.headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:97.0) Gecko/20100101 Firefox/97.0"
            }
            failed_urls = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=None) as con_fut:
                futures = [
                    con_fut.submit(check_link, fix_formatting(link), sess, filenames, folders)
                    for link in links
                ]
                for future in concurrent.futures.as_completed(futures):
                    fail = future.result()
                    if fail:
                        failed_urls.append(fail)
            create_failure_message(failed_urls)
