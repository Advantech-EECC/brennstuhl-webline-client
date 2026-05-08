"""Low-level client scaffolding for Premium-Web-Line V3 control."""

from __future__ import annotations

from dataclasses import dataclass
import socket
from typing import Protocol


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
    """Simple line-based TCP transport."""

    host: str
    port: int
    timeout_seconds: float = 2.0
    encoding: str = "ascii"
    line_ending: str = "\r\n"
    receive_bytes: int = 4096

    def send_command(self, command: str) -> str:
        payload = f"{command}{self.line_ending}".encode(self.encoding)
        with socket.create_connection((self.host, self.port), timeout=self.timeout_seconds) as conn:
            conn.settimeout(self.timeout_seconds)
            conn.sendall(payload)
            response = conn.recv(self.receive_bytes)
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
        if not response:
            raise RuntimeError("Device returned an empty response.")
        return response
