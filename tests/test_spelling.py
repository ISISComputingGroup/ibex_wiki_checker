import re
from typing import Generator

from enchant.checker import SpellChecker
from enchant.tokenize import EmailFilter, MentionFilter, URLFilter, WikiWordFilter

IBEX_ISSUES = "IBEX/issues/"


def strip_between_tags(expression, text, current_page):
    if text is None:
        return text
    matches = list(re.finditer(expression, text))
    if len(matches) == 0:
        new_text = text
    elif len(matches) % 2 != 0:
        raise ValueError(
            "Uneven number of {} detected in file {}.".format(expression, current_page)
        )
    else:
        new_text = text[0 : matches[0].start()]
        for i in range(1, len(matches) - 1, 2):
            new_text += text[matches[i].end() : matches[i + 1].start()]
        new_text += text[matches[-1].end() : len(text)]
    return new_text


def test_spelling(page_and_dir, ignored_words):
    page, wiki_dir, _ = page_and_dir

    def filter_upper_case(words: Generator[str, None, None]) -> Generator[str, None, None]:
        for w in words:
            if not w.isupper():
                yield w

    def replace_selected_specials_with_whitespace(text):
        # This gets around certain issues recognising Github links as URLs
        altered_text = text
        for character in ["[", "]", "(", ")"]:
            altered_text = altered_text.replace(character, " ")
        return altered_text

    def strip_pre_tag_blocks(text):
        return strip_between_tags(r"<pre>|</pre>", text, page)

    def strip_code_tag_blocks(text):
        return strip_between_tags(r"<code>|</code>", text, page)

    def strip_triple_dash_code_blocks(text):
        return strip_between_tags(r"```", text, page)

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

    with open(page, "r", encoding="utf-8") as wiki_file:
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

    failed_words = {x for x in filter_upper_case(
        err.word for err in checker if err.word.lower() not in ignored_words
    )}

    assert len(failed_words) == 0
