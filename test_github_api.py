import json
import os
import unittest

import requests
from jsonschema import validate
from parameterized import parameterized

from models.issue import issue_factory


class GHTest(unittest.TestCase):
    # TODO: extract configuration; not for this demo
    max_items_per_page = 30
    default_url = "{api}/repos/{owner}/{repo}".format(api=os.getenv("GH_API_URL", "https://api.github.com"),
                                                      owner=os.getenv("GH_REPO_OWNER", "ursusrepublic"),
                                                      repo=os.getenv("GH_REPO", "django_test"))
    base_headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "Really-determined-hexabear"}
    auth_headers = {"Authorization": "token " + os.getenv("", "553c9330f36d25ca761cb2f89ab4ca624155cef1")}

    # TODO: extract to helper \ parent class; not for this demo
    @staticmethod
    def load_jsonschema(source_file):
        with open(source_file) as schema_file:
            return json.load(schema_file)

    @parameterized.expand([["/pulls", 2, "open"],
                           ["/pulls?state=open", 2, "open"],
                           ["/pulls?state=closed", 1, "closed"]])
    def test_pulls_count_per_state(self, query, expected_count, expected_state):
        r = requests.get(GHTest.default_url + query, headers=GHTest.base_headers)
        r.raise_for_status()
        pulls = r.json()

        # Pagination is not needed fot the repo in the demo.
        # Otherwise we need to check amount of pages and count of items on at first 2 pages and last one
        self.assertIsInstance(pulls, list)
        self.assertEqual(expected_count, len(pulls))

        for pull in pulls:
            with self.subTest(msg="state validation", pull=pull):
                self.assertEqual(expected_state, pull['state'])

    def test_branches(self):
        r = requests.get(GHTest.default_url + "/branches", headers=GHTest.base_headers)
        r.raise_for_status()
        branches = r.json()

        # We could make a schema check on whole response here.
        # But this will not serve demonstration purposes.

        self.assertIsInstance(branches, list)
        self.assertGreater(len(branches), 1)
        self.assertLessEqual(len(branches), GHTest.max_items_per_page)

        schema_branch = self.load_jsonschema("schema/branch.json")

        for branch in branches:
            with self.subTest(msg="schema validation", branch=branch):
                validate(branch, schema_branch)

    def test_issue_create(self):
        issue = issue_factory()
        r = requests.post(GHTest.default_url + "/issues", json=issue, headers={**GHTest.base_headers,
                                                                               **GHTest.auth_headers})
        r.raise_for_status()
        self.assertEqual(r.status_code, 201)
        self.assertIn("Location", r.headers)

        created = r.json()

        with self.subTest(msg="schema validation", issue=created):
            validate(created, self.load_jsonschema("schema/issue.json"))

        with self.subTest(msg="basic sanity checks"):
            self.assertEqual("open", created['state'])
            self.assertEqual(issue['title'], created['title'])
            self.assertEqual(issue['body'], created['body'])

        with self.subTest(msg="non-privileged user checks"):
            # As we expect the test user to have no pull rights for the repo in this demo,
            # these fields should be omitted from response or be empty
            self.assertEqual(None, created["milestone"])
            self.assertEqual([], created["labels"])
            self.assertEqual([], created["assignees"])


if __name__ == "__main__":
    unittest.main()
