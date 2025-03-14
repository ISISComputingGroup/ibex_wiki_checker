import asyncio
import os
import re

import aiohttp

from ibex_wiki_checker.tests.conftest import WIKIS


IBEX_ISSUES = "IBEX/issues/"


async def test_urls(page_and_dir, ignored_urls, aiohttp_session):
    page, wiki_dir, all_pages = page_and_dir

    def get_urls_from_text(text):
        if os.path.splitext(page)[1] == ".md":
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
        elif os.path.splitext(page)[1] == ".rest":
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
            lambda url: any(allowed_url in url for allowed_url in ignored_urls),
            # Links to another page on the wiki
            lambda url: url.lower() in filenames,
        ]
        return any(condition(url) for condition in skip_conditions)

    def check_skip_conditions(url, filenames, folders):
        # Extra condition checks if it links to a file location on the wiki
        return short_check_skip_conditions(url, filenames) or url.split("/")[0] in folders

    async def try_to_connect(url):
        try:
            await aiohttp_session.head(url, timeout=5, raise_for_status=True)
        except aiohttp.ClientResponseError as e:
            return "Response HTTP {} from {}\n".format(e.status, get_url_basename(url))
        except aiohttp.InvalidURL:
            return "Invalid link: {}\n".format(get_url_basename(url))
        except aiohttp.ClientConnectionError:
            return "Client connection error for: {}\n".format(get_url_basename(url))
        except aiohttp.ClientError:
            return "General client error from {}\n".format(get_url_basename(url))

    def check_if_link_to_wiki_page(url, filenames, folders):
        # If link is to a file in the wiki and shouldn't be otherwise skipped, check that the file actually exists
        if url.split("/")[0] in folders and not short_check_skip_conditions(url, filenames):
            if not os.path.isfile(os.path.join(wiki_dir, url)):
                return True
        return False

    def fix_formatting(url):
        url = url.split("#")[0].strip()
        if url.lower().startswith("www."):
            url = "http://{}".format(url)
        return url

    def get_url_basename(url):
        if url.count("/") >= 2:
            return url.split("/")[2]
        else:
            return url

    async def check_link(link, filenames, folders):
        if not check_skip_conditions(link, filenames, folders):
            if get_url_basename(link) == "github.com":
                if IBEX_ISSUES in link:
                    return

                if any(f"{wiki}/wiki" in link for wiki in WIKIS):
                    # Get the wiki page name and append .md to it to check if the file exists in the local wiki repo
                    _page_file_name = f"{link.split('/')[-1]}.md"
                    return check_if_link_to_wiki_page(_page_file_name, filenames, folders)
            return await try_to_connect(link)
        elif check_if_link_to_wiki_page(link, filenames, folders):
            return "Could not follow page link {}".format(link)

    with open(page, encoding="utf-8") as wiki_file:
        text = wiki_file.read()

    links = get_urls_from_text(text)
    folders = os.listdir(wiki_dir) if wiki_dir else []

    filenames = [os.path.splitext(os.path.basename(f))[0].lower() for f in all_pages]

    results = await asyncio.gather(*[
        check_link(fix_formatting(link), filenames, folders) for link in links
    ])

    exception_results = [r for r in results if r]

    assert exception_results == []