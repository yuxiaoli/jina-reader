# Jina Reader for Sublime Text

A simple Sublime Text plugin that fetches Markdown content from a URL using [Jina Reader](https://r.jina.ai/), searches the web using [Jina Search](https://s.jina.ai/), and applies the result to the current note.

## What it does

The plugin supports two workflows:

- Highlight a URL and fetch its Markdown representation with Jina Reader.
- Highlight a search query, or enter one in an input panel, and insert Markdown search results from Jina Search.

The behavior is equivalent to this JavaScript bookmarklet:
```javascript
javascript:window.open('https://r.jina.ai/'+encodeURIComponent(location.href));
```

The plugin can either **insert** the Markdown below the line containing the URL, or **replace** the entire note with the fetched Markdown content.

## Installation

1. Open Sublime Text.
2. Go to **Preferences > Browse Packages...**.
3. Create a new directory named `JinaReader`.
4. Copy the files (`jina_reader.py`, `JinaReader.sublime-settings`, `Default.sublime-commands`, `Default.sublime-keymap`, `Main.sublime-menu`, `README.md`) into the `JinaReader` directory.
5. Restart Sublime Text if needed.

## Configuration

You can configure the plugin by creating a user settings file or modifying `JinaReader.sublime-settings`:

```json
{
  "api_key_env_var": "JINA_API_KEY",
  "require_api_key": false,
  "reader_base_url": "https://r.jina.ai/",
  "search_base_url": "https://s.jina.ai/",
  "timeout_seconds": 60,
  "accept": "text/plain; charset=utf-8",
  "search_parameters": {},
  "search_headers": {},
  "default_behavior": "insert_below",
  "search_default_behavior": "insert_below",
  "set_syntax_to_markdown": true
}
```

`search_parameters` accepts Jina Search query-string options. For example:

```json
{
  "search_parameters": {
    "type": "news",
    "num": 10,
    "site": ["example.com", "example.org"],
    "hl": "en",
    "gl": "us"
  }
}
```

Supported options include `type` (`web`, `images`, or `news`), `num`/`count` (0-20), `provider`, `page`, `location`, `hl`, `gl`, and search operators such as `site`, `ext`, `filetype`, `intitle`, and `loc`. Lists are encoded as repeated query parameters. Other documented Jina Search parameters can be added to the same object.

Header-only API options can be set with `search_headers`. Authorization is deliberately ignored here because the API key is read from the configured environment variable.

```json
{
  "search_headers": {
    "X-Preset": "research",
    "X-No-Cache": true,
    "X-Retain-Links": "all"
  }
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

### Read a URL

1. Highlight a valid `http://` or `https://` URL inside a note.
2. Run **Jina Reader: Insert Markdown Below URL** from the Command Palette, or press `Ctrl+Alt+J`.

### Search the web

1. Optionally highlight text to use as the search query.
2. Run **Jina Reader: Search and Insert Results** from the Command Palette, or press `Ctrl+Alt+Shift+J`.
3. If no text was highlighted, enter the query in the input panel.

Search results are inserted below the selected query's line. Queries entered through the input panel are inserted below the line containing the caret.

### Behaviors

- **Insert Below (Default):** Inserts Reader Markdown below the selected URL's line or Search Markdown below the selected query/caret line.
- **Replace:** Replaces the entire note. This behavior is available when invoking either command with `"behavior": "replace"` in a custom key binding or command.

## Troubleshooting

- **No highlighted URL found:** Check that you have explicitly highlighted/selected a valid `http://` or `https://` URL in the text. The plugin requires the URL to be selected.
- **Search options rejected:** Check `search_parameters` values against the Jina Search API constraints; for example, `num` and `count` must not exceed 20.
- **API Key not recognized:** Make sure you restarted Sublime Text after setting the environment variable. Also verify that the variable name matches `api_key_env_var` in your settings.
- **Timeout or Network errors:** Check your internet connection or try increasing the `timeout_seconds` in your settings.
