"""Command-line interface for Premium-Web-Line V3 power supply control."""

from __future__ import annotations

import argparse
import sys

from .client import (
    DeviceResponseError,
    DeviceTransportError,
    HttpCgiTransport,
    PremiumWebLineV3Client,
)

_DEFAULT_PORT = 80


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
    parser.add_argument("--username", help="Digest-auth username.", default=None)
    parser.add_argument("--password", help="Digest-auth password.", default=None)
    parser.add_argument(
        "--relay",
        type=int,
        choices=[0, 1],
        default=0,
        help="Relay index to control/read (default: 0).",
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

    transport = HttpCgiTransport(
        host=args.host,
        port=args.port,
        timeout_seconds=args.timeout,
        username=args.username,
        password=args.password,
    )
    client = PremiumWebLineV3Client(transport=transport, relay=args.relay)

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
