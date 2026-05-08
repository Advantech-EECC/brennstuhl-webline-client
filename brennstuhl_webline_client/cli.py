"""Command-line interface for Premium-Web-Line V3 power supply control."""

from __future__ import annotations

import argparse
import sys

from .client import (
    CommandSet,
    DeviceResponseError,
    DeviceTransportError,
    LineBasedSocketTransport,
    PremiumWebLineV3Client,
)

# Default command strings — replace with real firmware commands after protocol
# capture (see README implementation plan).
_DEFAULT_COMMANDS = CommandSet(
    power_on="PWR ON",
    power_off="PWR OFF",
    status="PWR STATUS",
)

_DEFAULT_PORT = 23


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="psu",
        description="Control a Brennstuhl Premium-Web-Line V3 power supply.",
    )
    parser.add_argument("host", help="IP address or hostname of the device.")
    parser.add_argument(
        "--port",
        type=int,
        default=_DEFAULT_PORT,
        help=f"TCP port to connect to (default: {_DEFAULT_PORT}).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=2.0,
        metavar="SECONDS",
        help="Connection timeout in seconds (default: 2.0).",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    subparsers.required = True

    subparsers.add_parser("on", help="Turn the power supply on.")
    subparsers.add_parser("off", help="Turn the power supply off.")
    subparsers.add_parser("status", help="Read the current power supply status.")

    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for the ``psu`` CLI. Returns an exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    transport = LineBasedSocketTransport(
        host=args.host,
        port=args.port,
        timeout_seconds=args.timeout,
    )
    client = PremiumWebLineV3Client(transport=transport, commands=_DEFAULT_COMMANDS)

    try:
        if args.command == "on":
            response = client.turn_on()
        elif args.command == "off":
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
