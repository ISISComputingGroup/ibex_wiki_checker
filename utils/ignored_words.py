def get_ignored_words():
    # We're finding it easier to work with ignored words ourselves rather than using Enchant's in-built
    with open("words.txt", "r", encoding="utf-8") as f:
        words = f.read().split()
    return sorted([ x.lower() for x in words ])


def get_ignored_urls():
    with open("ignored_urls.txt", "r", encoding="utf-8") as f:
        urls = f.read().split()
    return urls


IGNORED_WORDS = get_ignored_words()
IGNORED_URLS = get_ignored_urls()
IGNORED_ITEMS = {"WORDS": IGNORED_WORDS, "URLS": IGNORED_URLS}
