"""Low-level client scaffolding for Premium-Web-Line V3 control."""

from __future__ import annotations

from dataclasses import dataclass
import socket
from typing import Protocol


class DeviceResponseError(Exception):
    """Raised when the device returns an unusable response."""


class DeviceTransportError(Exception):
    """Raised when transport-level communication with the device fails."""


class DeviceTransport(Protocol):
    """Transport contract used by the client to exchange commands."""

    def send_command(self, command: str) -> str:
        """Send a single device command and return the raw response."""


@dataclass(frozen=True)
class CommandSet:
    """Configurable command profile for a given firmware/protocol mapping."""

    power_on: str
    power_off: str
    status: str


@dataclass
class LineBasedSocketTransport:
    """Simple line-based TCP transport.

    The default line ending is CRLF because many embedded line-based protocols
    expect it. It can be overridden per device firmware if needed.
    """

    host: str
    port: int
    timeout_seconds: float = 2.0
    encoding: str = "ascii"
    line_ending: str = "\r\n"
    receive_bytes: int = 4096

    def send_command(self, command: str) -> str:
        payload = f"{command}{self.line_ending}".encode(self.encoding)
        try:
            # Opens one connection per command for simplicity and reliability.
            with socket.create_connection((self.host, self.port), timeout=self.timeout_seconds) as conn:
                conn.sendall(payload)
                with conn.makefile("rb") as reader:
                    response = reader.readline(self.receive_bytes)
        except OSError as exc:
            raise DeviceTransportError(
                f"Failed to send command to device at {self.host}:{self.port}."
            ) from exc
        return response.decode(self.encoding, errors="replace").strip()


@dataclass
class PremiumWebLineV3Client:
    """High-level control client that does not depend on web pages."""

    transport: DeviceTransport
    commands: CommandSet

    def turn_on(self) -> str:
        return self._send(self.commands.power_on)

    def turn_off(self) -> str:
        return self._send(self.commands.power_off)

    def read_status(self) -> str:
        return self._send(self.commands.status)

    def _send(self, command: str) -> str:
        response = self.transport.send_command(command)
        if response == "":
            raise DeviceResponseError("Device returned an empty response.")
        return response
