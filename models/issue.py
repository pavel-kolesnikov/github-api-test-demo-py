import random
import unittest

import faker

faker = faker.Faker()


def issue_factory():
    return {
        "title": faker.sentence(),
        "body": faker.text(),
        "milestone": random.randint(1, 5),
        "labels": faker.words(),
        "assignees": [faker.user_name() for _ in range(3)]
    }


class IssueFactoryTest(unittest.TestCase):
    def test_generate(self):
        i = issue_factory()
        print(i)
