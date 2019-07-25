import unittest
import os
import requests


HTTP_OK = 200

SHADOW_URL = "http://shadow.nd.rl.ac.uk"

ERROR_TEXT = "Failed to render page: Traceback"


def url_from_file_location(file_location):
    relative_path = os.path.relpath(file_location, os.path.join(os.getcwd(), "source"))
    relative_path_without_extension, _ = os.path.splitext(relative_path)
    return "{}/{}".format(SHADOW_URL, relative_path_without_extension.replace("\\", "/"))


def get_response_from_shadow(url):
    return requests.get(url, timeout=20)  # 20s timeout as shadow can be quite slow to respond, 10s is not enough.


class ShadowReplicationTests(unittest.TestCase):

    def __init__(self, methodName, ignored_words=None, wiki_info=None):
        # Boilerplate so that unittest knows how to run these tests.
        super(ShadowReplicationTests, self).__init__(methodName)
        self.page = wiki_info[0]

    def setUp(self):
        # Class has to have an __init__ that accepts one argument for unittest's test loader to work properly.
        # However it should never be the default (None) when actually running the tests.
        self.assertIsNotNone(self.page, "Cannot test if no page provided")

    def test_GIVEN_page_then_its_content_is_accessible_on_shadow(self):
        url = url_from_file_location(self.page)
        response = get_response_from_shadow(url)

        self.assertEqual(response.status_code, HTTP_OK,
                         "Page {} returned status code {}".format(url, response.status_code))
        self.assertNotIn(ERROR_TEXT, str(response.content),
                         "Page {} appears to be failing to render.".format(url))
