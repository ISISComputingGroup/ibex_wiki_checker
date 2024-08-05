import functools
import unittest
from unittest.mock import patch

from tests import shadow_mirroring_tests
from tests.page_tests import strip_between_tags


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
            methodName="test_GIVEN_page_then_its_content_is_accessible_on_shadow", page="abc.md"
        )

        with patch(
            "tests.shadow_mirroring_tests.get_response_from_shadow",
            side_effect=functools.partial(fake_get_response_from_shadow, status=404),
        ):
            with self.assertRaises(AssertionError):
                tests.test_GIVEN_page_then_its_content_is_accessible_on_shadow()

    def test_GIVEN_live_url_THEN_shadow_replication_test_passes(self):
        tests = shadow_mirroring_tests.ShadowReplicationTests(
            methodName="test_GIVEN_page_then_its_content_is_accessible_on_shadow", page="abc.md"
        )

        with patch(
            "tests.shadow_mirroring_tests.get_response_from_shadow",
            side_effect=functools.partial(fake_get_response_from_shadow, status=200),
        ):
            tests.test_GIVEN_page_then_its_content_is_accessible_on_shadow()

    def test_GIVEN_three_chars_repeated_expression_THEN_words_between_them_stripped(self):
        test_string = "NOT!!!STRIPPED!!!_STRIPPED"

        new_string = strip_between_tags("!!!", test_string)

        self.assertEqual(new_string, "NOT_STRIPPED")

    def test_GIVEN_one_char_repeated_expression_THEN_words_between_them_stripped(self):
        test_string = "NOT!STRIPPED!_STRIPPED"

        new_string = strip_between_tags("!", test_string)

        self.assertEqual(new_string, "NOT_STRIPPED")

    def test_GIVEN_different_token_expression_THEN_words_between_them_stripped(self):
        test_string = "NOT<code>STRIPPED</code>_STRIPPED"

        new_string = strip_between_tags("<code>|</code>", test_string)

        self.assertEqual(new_string, "NOT_STRIPPED")
