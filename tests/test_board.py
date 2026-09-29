#!/usr/bin/env python3
"""Tests for the parts of board.py that decide whether a message is well-formed.

No network: everything here runs against strings. The point of these tests is the refusal —
a message with no head, a head of the wrong kind, an empty agent must not be postable.

    python3 -m unittest discover -s tests -v
"""

import json
import unittest

import board


class ReadHead(unittest.TestCase):
    def test_reads_the_first_block(self):
        body = '```json\n{"agent": "a", "kind": "question"}\n```\n\nprose'
        self.assertEqual(board.read_head(body), {"agent": "a", "kind": "question"})

    def test_only_the_first_block(self):
        body = ('```json\n{"agent": "a", "kind": "task"}\n```\n\n'
                '```json\n{"agent": "b", "kind": "report"}\n```')
        self.assertEqual(board.read_head(body)["agent"], "a")

    def test_a_later_block_is_not_a_head(self):
        body = 'prose first\n\n```json\n{"agent": "a", "kind": "task"}\n```'
        self.assertIsNone(board.read_head(body))

    def test_no_block_no_head(self):
        self.assertIsNone(board.read_head("just prose"))
        self.assertIsNone(board.read_head(""))
        self.assertIsNone(board.read_head(None))

    def test_broken_json_is_not_a_head(self):
        self.assertIsNone(board.read_head('```json\n{"agent": "a",\n```'))

    def test_a_json_list_is_not_a_head(self):
        self.assertIsNone(board.read_head('```json\n[1, 2]\n```'))

    def test_other_languages_are_not_the_head(self):
        self.assertIsNone(board.read_head('```python\nx = 1\n```'))


class CheckHead(unittest.TestCase):
    def good(self, **over):
        head = {"agent": "an-agent", "kind": "question"}
        head.update(over)
        return head

    def test_accepts_a_good_head(self):
        self.assertEqual(board.check_head(self.good()), self.good())

    def test_refuses_no_head(self):
        with self.assertRaises(board.BoardError):
            board.check_head(None)

    def test_refuses_empty_or_missing_agent(self):
        for agent in ("", "   ", None):
            with self.assertRaises(board.BoardError):
                board.check_head(self.good(agent=agent))
        with self.assertRaises(board.BoardError):
            board.check_head({"kind": "question"})

    def test_refuses_unknown_kind(self):
        with self.assertRaises(board.BoardError):
            board.check_head(self.good(kind="announcement"))
        with self.assertRaises(board.BoardError):
            board.check_head({"agent": "a"})

    def test_refuses_a_kind_that_does_not_match_the_request(self):
        with self.assertRaises(board.BoardError):
            board.check_head(self.good(kind="report"), for_kind="task")

    def test_every_declared_kind_is_postable(self):
        for kind in board.KINDS:
            self.assertEqual(board.check_head(self.good(kind=kind))["kind"], kind)


class HeadBlock(unittest.TestCase):
    def test_round_trip(self):
        head = {"agent": "a", "kind": "claim", "thread": "t", "ref": "abc123"}
        block = board.head_block(head)
        self.assertTrue(block.startswith("```json\n"))
        self.assertTrue(block.endswith("\n```"))
        self.assertEqual(json.loads(block.split("\n")[1]), head)

    def test_a_head_block_reads_back_as_a_head(self):
        head = {"agent": "a", "kind": "task"}
        self.assertEqual(board.read_head(board.head_block(head) + "\n\nprose"), head)


class KindAndWho(unittest.TestCase):
    def test_kind_from_label_when_the_body_has_no_head(self):
        self.assertEqual(board.kind_of({"body": "hi", "user": {"login": "x"}}, ["task"]), "task")

    def test_head_wins_over_the_label(self):
        body = '```json\n{"agent": "a", "kind": "report"}\n```'
        self.assertEqual(board.kind_of({"body": body, "user": {"login": "x"}}, ["task"]), "report")

    def test_who_falls_back_to_the_github_login(self):
        self.assertEqual(board.who_of({"body": "hi", "user": {"login": "octocat"}}), "octocat")


if __name__ == "__main__":
    unittest.main()
