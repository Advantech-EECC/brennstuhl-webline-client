"""Command-line interface for Premium-Web-Line V3 power supply control."""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Any

import yaml

from .client import (
    DeviceResponseError,
    DeviceTransportError,
    HttpCgiTransport,
    PremiumWebLineV3Client,
)

_DEFAULT_PORT = 80
_DEFAULT_TIMEOUT = 2.0
_DEFAULT_RELAY = 0
_VALID_COMMANDS = {"on", "off", "status"}


def _load_config(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as config_file:
        data = yaml.safe_load(config_file)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError("config must be a mapping/object at the top level")
    return data


def _coerce_int(value: Any, field_name: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid integer value for '{field_name}': {value!r}") from exc


def _coerce_float(value: Any, field_name: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid numeric value for '{field_name}': {value!r}") from exc


def _coerce_bool(value: Any, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "on", "1"}:
            return True
        if lowered in {"false", "no", "off", "0"}:
            return False
    raise ValueError(f"Invalid boolean value for '{field_name}': {value!r}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="psu",
        description="Control a Brennstuhl Premium-Web-Line V3 power supply.",
    )
    parser.add_argument("host", nargs="?", help="IP address or hostname of the device.")
    parser.add_argument(
        "command",
        nargs="?",
        choices=sorted(_VALID_COMMANDS),
        help="Device operation to execute.",
    )
    parser.add_argument(
        "--config",
        help="Path to YAML config file (e.g. /etc/psu/psu.yaml).",
        default=None,
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help=f"TCP port to connect to (default: {_DEFAULT_PORT}).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        metavar="SECONDS",
        help=f"Connection timeout in seconds (default: {_DEFAULT_TIMEOUT}).",
    )
    parser.add_argument("--username", help="Digest-auth username.", default=None)
    parser.add_argument("--password", help="Digest-auth password.", default=None)
    parser.add_argument(
        "--relay",
        type=int,
        choices=[0, 1],
        default=None,
        help=f"Relay index to control/read (default: {_DEFAULT_RELAY}).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose/debug logging.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for the ``psu`` CLI. Returns an exit code."""
    parser = _build_parser()
    if hasattr(parser, "parse_intermixed_args"):
        args = parser.parse_intermixed_args(argv)
    else:
        args = parser.parse_args(argv)
    config: dict[str, Any] = {}
    if args.config is not None:
        try:
            config = _load_config(args.config)
        except (OSError, ValueError) as exc:
            parser.error(f"failed to read config '{args.config}': {exc}")

    verbose = args.verbose
    if not verbose and "verbose" in config:
        try:
            verbose = _coerce_bool(config["verbose"], "verbose")
        except ValueError as exc:
            parser.error(str(exc))
    if verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s:%(name)s:%(message)s")

    logger = logging.getLogger(__name__)
    logger.debug("Loaded config file: %s", args.config if args.config else "<none>")

    host = args.host if args.host is not None else config.get("host")
    command = args.command if args.command is not None else config.get("command")
    if host is None:
        parser.error("host must be provided via CLI or config file.")
    if command is None:
        parser.error("command must be provided via CLI or config file.")
    if command not in _VALID_COMMANDS:
        parser.error(f"unsupported command: {command!r}; expected one of: on, off, status")

    port = args.port if args.port is not None else config.get("port", _DEFAULT_PORT)
    timeout = args.timeout if args.timeout is not None else config.get("timeout", _DEFAULT_TIMEOUT)
    relay = args.relay if args.relay is not None else config.get("relay", _DEFAULT_RELAY)
    username = args.username if args.username is not None else config.get("username")
    password = args.password if args.password is not None else config.get("password")

    try:
        port = _coerce_int(port, "port")
        timeout = _coerce_float(timeout, "timeout")
        relay = _coerce_int(relay, "relay")
    except ValueError as exc:
        parser.error(str(exc))
    if relay not in (0, 1):
        parser.error("relay must be 0 or 1")

    transport = HttpCgiTransport(
        host=str(host),
        port=port,
        timeout_seconds=timeout,
        username=None if username is None else str(username),
        password=None if password is None else str(password),
    )
    client = PremiumWebLineV3Client(transport=transport, relay=relay)
    logger.debug(
        "Executing command=%s host=%s port=%s relay=%s auth=%s",
        command,
        host,
        port,
        relay,
        "enabled" if username and password else "disabled",
    )

    try:
        if command == "on":
            response = client.turn_on()
        elif command == "off":
            response = client.turn_off()
        else:
            response = client.read_status()
    except DeviceTransportError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except DeviceResponseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(response)
    return 0


if __name__ == "__main__":
    sys.exit(main())
