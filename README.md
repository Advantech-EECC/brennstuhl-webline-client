# brennstuhl-webline-client
Premium-Web-Line V3 python client library

## Implementation alignment

This module is aligned to the reference implementation in:
https://github.com/CrunkA3/BrennstuhlWebLineApi

It uses the same **HTTP CGI endpoints** and optional **digest authentication** approach:

- `GET cgi/setRelay?Rel=<0|1>&State=<0|1>`
- `GET cgi/getRelays`
- `GET cgi/toggleRelay?Rel=<0|1>`
- `POST cgi/getJsonData` with `json=on&panel=<...>`

The high-level client exposes:
- `turn_on()` / `turn_off()` for the selected relay
- `read_status()` returning `ON`/`OFF`
- `get_state_information()` / `get_header_information()`

## CLI usage (`psu`)

Install the package and the `psu` entry point is registered automatically:

```bash
pip install .
```

```
psu [--config /etc/psu/psu.yaml] [<host>] [--port PORT] [--timeout SECONDS] [--verbose] [on|off|status]
```

Optional auth/relay arguments:
- `--username USER`
- `--password PASSWORD`
- `--relay {0,1}` (default: `0`)
- `--verbose` (enable debug logging)
- `--config /etc/psu/psu.yaml` (load defaults from YAML-style key/value file)

Supported config keys: `host`, `command`, `port`, `timeout`, `username`, `password`, `relay`, `verbose`.

| COMMAND  | Description                          |
|----------|--------------------------------------|
| `on`     | Turn selected relay on               |
| `off`    | Turn selected relay off              |
| `status` | Read selected relay status (`ON/OFF`)|

**Examples:**

```bash
# Turn on relay 0 at 192.168.1.50 (default port 80)
psu 192.168.1.50 on

# Turn off relay 1 with digest auth
psu 192.168.1.50 --username admin --password secret --relay 1 off

# Read status with a 5-second timeout
psu 192.168.1.50 --timeout 5.0 status

# Use config file defaults (host/command/etc. can come from config)
psu --config /etc/psu/psu.yaml
```

Without installing, you can run the CLI directly with:

```bash
python -m brennstuhl_webline_client 192.168.1.50 on
```
