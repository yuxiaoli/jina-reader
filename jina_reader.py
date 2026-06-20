import sublime
import sublime_plugin
import urllib.request
import urllib.parse
import urllib.error
import threading
import os
import re
import json

SETTINGS_FILE = "JinaReader.sublime-settings"
URL_REGEX = re.compile(r'https?://[^\s]+')
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 "
    "Safari/537.36"
)


def validate_behavior(behavior, service_name):
    if behavior in ("replace", "insert_below"):
        return True

    sublime.error_message(
        "{}: Invalid behavior '{}'. Must be 'replace' or "
        "'insert_below'.".format(service_name, behavior)
    )
    return False


def get_api_key(settings, service_name):
    api_key_env_var = settings.get("api_key_env_var", "JINA_API_KEY")
    api_key = os.environ.get(api_key_env_var)
    
    # Jina Search strictly requires an API key, so we enforce it
    is_search = service_name == "Jina Search"
    requires_key = settings.get("require_api_key", False) or is_search

    if requires_key and not api_key:
        sublime.error_message(
            "{}: API key required but not found in environment variable "
            "'{}'.".format(service_name, api_key_env_var)
        )
        return None, False

    return api_key, True


def add_common_headers(request, api_key, accept_header):
    request.add_header("Accept", accept_header)
    # Some servers block default Python urllib User-Agents with a 403.
    request.add_header("User-Agent", USER_AGENT)
    if api_key:
        request.add_header("Authorization", "Bearer {}".format(api_key))


def add_custom_headers(request, headers):
    for name, value in headers.items():
        if value is None:
            continue
        if name.lower() == "authorization":
            continue
        if isinstance(value, bool):
            value = str(value).lower()
        elif isinstance(value, (dict, list)):
            value = json.dumps(value, separators=(",", ":"))
        request.add_header(name, str(value))


def build_search_url(base_url, query, parameters):
    request_url = base_url.rstrip("/") + "/" + urllib.parse.quote(query, safe="")
    if parameters:
        normalized_parameters = []
        for key, value in parameters.items():
            values = value if isinstance(value, list) else [value]
            for item in values:
                if item is None:
                    continue
                if isinstance(item, bool):
                    item = str(item).lower()
                elif isinstance(item, (dict, list)):
                    item = json.dumps(item, separators=(",", ":"))
                normalized_parameters.append((key, item))
        if normalized_parameters:
            request_url += "?" + urllib.parse.urlencode(normalized_parameters)
    return request_url


class JinaReaderFetchCommand(sublime_plugin.TextCommand):
    def run(self, edit, behavior=None, url=None):
        settings = sublime.load_settings(SETTINGS_FILE)
        
        if behavior is None:
            behavior = settings.get("default_behavior", "insert_below")
            
        if not validate_behavior(behavior, "Jina Reader"):
            return
            
        url_region = None
        if not url:
            url, url_region = self.find_url()
        
        if not url:
            sublime.error_message("Jina Reader: No highlighted URL found. Please select a valid URL.")
            return

        api_key, key_available = get_api_key(settings, "Jina Reader")
        if not key_available:
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
        add_common_headers(req, api_key, accept_header)
            
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


class JinaReaderSearchCommand(sublime_plugin.TextCommand):
    def run(
        self,
        edit,
        query=None,
        behavior=None,
        query_region_a=-1,
        query_region_b=-1
    ):
        settings = sublime.load_settings(SETTINGS_FILE)
        if behavior is None:
            behavior = settings.get(
                "search_default_behavior",
                settings.get("default_behavior", "insert_below")
            )

        if not validate_behavior(behavior, "Jina Search"):
            return

        query_region = None
        if query is None:
            query, query_region = self.find_query()
        elif query_region_a != -1 and query_region_b != -1:
            query_region = sublime.Region(query_region_a, query_region_b)

        if not query or not query.strip():
            selections = list(self.view.sel())
            insert_point = selections[0].begin() if selections else self.view.size()
            self.view.window().show_input_panel(
                "Jina Search query:",
                "",
                lambda value: self.run_search_from_panel(
                    value, behavior, insert_point
                ),
                None,
                None
            )
            return

        query = query.strip()
        api_key, key_available = get_api_key(settings, "Jina Search")
        if not key_available:
            return

        search_base_url = settings.get("search_base_url", "https://s.jina.ai/")
        timeout_seconds = settings.get("timeout_seconds", 60)
        accept_header = settings.get("accept", "text/plain; charset=utf-8")
        set_syntax = settings.get("set_syntax_to_markdown", True)
        parameters = settings.get("search_parameters", {})
        headers = settings.get("search_headers", {})
        if not isinstance(parameters, dict):
            sublime.error_message(
                "Jina Search: 'search_parameters' must be a JSON object."
            )
            return
        if not isinstance(headers, dict):
            sublime.error_message(
                "Jina Search: 'search_headers' must be a JSON object."
            )
            return

        change_id = self.view.change_count()
        thread = threading.Thread(
            target=self.fetch_results,
            args=(
                query,
                query_region,
                behavior,
                api_key,
                search_base_url,
                parameters,
                headers,
                timeout_seconds,
                accept_header,
                set_syntax,
                change_id
            )
        )
        thread.start()
        sublime.status_message("Jina Search: searching...")

    def find_query(self):
        for region in self.view.sel():
            if not region.empty():
                query = self.view.substr(region).strip()
                if query:
                    return query, region
        return None, None

    def run_search_from_panel(self, query, behavior, insert_point):
        if not query.strip():
            return
        self.view.run_command(
            "jina_reader_search",
            {
                "query": query,
                "behavior": behavior,
                "query_region_a": insert_point,
                "query_region_b": insert_point
            }
        )

    def fetch_results(
        self,
        query,
        query_region,
        behavior,
        api_key,
        search_base_url,
        parameters,
        headers,
        timeout_seconds,
        accept_header,
        set_syntax,
        change_id
    ):
        request_url = build_search_url(search_base_url, query, parameters)
        request = urllib.request.Request(request_url)
        add_common_headers(request, api_key, accept_header)
        add_custom_headers(request, headers)

        try:
            with urllib.request.urlopen(
                request, timeout=timeout_seconds
            ) as response:
                content = response.read().decode("utf-8")

            sublime.set_timeout(
                lambda: self.apply_results(
                    content,
                    query_region,
                    behavior,
                    set_syntax,
                    change_id
                ),
                0
            )
        except urllib.error.HTTPError as error:
            error_msg = "HTTP Error {}: {}".format(error.code, error.reason)
            sublime.set_timeout(lambda: self.show_error(error_msg), 0)
        except urllib.error.URLError as error:
            error_msg = "Network Error: {}".format(error.reason)
            sublime.set_timeout(lambda: self.show_error(error_msg), 0)
        except Exception as error:
            error_msg = "Unexpected Error: {}".format(str(error))
            sublime.set_timeout(lambda: self.show_error(error_msg), 0)

    def show_error(self, message):
        sublime.error_message("Jina Search: {}".format(message))
        sublime.status_message("Jina Search: search failed.")

    def apply_results(
        self,
        content,
        query_region,
        behavior,
        set_syntax,
        original_change_id
    ):
        if self.view.change_count() != original_change_id:
            should_apply = sublime.ok_cancel_dialog(
                "Jina Search: The note has changed while searching. "
                "Continue applying?",
                "Apply Search Results"
            )
            if not should_apply:
                sublime.status_message("Jina Search: search aborted by user.")
                return

        args = {
            "content": content,
            "behavior": behavior,
            "url_region_a": query_region.a if query_region else -1,
            "url_region_b": query_region.b if query_region else -1,
            "set_syntax": set_syntax,
            "service": "search"
        }
        self.view.run_command("jina_reader_apply_content", args)


class JinaReaderApplyContentCommand(sublime_plugin.TextCommand):
    def run(
        self,
        edit,
        content,
        behavior,
        url_region_a,
        url_region_b,
        set_syntax,
        service="reader"
    ):
        service_name = "Jina Search" if service == "search" else "Jina Reader"
        if behavior == "replace":
            entire_region = sublime.Region(0, self.view.size())
            self.view.replace(edit, entire_region, content)
            sublime.status_message(
                "{}: note replaced with Markdown.".format(service_name)
            )
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
            sublime.status_message(
                "{}: Markdown inserted.".format(service_name)
            )

        if set_syntax:
            self.view.assign_syntax("Packages/Markdown/Markdown.sublime-syntax")
