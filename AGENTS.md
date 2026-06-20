# Repository Guidelines

## Project Structure & Module Organization

The plugin is intentionally small and keeps its runtime files at the repository root. `jina_reader.py` contains the Sublime Text commands, URL detection, asynchronous HTTP request, and editor updates. `JinaReader.sublime-settings` defines user-configurable defaults. `Default.sublime-commands`, `Default.sublime-keymap`, and `Main.sublime-menu` expose the command through Sublime's UI. `scripts/install.py` copies the distributable files into the platform-specific Sublime Text `Packages/JinaReader` directory. User-facing setup and behavior belong in `README.md`.

There is currently no automated `tests/` directory or generated asset tree. If tests are added, place them under `tests/` and mirror the source feature in filenames such as `test_url_detection.py`.

## Build, Test, and Development Commands

No build step or third-party dependency installation is required; the plugin uses Python's standard library and Sublime's embedded API.

- `python -m py_compile jina_reader.py scripts/install.py` checks Python syntax without launching Sublime Text.
- `python scripts/install.py` installs the working tree into the detected Sublime Text package directory. Review the printed target before testing.
- In Sublime Text, select an HTTP(S) URL and run **Jina Reader: Insert Markdown Below URL** or press `Ctrl+Alt+J` for an end-to-end check.

Restart Sublime Text after first installation or environment-variable changes.

## Coding Style & Naming Conventions

Use four-space indentation and follow standard Python conventions: `snake_case` for functions and variables, `UPPER_SNAKE_CASE` for module constants, and `PascalCase` for command classes. Keep Sublime API mutations on the main thread via `sublime.set_timeout`; network work must remain off the UI thread. Use descriptive setting keys and preserve valid JSON in Sublime configuration files. No formatter or linter is currently configured, so keep changes focused and consistent with nearby code.

## Testing Guidelines

Run the syntax check for every Python change. Manually verify URL selection, successful insertion, missing-key behavior, network errors, and the changed-buffer confirmation when relevant. Never use a real API key in committed fixtures or settings.

## Commit & Pull Request Guidelines

History currently contains only `Initial commit`, so no detailed convention is established. Use short, imperative subjects (for example, `Handle timed-out reader requests`). Pull requests should explain the user-visible behavior, list manual test steps, link related issues, and include screenshots only when menus, commands, or editor output change.
