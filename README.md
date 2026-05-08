# brennstuhl-webline-client
Premium-Web-Line V3 python client library

## Is this possible without using HTTP web pages?

Yes. Even when the firmware does not expose a REST API, a Python module can still control the device by speaking its native control protocol directly (for example, a line-based TCP protocol on the local network).

## Implementation plan

1. Capture and document the device protocol  
   - Connect to the device web UI once in a controlled environment.
   - Capture traffic (Wireshark/tcpdump) while performing ON/OFF/status actions.
   - Extract the real command format, authentication flow, and response format.
2. Build a transport layer
   - Implement a socket transport that sends raw commands and reads responses.
   - Add timeout handling and clear transport exceptions.
3. Add a command layer
   - Store ON/OFF/STATUS commands in a command profile.
   - Validate responses and convert them into predictable return values.
4. Expose a Python client API
   - Provide simple methods like `turn_on()`, `turn_off()`, and `read_status()`.
   - Keep transport and command profile injectable for testing and future firmware variants.
5. Add focused tests
   - Unit test command dispatch and response handling with a fake transport.
   - Include failure-path tests (empty or malformed responses, transport failures).
6. Harden and release
   - Add retry/backoff strategy and optional logging.
   - Package as a reusable module once protocol mapping is complete.

## Current scaffold in this repository

This repository now includes a minimal module scaffold that already supports:
- transport abstraction (`DeviceTransport`)
- configurable command set (`CommandSet`)
- high-level client (`PremiumWebLineV3Client`)
- `psu` command-line interface

After protocol capture, you only need to plug in the real command strings and any auth handshake logic.

## CLI usage (`psu`)

Install the package and the `psu` entry point is registered automatically:

```bash
pip install .
```

```
psu <host> [--port PORT] [--timeout SECONDS] COMMAND
```

| COMMAND  | Description                          |
|----------|--------------------------------------|
| `on`     | Turn the power supply on             |
| `off`    | Turn the power supply off            |
| `status` | Read the current power supply status |

**Examples:**

```bash
# Turn on device at 192.168.1.50 (default port 23)
psu 192.168.1.50 on

# Turn off with a custom port
psu 192.168.1.50 --port 1234 off

# Read status with a 5-second timeout
psu 192.168.1.50 --timeout 5.0 status
```

Without installing, you can run the CLI directly with:

```bash
python -m brennstuhl_webline_client 192.168.1.50 on
```
