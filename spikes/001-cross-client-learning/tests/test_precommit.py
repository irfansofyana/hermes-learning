"""Narrow precommit regressions; no servers, real tokens, or network traffic."""
import importlib.util
import io
import os
from email.message import Message
from pathlib import Path
import sys
import tempfile
import unittest
from contextlib import chdir, redirect_stderr
from unittest.mock import patch
from urllib.response import addinfourl

SPIKE = Path(__file__).resolve().parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


integration = load_module("spike_integration_check", SPIKE / "check_integration.py")
runner = load_module("spike_runner_check", SPIKE / "run.py")
api = load_module("spike_api_check", SPIKE / "plugin/dashboard/plugin_api.py")


class ProbeFinished(Exception):
    pass


class Response(addinfourl):
    msg = "Fixture response"


class LocalTransportTests(unittest.TestCase):
    def response(self, request, status, location=None):
        headers = Message()
        if location is not None:
            headers["Location"] = location
        response = Response(io.BytesIO(b"{}"), headers, request.full_url, status)
        self.addCleanup(response.close)
        return response

    def invoke(self, url, transport):
        argv = ["check_integration.py", "--url", url, "--home", "unused-fixture-home",
                "--source", "unused-fixture-source"]
        # Intercept below urllib's proxy/redirect machinery. Even a regression
        # cannot make a socket connection or read an actual session token.
        with patch.object(sys, "argv", argv), \
                patch.object(Path, "read_text", return_value="synthetic-test-token") as read, \
                patch("urllib.request._opener", None), \
                patch("urllib.request.AbstractHTTPHandler.do_open", side_effect=transport), \
                patch("socket.create_connection", side_effect=AssertionError("Network forbidden")), \
                patch.dict(os.environ, {"http_proxy": "http://proxy.invalid:9999"}, clear=True):
            try:
                integration.main()
            except (Exception, SystemExit) as error:
                return error, read.call_count
        self.fail("Probe unexpectedly completed the entire integration check")

    def test_rejects_deceptive_or_non_origin_urls_before_reading_token(self):
        for url in ["http://127.0.0.1:80@outside.invalid", "http://127.0.0.1:80/path",
                    "http://127.0.0.1:80?target=outside", "http://127.0.0.1:80#fragment",
                    "http://127.0.0.1:bad", "http://127.0.0.1:0", "https://127.0.0.1:80",
                    "http://127.0.0.1:65536", "http://127.0.0.1:80\n"]:
            with self.subTest(url=url):
                with redirect_stderr(io.StringIO()):
                    error, reads = self.invoke(url, lambda *a, **k: (_ for _ in ()).throw(ProbeFinished()))
                self.assertIsInstance(error, SystemExit)
                self.assertEqual(getattr(error, "code", None), 2)
                self.assertEqual(reads, 0)

    def test_environment_proxy_is_not_used(self):
        requests = []

        def transport(_connection, request, **kwargs):
            if not request.has_header("X-hermes-session-token"):
                return self.response(request, 401)
            requests.append(request)
            raise ProbeFinished()

        error, _ = self.invoke("http://127.0.0.1:8123/", transport)
        self.assertIsInstance(error, ProbeFinished)
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0].host, "127.0.0.1:8123")
        self.assertFalse(requests[0].has_proxy())
        self.assertEqual(requests[0].get_header("X-hermes-session-token"), "synthetic-test-token")

    def test_off_origin_redirect_is_refused_before_second_transport(self):
        for target in ["http://outside.invalid/collect", "http://127.0.0.1:8124/collect",
                       "https://127.0.0.1:8123/collect", "http://127.0.0.1:0/collect",
                       "http://fixture@127.0.0.1:8123/collect"]:
            with self.subTest(target=target):
                requests = []
                responses = []

                def transport(_connection, request, **kwargs):
                    if not request.has_header("X-hermes-session-token"):
                        return self.response(request, 401)
                    requests.append(request)
                    if len(requests) > 1:
                        raise ProbeFinished()
                    response = self.response(request, 302, target)
                    responses.append(response)
                    return response

                error, _ = self.invoke("http://127.0.0.1:8123", transport)
                self.assertIsInstance(error, ValueError)
                self.assertEqual(len(requests), 1)
                self.assertTrue(responses[0].closed)

    def test_same_origin_redirect_still_works(self):
        urls = []

        def transport(_connection, request, **kwargs):
            urls.append(request.full_url)
            if len(urls) > 1:
                raise ProbeFinished()
            return self.response(request, 302, "/same-origin")

        error, _ = self.invoke("http://127.0.0.1:8123", transport)
        self.assertIsInstance(error, ProbeFinished)
        self.assertEqual(urls, ["http://127.0.0.1:8123/api/plugins/hermes-learning-spike/state",
                               "http://127.0.0.1:8123/same-origin"])


class RunnerAndAPITests(unittest.TestCase):
    def test_explicit_relative_source_is_absolute_before_environment_construction(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "relative-source"
            dashboard = source / "hermes_cli/web_dist/index.html"
            dashboard.parent.mkdir(parents=True)
            dashboard.write_text("fixture")
            with patch.object(sys, "argv", ["run.py", "--source", "relative-source", "inspect"]), \
                    patch.object(runner, "isolated_environment", return_value={"HOME": temp}) as environment, \
                    patch.object(runner.subprocess, "run"), chdir(root):
                runner.main()
            self.assertEqual(environment.call_args.args[1], source.resolve())

    def test_start_whitespace_label_maps_learning_error_to_http_409(self):
        from fastapi import HTTPException
        with tempfile.TemporaryDirectory() as temp:
            service = api.runtime.Store(Path(temp) / "learning.db")
            with patch.object(api.runtime, "store", return_value=service):
                try:
                    api.start(api.StartBody(label="   "))
                except Exception as error:
                    self.assertIsInstance(error, HTTPException)
                    self.assertEqual(getattr(error, "status_code", None), 409)
                else:
                    self.fail("Whitespace-only label was accepted")
                self.assertEqual(service.state()["contexts"], [])
                created = api.start(api.StartBody(label=" Valid label "))
                self.assertEqual(created["label"], "Valid label")
                self.assertEqual(created["origin"], "workspace_action")


if __name__ == "__main__":
    unittest.main()
