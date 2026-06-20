import json
import sys
import types
import unittest
import urllib.parse


sublime = types.ModuleType("sublime")
sublime_plugin = types.ModuleType("sublime_plugin")
sublime_plugin.TextCommand = object
sys.modules.setdefault("sublime", sublime)
sys.modules.setdefault("sublime_plugin", sublime_plugin)

import jina_reader


class BuildSearchUrlTest(unittest.TestCase):
    def test_encodes_query_as_path_segment(self):
        url = jina_reader.build_search_url(
            "https://s.jina.ai/", "Sublime Text/API", {}
        )

        self.assertEqual(
            url, "https://s.jina.ai/Sublime%20Text%2FAPI"
        )

    def test_encodes_lists_as_repeated_parameters(self):
        url = jina_reader.build_search_url(
            "https://s.jina.ai/",
            "query",
            {"site": ["example.com", "example.org"], "fallback": False}
        )
        parameters = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)

        self.assertEqual(parameters["site"], ["example.com", "example.org"])
        self.assertEqual(parameters["fallback"], ["false"])

    def test_encodes_object_values_as_json_and_omits_nulls(self):
        schema = {"type": "object", "properties": {"title": {"type": "string"}}}
        url = jina_reader.build_search_url(
            "https://s.jina.ai/",
            "query",
            {"jsonSchema": schema, "location": None}
        )
        parameters = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)

        self.assertEqual(json.loads(parameters["jsonSchema"][0]), schema)
        self.assertNotIn("location", parameters)


class AddCustomHeadersTest(unittest.TestCase):
    def test_normalizes_values_and_does_not_override_authorization(self):
        request = urllib.request.Request("https://s.jina.ai/query")
        request.add_header("Authorization", "Bearer environment-key")

        jina_reader.add_custom_headers(
            request,
            {
                "Authorization": "Bearer settings-key",
                "X-No-Cache": True,
                "X-Custom": {"mode": "strict"}
            }
        )

        self.assertEqual(
            request.get_header("Authorization"), "Bearer environment-key"
        )
        self.assertEqual(request.get_header("X-no-cache"), "true")
        self.assertEqual(request.get_header("X-custom"), '{"mode":"strict"}')


if __name__ == "__main__":
    unittest.main()
