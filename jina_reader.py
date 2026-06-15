import sublime
import sublime_plugin
import urllib.request
import urllib.parse
import urllib.error
import threading
import os
import re

SETTINGS_FILE = "JinaReader.sublime-settings"
URL_REGEX = re.compile(r'https?://[^\s]+')

class JinaReaderFetchCommand(sublime_plugin.TextCommand):
    def run(self, edit, behavior=None, url=None):
        settings = sublime.load_settings(SETTINGS_FILE)
        
        if behavior is None:
            behavior = settings.get("default_behavior", "insert_below")
            
        if behavior not in ("replace", "insert_below"):
            sublime.error_message("Jina Reader: Invalid default_behavior '{}'. Must be 'replace' or 'insert_below'.".format(behavior))
            return
            
        url_region = None
        if not url:
            url, url_region = self.find_url()
        
        if not url:
            sublime.error_message("Jina Reader: No highlighted URL found. Please select a valid URL.")
            return

        api_key_env_var = settings.get("api_key_env_var", "JINA_API_KEY")
        require_api_key = settings.get("require_api_key", False)
        api_key = os.environ.get(api_key_env_var)

        if require_api_key and not api_key:
            sublime.error_message("Jina Reader: API key required but not found in environment variable '{}'.".format(api_key_env_var))
            return

        reader_base_url = settings.get("reader_base_url", "https://r.jina.ai/")
        timeout_seconds = settings.get("timeout_seconds", 60)
        accept_header = settings.get("accept", "text/plain; charset=utf-8")
        set_syntax = settings.get("set_syntax_to_markdown", True)

        change_id = self.view.change_count()
        
        thread = threading.Thread(
            target=self.fetch_markdown,
            args=(url, url_region, behavior, api_key, reader_base_url, timeout_seconds, accept_header, set_syntax, change_id)
        )
        thread.start()
        sublime.status_message("Jina Reader: fetching Markdown...")

    def find_url(self):
        # Strictly use highlighted text
        for region in self.view.sel():
            if not region.empty():
                text = self.view.substr(region)
                match = URL_REGEX.search(text)
                if match:
                    start = region.begin() + match.start()
                    end = region.begin() + match.end()
                    return match.group(0), sublime.Region(start, end)

        return None, None

    def fetch_markdown(self, url, url_region, behavior, api_key, reader_base_url, timeout_seconds, accept_header, set_syntax, change_id):
        encoded_url = urllib.parse.quote(url, safe="")
        request_url = reader_base_url + encoded_url
        
        req = urllib.request.Request(request_url)
        req.add_header("Accept", accept_header)
        # Some servers block default Python urllib User-Agents with a 403 Forbidden
        req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 JinaReader-Sublime/1.0")
        if api_key:
            req.add_header("Authorization", "Bearer {}".format(api_key))
            
        try:
            with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
                content = response.read().decode('utf-8')
                
            sublime.set_timeout(lambda: self.apply_content(content, url_region, behavior, set_syntax, change_id), 0)
        except urllib.error.HTTPError as e:
            error_msg = "HTTP Error {}: {}".format(e.code, e.reason)
            sublime.set_timeout(lambda: self.show_error(error_msg), 0)
        except urllib.error.URLError as e:
            error_msg = "Network Error: {}".format(e.reason)
            sublime.set_timeout(lambda: self.show_error(error_msg), 0)
        except Exception as e:
            error_msg = "Unexpected Error: {}".format(str(e))
            sublime.set_timeout(lambda: self.show_error(error_msg), 0)

    def show_error(self, message):
        sublime.error_message("Jina Reader: {}".format(message))
        sublime.status_message("Jina Reader: fetch failed.")

    def apply_content(self, content, url_region, behavior, set_syntax, original_change_id):
        current_change_id = self.view.change_count()
        if current_change_id != original_change_id:
            res = sublime.ok_cancel_dialog(
                "Jina Reader: The note has changed while fetching Markdown. Continue applying?",
                "Apply Markdown"
            )
            if not res:
                sublime.status_message("Jina Reader: fetch aborted by user.")
                return

        args = {
            "content": content,
            "behavior": behavior,
            "url_region_a": url_region.a if url_region else -1,
            "url_region_b": url_region.b if url_region else -1,
            "set_syntax": set_syntax
        }
        self.view.run_command("jina_reader_apply_content", args)


class JinaReaderApplyContentCommand(sublime_plugin.TextCommand):
    def run(self, edit, content, behavior, url_region_a, url_region_b, set_syntax):
        if behavior == "replace":
            entire_region = sublime.Region(0, self.view.size())
            self.view.replace(edit, entire_region, content)
            sublime.status_message("Jina Reader: note replaced with Markdown.")
        elif behavior == "insert_below":
            if url_region_a != -1 and url_region_b != -1:
                url_region = sublime.Region(url_region_a, url_region_b)
                line_region = self.view.line(url_region)
                insert_point = line_region.b
                self.view.insert(edit, insert_point, "\n\n" + content)
            else:
                # Fallback: append to end
                insert_point = self.view.size()
                self.view.insert(edit, insert_point, "\n\n" + content)
            sublime.status_message("Jina Reader: Markdown inserted.")

        if set_syntax:
            self.view.assign_syntax("Packages/Markdown/Markdown.sublime-syntax")
