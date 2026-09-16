"""Unit tests for the curses-independent Editor core logic.

These tests exercise `editor.Editor` directly and never import
`editor_curses`, so they run in any environment (including CI) without a
real TTY.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from editor import Editor


class EditorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)

    def path(self, name: str) -> str:
        return os.path.join(self.tmpdir.name, name)

    def write_file(self, name: str, content: str) -> str:
        p = self.path(name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        return p

    # ------------------------------------------------------------------
    def test_load_file_into_buffer(self) -> None:
        p = self.write_file("in.txt", "hello\nworld\n")
        editor = Editor(p)
        self.assertEqual(editor.lines, ["hello", "world"])
        self.assertEqual(editor.cursor_row, 0)
        self.assertEqual(editor.cursor_col, 0)
        self.assertFalse(editor.modified)

    def test_insert_char_at_cursor(self) -> None:
        editor = Editor()
        editor.lines = ["ac"]
        editor.cursor_row = 0
        editor.cursor_col = 1
        editor.insert_char("b")
        self.assertEqual(editor.lines, ["abc"])
        self.assertEqual(editor.cursor_col, 2)
        self.assertTrue(editor.modified)

    def test_backspace_within_line(self) -> None:
        editor = Editor()
        editor.lines = ["abc"]
        editor.cursor_row = 0
        editor.cursor_col = 2
        editor.backspace()
        self.assertEqual(editor.lines, ["ac"])
        self.assertEqual(editor.cursor_col, 1)

    def test_backspace_at_start_of_line_joins_previous(self) -> None:
        editor = Editor()
        editor.lines = ["foo", "bar"]
        editor.cursor_row = 1
        editor.cursor_col = 0
        editor.backspace()
        self.assertEqual(editor.lines, ["foobar"])
        self.assertEqual(editor.cursor_row, 0)
        self.assertEqual(editor.cursor_col, 3)

    def test_insert_newline_splits_line(self) -> None:
        editor = Editor()
        editor.lines = ["helloworld"]
        editor.cursor_row = 0
        editor.cursor_col = 5
        editor.insert_newline()
        self.assertEqual(editor.lines, ["hello", "world"])
        self.assertEqual(editor.cursor_row, 1)
        self.assertEqual(editor.cursor_col, 0)

    def test_cursor_movement_clamps_to_valid_bounds(self) -> None:
        editor = Editor()
        editor.lines = ["ab", "cde"]
        editor.cursor_row = 0
        editor.cursor_col = 0

        # Can't move up from the first line, or left from column 0.
        editor.move_up()
        self.assertEqual(editor.cursor_row, 0)
        editor.move_left()
        self.assertEqual((editor.cursor_row, editor.cursor_col), (0, 0))

        # Moving down clamps column to the new (shorter/longer) line length.
        editor.cursor_col = 2
        editor.move_down()
        self.assertEqual(editor.cursor_row, 1)
        self.assertEqual(editor.cursor_col, 2)

        # Can't move down past the last line.
        editor.move_down()
        self.assertEqual(editor.cursor_row, 1)

        # Moving right past end of last line has no further line to go to.
        editor.cursor_col = 3
        editor.move_right()
        self.assertEqual((editor.cursor_row, editor.cursor_col), (1, 3))

    def test_save_writes_buffer_to_disk(self) -> None:
        p = self.path("out.txt")
        editor = Editor()
        editor.lines = ["line one", "line two"]
        editor.save(p)
        with open(p, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, "line one\nline two\n")

    def test_modified_flag_tracks_changes_and_resets_on_save(self) -> None:
        p = self.write_file("in.txt", "abc\n")
        editor = Editor(p)
        self.assertFalse(editor.modified)
        editor.insert_char("x")
        self.assertTrue(editor.modified)
        editor.save()
        self.assertFalse(editor.modified)

    def test_open_nonexistent_file_starts_empty_buffer(self) -> None:
        p = self.path("does_not_exist.txt")
        editor = Editor(p)
        self.assertEqual(editor.lines, [""])
        self.assertEqual(editor.filename, p)
        self.assertFalse(editor.modified)

    def test_delete_char_forward(self) -> None:
        editor = Editor()
        editor.lines = ["abc"]
        editor.cursor_row = 0
        editor.cursor_col = 1
        editor.delete_char()
        self.assertEqual(editor.lines, ["ac"])
        self.assertTrue(editor.modified)


if __name__ == "__main__":
    unittest.main()
