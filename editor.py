"""Core, curses-independent editing logic for Terminal Text Editor.

This module contains the `Editor` class, which implements the text buffer
and all editing operations (load, insert, delete, newline, cursor movement,
save, modified tracking) using nothing but plain Python data structures and
the filesystem. It has NO dependency on the `curses` module, which is what
makes it possible to unit test the editing logic without a real TTY.

The curses rendering/input loop lives in `editor_curses.py`.
"""

from __future__ import annotations

import os
from typing import List


class Editor:
    """Holds the text buffer and cursor state for a single open file.

    The buffer is represented as a list of strings, one per line, with no
    trailing newline characters stored in any line.
    """

    def __init__(self, filename: str | None = None) -> None:
        self.filename = filename
        self.lines: List[str] = [""]
        self.cursor_row = 0
        self.cursor_col = 0
        self.modified = False

        if filename is not None:
            self.open(filename)

    # ------------------------------------------------------------------
    # File I/O
    # ------------------------------------------------------------------
    def open(self, filename: str) -> None:
        """Load `filename` into the buffer.

        If the file does not exist, start with a single empty line (an
        empty buffer) rather than raising an error, so the editor can be
        used to create new files.
        """
        self.filename = filename
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                content = f.read()
            # Split on newlines; a trailing newline in the file should not
            # produce a bogus extra blank line beyond what splitlines gives.
            lines = content.splitlines()
            self.lines = lines if lines else [""]
        else:
            self.lines = [""]

        self.cursor_row = 0
        self.cursor_col = 0
        self.modified = False

    def save(self, filename: str | None = None) -> None:
        """Write the buffer back to disk, one line per row, newline joined."""
        target = filename or self.filename
        if target is None:
            raise ValueError("No filename set for save()")
        self.filename = target
        with open(target, "w", encoding="utf-8") as f:
            f.write("\n".join(self.lines))
            if self.lines:
                f.write("\n")
        self.modified = False

    # ------------------------------------------------------------------
    # Cursor movement (all clamp to valid bounds)
    # ------------------------------------------------------------------
    def _clamp_col(self) -> None:
        line_len = len(self.lines[self.cursor_row])
        if self.cursor_col > line_len:
            self.cursor_col = line_len
        if self.cursor_col < 0:
            self.cursor_col = 0

    def move_up(self) -> None:
        if self.cursor_row > 0:
            self.cursor_row -= 1
            self._clamp_col()

    def move_down(self) -> None:
        if self.cursor_row < len(self.lines) - 1:
            self.cursor_row += 1
            self._clamp_col()

    def move_left(self) -> None:
        if self.cursor_col > 0:
            self.cursor_col -= 1
        elif self.cursor_row > 0:
            self.cursor_row -= 1
            self.cursor_col = len(self.lines[self.cursor_row])

    def move_right(self) -> None:
        line_len = len(self.lines[self.cursor_row])
        if self.cursor_col < line_len:
            self.cursor_col += 1
        elif self.cursor_row < len(self.lines) - 1:
            self.cursor_row += 1
            self.cursor_col = 0

    # ------------------------------------------------------------------
    # Editing operations
    # ------------------------------------------------------------------
    def insert_char(self, ch: str) -> None:
        """Insert a single character at the cursor position."""
        line = self.lines[self.cursor_row]
        self.lines[self.cursor_row] = line[: self.cursor_col] + ch + line[self.cursor_col :]
        self.cursor_col += 1
        self.modified = True

    def insert_newline(self) -> None:
        """Split the current line at the cursor into two lines."""
        line = self.lines[self.cursor_row]
        before = line[: self.cursor_col]
        after = line[self.cursor_col :]
        self.lines[self.cursor_row] = before
        self.lines.insert(self.cursor_row + 1, after)
        self.cursor_row += 1
        self.cursor_col = 0
        self.modified = True

    def backspace(self) -> None:
        """Delete the character before the cursor.

        At the start of a line (col == 0), joins the current line with the
        previous line (unless already on the first line).
        """
        if self.cursor_col > 0:
            line = self.lines[self.cursor_row]
            self.lines[self.cursor_row] = line[: self.cursor_col - 1] + line[self.cursor_col :]
            self.cursor_col -= 1
            self.modified = True
        elif self.cursor_row > 0:
            prev_line = self.lines[self.cursor_row - 1]
            current_line = self.lines[self.cursor_row]
            new_col = len(prev_line)
            self.lines[self.cursor_row - 1] = prev_line + current_line
            del self.lines[self.cursor_row]
            self.cursor_row -= 1
            self.cursor_col = new_col
            self.modified = True

    def delete_char(self) -> None:
        """Delete the character under the cursor (forward delete)."""
        line = self.lines[self.cursor_row]
        if self.cursor_col < len(line):
            self.lines[self.cursor_row] = line[: self.cursor_col] + line[self.cursor_col + 1 :]
            self.modified = True
        elif self.cursor_row < len(self.lines) - 1:
            next_line = self.lines[self.cursor_row + 1]
            self.lines[self.cursor_row] = line + next_line
            del self.lines[self.cursor_row + 1]
            self.modified = True

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------
    def line_count(self) -> int:
        return len(self.lines)

    def current_line(self) -> str:
        return self.lines[self.cursor_row]


def main() -> None:
    """Entry point: `python editor.py somefile.txt` opens the curses UI."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python editor.py <filename>")
        sys.exit(1)

    # Imported lazily so that importing this module (e.g. for tests) never
    # requires curses or a real TTY.
    from editor_curses import run

    run(sys.argv[1])


if __name__ == "__main__":
    main()
