import unittest
import functools
from tests import shadow_mirroring_tests
from mock import patch


class FakeResponse(object):
    """
    A fake response object with some of the same properties as the one from requests.
    """
    def __init__(self, status, content=""):
        self.status_code = status
        self.content = content


def fake_get_response_from_shadow(page, **kwargs):
    """
    Mocked out version of get_response_from_shadow
    """
    return FakeResponse(**kwargs)


class SelfTests(unittest.TestCase):
    """
    Tests that test the wiki checker tests themselves.
    """

    def test_GIVEN_dead_url_THEN_shadow_replication_test_fails(self):
        tests = shadow_mirroring_tests.ShadowReplicationTests(
            methodName="test_GIVEN_page_then_its_content_is_accessible_on_shadow",
            page="abc.md")

        with patch("tests.shadow_mirroring_tests.get_response_from_shadow",
                   side_effect=functools.partial(fake_get_response_from_shadow, status=404)):
            with self.assertRaises(AssertionError):
                tests.test_GIVEN_page_then_its_content_is_accessible_on_shadow()

    def test_GIVEN_live_url_THEN_shadow_replication_test_passes(self):
        tests = shadow_mirroring_tests.ShadowReplicationTests(
            methodName="test_GIVEN_page_then_its_content_is_accessible_on_shadow", page="abc.md")

        with patch("tests.shadow_mirroring_tests.get_response_from_shadow",
                   side_effect=functools.partial(fake_get_response_from_shadow, status=200)):
            tests.test_GIVEN_page_then_its_content_is_accessible_on_shadow()
