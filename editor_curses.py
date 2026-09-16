"""Thin curses UI layer for Terminal Text Editor.

This module contains ONLY rendering and input-loop code. All actual editing
logic lives in `editor.py`'s `Editor` class, which has no curses dependency.
This file is intentionally not covered by the unit tests (it needs a real
TTY to run) and should be verified manually.
"""

from __future__ import annotations

import curses

from editor import Editor

CTRL_S = 19  # Ctrl+S
CTRL_Q = 17  # Ctrl+Q

GUTTER_WIDTH = 5  # width reserved for line numbers, e.g. "  12 "


def run(filename: str) -> None:
    curses.wrapper(lambda stdscr: _main(stdscr, filename))


def _main(stdscr, filename: str) -> None:
    curses.curs_set(1)
    stdscr.keypad(True)

    editor = Editor(filename)
    scroll_top = 0
    quit_confirm_pending = False
    status_message = ""

    while True:
        height, width = stdscr.getmaxyx()
        text_height = max(height - 1, 1)  # last row reserved for status bar

        # Keep cursor within the visible scroll window.
        if editor.cursor_row < scroll_top:
            scroll_top = editor.cursor_row
        elif editor.cursor_row >= scroll_top + text_height:
            scroll_top = editor.cursor_row - text_height + 1

        stdscr.erase()

        # Draw visible lines with line numbers.
        for screen_row in range(text_height):
            file_row = scroll_top + screen_row
            if file_row >= editor.line_count():
                break
            line_num_str = str(file_row + 1).rjust(GUTTER_WIDTH - 1) + " "
            line_text = editor.lines[file_row]
            available = max(width - len(line_num_str), 0)
            try:
                stdscr.addstr(screen_row, 0, line_num_str, curses.A_DIM)
                stdscr.addstr(screen_row, len(line_num_str), line_text[:available])
            except curses.error:
                pass  # writing to bottom-right corner can raise; ignore

        # Status bar.
        mod_flag = "[modified]" if editor.modified else "[saved]"
        status = (
            f"{editor.filename or '[No Name]'} - "
            f"Ln {editor.cursor_row + 1}, Col {editor.cursor_col + 1} {mod_flag}"
        )
        if status_message:
            status = f"{status} | {status_message}"
        try:
            stdscr.addstr(height - 1, 0, status[: max(width - 1, 0)], curses.A_REVERSE)
        except curses.error:
            pass

        cursor_screen_row = editor.cursor_row - scroll_top
        cursor_screen_col = min(editor.cursor_col + GUTTER_WIDTH, max(width - 1, 0))
        try:
            stdscr.move(cursor_screen_row, cursor_screen_col)
        except curses.error:
            pass

        stdscr.refresh()

        ch = stdscr.getch()
        status_message = ""

        if ch == CTRL_Q:
            if editor.modified and not quit_confirm_pending:
                status_message = "Unsaved changes! Press Ctrl+Q again to quit without saving."
                quit_confirm_pending = True
                continue
            break
        quit_confirm_pending = False

        if ch == CTRL_S:
            try:
                editor.save()
                status_message = "Saved."
            except OSError as exc:
                status_message = f"Save failed: {exc}"
        elif ch in (curses.KEY_UP,):
            editor.move_up()
        elif ch in (curses.KEY_DOWN,):
            editor.move_down()
        elif ch in (curses.KEY_LEFT,):
            editor.move_left()
        elif ch in (curses.KEY_RIGHT,):
            editor.move_right()
        elif ch in (curses.KEY_BACKSPACE, 127, 8):
            editor.backspace()
        elif ch in (curses.KEY_DC,):
            editor.delete_char()
        elif ch in (curses.KEY_ENTER, 10, 13):
            editor.insert_newline()
        elif 0 <= ch < 256 and chr(ch).isprintable():
            editor.insert_char(chr(ch))
        # Other keys (function keys, resize, etc.) are ignored.
