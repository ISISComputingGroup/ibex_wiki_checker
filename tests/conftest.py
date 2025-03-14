import asyncio
import os.path

import aiohttp

from ibex_wiki_checker.wiki import Wiki
import pytest
from contextlib import ExitStack


WIKIS = [
    "ibex_developers_manual",
    "IBEX",
    "ibex_user_manual",
    "ibex_wiki_checker",
]

@pytest.fixture(scope="session")
def ignored_words():
    with open("words.txt", "r", encoding="utf-8") as f:
        words = f.read().split()
    return sorted(set([x.lower() for x in words]))


@pytest.fixture(scope="session")
def ignored_urls():
    with open("ignored_urls.txt", "r", encoding="utf-8") as f:
        urls = f.read().split()
    return urls


@pytest.fixture(scope='session', autouse=True)
def wikis_checked_out(request):
    with ExitStack() as stack:
        for wiki in WIKIS:
            stack.enter_context(Wiki(wiki))
        yield


@pytest.fixture(scope="function")
async def aiohttp_session():
    async with aiohttp.ClientSession() as sess:
        sess.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:97.0) Gecko/20100101 Firefox/97.0"
        yield sess


def pytest_generate_tests(metafunc):
    if "page_and_dir" in metafunc.fixturenames:
        pages = []
        paths = []
        ids = []
        for wiki_name in WIKIS:
            wiki = Wiki(wiki_name)
            with wiki:
                wiki_dir = wiki.get_path()
                for page in wiki.get_pages():
                    pages.append(page)
                    paths.append(wiki_dir)
                    ids.append(f"{os.path.basename(wiki_dir)}-{os.path.basename(page)}")

        metafunc.parametrize("page_and_dir", [
            (page, path, pages) for page, path in zip(pages, paths, strict=True)
        ], ids=ids)
