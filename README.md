# Jina Reader for Sublime Text

A simple Sublime Text plugin that fetches Markdown content from a URL using [Jina Reader](https://r.jina.ai/) and applies it to the current note.

## What it does

The plugin allows you to highlight a URL inside a Sublime Text note, run a command, and fetch the Markdown version of that URL.

The behavior is equivalent to this JavaScript bookmarklet:
```javascript
javascript:window.open('https://r.jina.ai/'+encodeURIComponent(location.href));
```

The plugin can either **insert** the Markdown below the line containing the URL, or **replace** the entire note with the fetched Markdown content.

## Installation

1. Open Sublime Text.
2. Go to **Preferences > Browse Packages...**.
3. Create a new directory named `JinaReader`.
4. Copy the files (`jina_reader.py`, `JinaReader.sublime-settings`, `Default.sublime-commands`, `Default.sublime-keymap`, `README.md`) into the `JinaReader` directory.
5. Restart Sublime Text if needed.

## Configuration

You can configure the plugin by creating a user settings file or modifying `JinaReader.sublime-settings`:

```json
{
  "api_key_env_var": "JINA_API_KEY",
  "require_api_key": false,
  "reader_base_url": "https://r.jina.ai/",
  "timeout_seconds": 60,
  "accept": "text/plain; charset=utf-8",
  "default_behavior": "insert_below",
  "set_syntax_to_markdown": true
}
```

### Jina API Key

The plugin reads the API key from the environment variable specified in `api_key_env_var` (default: `JINA_API_KEY`). 

To set the API key, add it to your system environment variables. For example:
- **Windows:** `setx JINA_API_KEY "your_api_key"`
- **Linux/macOS:** `export JINA_API_KEY="your_api_key"` (in your `~/.bashrc` or `~/.zshrc`)

*(Note: You must restart Sublime Text after setting the environment variable so it can pick up the changes.)*

If `require_api_key` is set to `true`, the plugin will show an error if the environment variable is missing.

## Usage

1. Highlight a valid `http://` or `https://` URL inside a note.
2. Open the **Command Palette** (`Ctrl+Shift+P` or `Cmd+Shift+P`).
3. Search for `Jina Reader:` and select the command:
   - **Jina Reader: Insert Markdown Below URL** (Shortcut: `Ctrl+Alt+J`)

### Behaviors

- **Insert Below (Default):** Inserts the fetched Markdown below the line containing the detected URL.

## Troubleshooting

- **No highlighted URL found:** Check that you have explicitly highlighted/selected a valid `http://` or `https://` URL in the text. The plugin requires the URL to be selected.
- **API Key not recognized:** Make sure you restarted Sublime Text after setting the environment variable. Also verify that the variable name matches `api_key_env_var` in your settings.
- **Timeout or Network errors:** Check your internet connection or try increasing the `timeout_seconds` in your settings.
