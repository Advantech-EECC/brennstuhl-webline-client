"""HTTP CGI client for Brennstuhl Premium-Web-Line V3 control."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Protocol
import urllib.error
import urllib.parse
import urllib.request


class DeviceResponseError(Exception):
    """Raised when the device returns an unusable response."""


class DeviceTransportError(Exception):
    """Raised when transport-level communication with the device fails."""


class DeviceTransport(Protocol):
    """Transport contract used by the client to exchange CGI requests."""

    def get(self, path: str, params: dict[str, str] | None = None) -> str:
        """Issue a GET request and return the raw response."""

    def post(self, path: str, data: dict[str, str]) -> str:
        """Issue a POST request and return the raw response."""


@dataclass
class HttpCgiTransport:
    """HTTP transport aligned with device CGI endpoints."""

    host: str
    port: int = 80
    timeout_seconds: float = 2.0
    username: str | None = None
    password: str | None = None
    encoding: str = "utf-8"
    _opener: urllib.request.OpenerDirector | None = None

    def get(self, path: str, params: dict[str, str] | None = None) -> str:
        query = urllib.parse.urlencode(params or {})
        suffix = f"?{query}" if query else ""
        url = self._build_url(path + suffix)
        request = urllib.request.Request(url=url, method="GET")
        return self._execute(request)

    def post(self, path: str, data: dict[str, str]) -> str:
        url = self._build_url(path)
        encoded_data = urllib.parse.urlencode(data).encode(self.encoding)
        request = urllib.request.Request(url=url, data=encoded_data, method="POST")
        return self._execute(request)

    def _execute(self, request: urllib.request.Request) -> str:
        opener = self._get_opener()
        try:
            with opener.open(request, timeout=self.timeout_seconds) as response:
                body = response.read()
        except (OSError, urllib.error.HTTPError, urllib.error.URLError) as exc:
            raise DeviceTransportError(
                f"Failed request to device at {self.host}:{self.port}."
            ) from exc
        return body.decode(self.encoding, errors="replace").strip()

    def _build_url(self, path: str) -> str:
        trimmed = path.lstrip("/")
        return f"http://{self.host}:{self.port}/{trimmed}"

    def _get_opener(self) -> urllib.request.OpenerDirector:
        if self._opener is not None:
            return self._opener

        handlers: list[urllib.request.BaseHandler] = []
        if self.username and self.password:
            password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
            password_mgr.add_password(
                realm=None,
                uri=f"http://{self.host}:{self.port}/",
                user=self.username,
                passwd=self.password,
            )
            digest_handler = urllib.request.HTTPDigestAuthHandler(password_mgr)
            handlers.append(digest_handler)

        self._opener = urllib.request.build_opener(*handlers)
        return self._opener


@dataclass
class PremiumWebLineV3Client:
    """High-level client aligned with Web-Line CGI endpoints."""

    transport: DeviceTransport
    relay: int = 0

    def __post_init__(self) -> None:
        self._validate_relay(self.relay)

    def turn_on(self) -> str:
        return self.set_relay_state(self.relay, 1)

    def turn_off(self) -> str:
        return self.set_relay_state(self.relay, 0)

    def toggle(self) -> str:
        response = self.transport.get("cgi/toggleRelay", {"Rel": str(self.relay)})
        return self._ensure_non_empty(response)

    def read_status(self) -> str:
        states = self.get_relay_states()
        return "ON" if states[self.relay] == 1 else "OFF"

    def set_relay_state(self, relay: int, state: int) -> str:
        self._validate_relay(relay)
        self._validate_state(state)
        response = self.transport.get("cgi/setRelay", {"Rel": str(relay), "State": str(state)})
        return self._ensure_non_empty(response)

    def get_relay_states(self) -> tuple[int, int]:
        response = self.transport.get("cgi/getRelays")
        body = self._ensure_non_empty(response)
        states = re.findall(r"[01]", body)
        if len(states) < 2:
            raise DeviceResponseError(f"Unexpected relay state response: {body!r}")
        return int(states[0]), int(states[1])

    def get_information(self, panel: str) -> str:
        response = self.transport.post("cgi/getJsonData", {"json": "on", "panel": panel})
        return self._ensure_non_empty(response)

    def get_state_information(self) -> str:
        return self.get_information("bsState")

    def get_header_information(self) -> str:
        return self.get_information("bsHeader")

    @staticmethod
    def _ensure_non_empty(response: str) -> str:
        if response == "":
            raise DeviceResponseError("Device returned an empty response.")
        return response

    @staticmethod
    def _validate_relay(relay: int) -> None:
        if relay not in (0, 1):
            raise ValueError("relay must be 0 or 1")

    @staticmethod
    def _validate_state(state: int) -> None:
        if state not in (0, 1):
            raise ValueError("state must be 0 or 1")


# Backwards-compatible alias with previous scaffold name.
LineBasedSocketTransport = HttpCgiTransport
