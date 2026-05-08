import unittest
from unittest.mock import patch

from brennstuhl_webline_client import (
    DeviceResponseError,
    DeviceTransportError,
    HttpCgiTransport,
    PremiumWebLineV3Client,
)


class FakeTransport:
    def __init__(self, responses=None):
        self.responses = responses or {}
        self.get_responses = {}
        self.post_responses = {}
        for (method, path), value in self.responses.items():
            if method == "GET":
                self.get_responses[path] = value
            if method == "POST":
                self.post_responses[path] = value
        self.get_calls = []
        self.post_calls = []

    def get(self, path: str, params: dict[str, str] | None = None) -> str:
        self.get_calls.append((path, params or {}))
        return self.get_responses[path]

    def post(self, path: str, data: dict[str, str]) -> str:
        self.post_calls.append((path, data))
        return self.post_responses[path]


class PremiumWebLineV3ClientTests(unittest.TestCase):
    def test_turn_on_uses_set_relay_endpoint(self):
        transport = FakeTransport({("GET", "cgi/setRelay"): "OK"})
        client = PremiumWebLineV3Client(transport=transport, relay=0)

        response = client.turn_on()

        self.assertEqual("OK", response)
        self.assertEqual([("cgi/setRelay", {"Rel": "0", "State": "1"})], transport.get_calls)

    def test_turn_off_uses_set_relay_endpoint(self):
        transport = FakeTransport({("GET", "cgi/setRelay"): "OK"})
        client = PremiumWebLineV3Client(transport=transport, relay=1)

        response = client.turn_off()

        self.assertEqual("OK", response)
        self.assertEqual([("cgi/setRelay", {"Rel": "1", "State": "0"})], transport.get_calls)

    def test_read_status_parses_get_relays_response(self):
        transport = FakeTransport({("GET", "cgi/getRelays"): "0;1"})
        client = PremiumWebLineV3Client(transport=transport, relay=1)

        response = client.read_status()

        self.assertEqual("ON", response)
        self.assertEqual([("cgi/getRelays", {})], transport.get_calls)

    def test_get_information_posts_get_json_data(self):
        transport = FakeTransport({("POST", "cgi/getJsonData"): '{"ok":true}'})
        client = PremiumWebLineV3Client(transport=transport)

        response = client.get_state_information()

        self.assertEqual('{"ok":true}', response)
        self.assertEqual(
            [("cgi/getJsonData", {"json": "on", "panel": "bsState"})],
            transport.post_calls,
        )

    def test_empty_response_raises_device_response_error(self):
        transport = FakeTransport({("GET", "cgi/getRelays"): ""})
        client = PremiumWebLineV3Client(transport=transport)

        with self.assertRaises(DeviceResponseError):
            client.read_status()

    def test_malformed_relay_response_raises_device_response_error(self):
        transport = FakeTransport({("GET", "cgi/getRelays"): "bad"})
        client = PremiumWebLineV3Client(transport=transport)

        with self.assertRaises(DeviceResponseError):
            client.get_relay_states()


class HttpCgiTransportTests(unittest.TestCase):
    @patch("brennstuhl_webline_client.client.urllib.request.build_opener")
    def test_get_wraps_transport_errors(self, mock_build_opener):
        opener = mock_build_opener.return_value
        opener.open.side_effect = OSError("boom")
        transport = HttpCgiTransport(host="127.0.0.1", port=1234)

        with self.assertRaises(DeviceTransportError):
            transport.get("cgi/getRelays")


if __name__ == "__main__":
    unittest.main()
