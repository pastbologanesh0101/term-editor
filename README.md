# Terminal Text Editor

A small, kilo-style terminal text editor written in pure-Python `curses`.

## Features

- Open and edit plain text files directly in the terminal
- Line numbers in a gutter alongside the text
- Arrow-key cursor navigation (up/down/left/right, with line wrap-around)
- Insert and delete characters at the cursor
- Enter to split a line into two (insert newline)
- Backspace that joins the current line with the previous one at column 0
- Save with `Ctrl+S`
- Quit with `Ctrl+Q`, with an unsaved-changes warning (press `Ctrl+Q` twice
  to discard changes and quit)
- Status bar showing filename, cursor line/column, and a modified flag

## Design: testable core, thin UI

The project is split into two files on purpose:

- `editor.py` — the `Editor` class: the text buffer (a list of lines) and
  every editing operation (load, insert, delete, newline, cursor movement,
  save, modified tracking). It has **no dependency on `curses`**, so it can
  be imported and unit tested in any environment, including CI, without a
  real TTY.
- `editor_curses.py` — a thin wrapper containing only the rendering and
  input loop. It imports `Editor` and translates keypresses into calls on
  it. This file is **not covered by automated tests** (curses needs a real
  terminal) and is verified manually.

## Running

```bash
python editor.py somefile.txt
```

If `somefile.txt` doesn't exist yet, the editor starts with an empty buffer
and will create the file on first save.

## Keybindings

| Key           | Action                                   |
|---------------|-------------------------------------------|
| Arrow keys    | Move cursor                              |
| Enter         | Insert newline (split line)              |
| Backspace     | Delete character before cursor / join line |
| Delete        | Delete character under cursor            |
| Ctrl+S        | Save file                                |
| Ctrl+Q        | Quit (press twice if there are unsaved changes) |

## Running the tests

```bash
python -m pytest tests/
# or
python -m unittest discover tests
```

The test suite (`tests/test_editor.py`) covers the `Editor` class only —
loading files, inserting/deleting characters, newline splitting, cursor
clamping, saving, the modified flag, and opening a nonexistent file. It
runs entirely without curses or a TTY, which is also what the CI workflow
(`.github/workflows/tests.yml`) runs on every push and pull request.

## Requirements

Pure Python standard library only (`curses`, part of the stdlib on
Unix-like systems). Tested on Python 3.11 and 3.12.

## License

MIT — see [LICENSE](LICENSE).
